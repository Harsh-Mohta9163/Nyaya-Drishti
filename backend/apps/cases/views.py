from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.action_plans.models import ActionPlan
from apps.action_plans.serializers import ActionPlanSerializer
from apps.action_plans.services.plan_generator import generate_or_refresh_action_plan
from apps.reviews.models import ReviewLog
from apps.reviews.serializers import ReviewLogSerializer

from .models import Case, ExtractedData
from .serializers import CaseSerializer, CaseStatusSerializer, ExtractedDataSerializer


class CaseListCreateView(ListCreateAPIView):
	queryset = Case.objects.select_related("uploaded_by").all().order_by("-created_at")
	serializer_class = CaseSerializer
	parser_classes = [MultiPartParser, FormParser]

	def get_queryset(self):
		qs = super().get_queryset()
		# Support filtering by status, case_type, search
		s = self.request.query_params.get("status")
		if s:
			qs = qs.filter(status=s)
		ct = self.request.query_params.get("case_type")
		if ct:
			qs = qs.filter(case_type=ct)
		search = self.request.query_params.get("search")
		if search:
			from django.db.models import Q
			qs = qs.filter(
				Q(case_number__icontains=search) |
				Q(petitioner__icontains=search) |
				Q(respondent__icontains=search)
			)
		ordering = self.request.query_params.get("ordering")
		if ordering:
			qs = qs.order_by(ordering)
		return qs

	def perform_create(self, serializer):
		serializer.save(uploaded_by=self.request.user)


class CaseDetailView(RetrieveAPIView):
	queryset = Case.objects.select_related("uploaded_by").all()
	serializer_class = CaseSerializer


class CaseStatusUpdateView(APIView):
	def patch(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		serializer = CaseStatusSerializer(case, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(CaseSerializer(case).data)


class CaseExtractionView(APIView):
	"""GET extracted data for a case."""
	def get(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		try:
			extracted = case.extracted_data
		except ExtractedData.DoesNotExist:
			return Response({"detail": "No extraction data yet."}, status=status.HTTP_404_NOT_FOUND)
		return Response(ExtractedDataSerializer(extracted).data)


class CaseExtractView(APIView):
	"""POST to trigger extraction pipeline."""
	def post(self, request, pk):
		case = get_object_or_404(Case, pk=pk)

		from .services.extractor import extract_structured_data
		from .services.pdf_processor import extract_text_from_pdf
		from .services.section_segmenter import segment_judgment

		pdf_text = extract_text_from_pdf(case.pdf_file.path)
		sections = segment_judgment(pdf_text)
		extracted_payload = extract_structured_data(case=case, sections=sections)

		# Find page numbers for court directions
		directions = extracted_payload.get("court_directions", [])
		for dir in directions:
			text_to_find = dir.get("text", "")
			if text_to_find and len(text_to_find) > 10:
				# Find the index of the text in the full pdf
				# (simplistic search, handles exact matches)
				idx = pdf_text.find(text_to_find[:50])
				if idx != -1:
					# Find the last "--- Page X ---" before this index
					page_marker_idx = pdf_text.rfind("--- Page ", 0, idx)
					if page_marker_idx != -1:
						end_marker = pdf_text.find(" ---", page_marker_idx)
						if end_marker != -1:
							try:
								page_num = int(pdf_text[page_marker_idx + 9 : end_marker])
								dir["source_reference"] = {"page": page_num, "text_snippet": text_to_find}
							except ValueError:
								pass

		ExtractedData.objects.update_or_create(
			case=case,
			defaults={
				"header_data": extracted_payload.get("header_data", {}),
				"operative_order": extracted_payload.get("operative_order", ""),
				"court_directions": directions,
				"order_type": extracted_payload.get("order_type", "unknown"),
				"entities": extracted_payload.get("entities", []),
				"extraction_confidence": extracted_payload.get("extraction_confidence", 0.0),
				"source_references": extracted_payload.get("source_references", []),
			},
		)

		case.status = Case.Status.EXTRACTED
		case.ocr_confidence = extracted_payload.get("ocr_confidence", 0.0)

		# Map entities back to the case header if possible
		entities = extracted_payload.get("entities", [])
		for e in entities:
			role = e.get("role", "").lower()
			name = e.get("name", "")
			if "petitioner" in role or "appellant" in role:
				case.petitioner = name
			elif "respondent" in role:
				case.respondent = name

		# Map case number and court
		header = extracted_payload.get("header_data", {})
		if header.get("case_number"):
			case.case_number = header["case_number"]
		if header.get("court"):
			case.court = header["court"]

		case.save(update_fields=["status", "ocr_confidence", "updated_at", "petitioner", "respondent", "case_number", "court"])

		return Response(CaseSerializer(case).data, status=status.HTTP_200_OK)


class CaseActionPlanView(APIView):
	"""GET action plan for a case, or POST to generate/refresh it."""
	def get(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		try:
			plan = case.action_plan
		except ActionPlan.DoesNotExist:
			return Response({"detail": "No action plan yet."}, status=status.HTTP_404_NOT_FOUND)
		return Response(ActionPlanSerializer(plan).data)

	def post(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		action_plan = generate_or_refresh_action_plan(case)
		return Response(ActionPlanSerializer(action_plan).data, status=status.HTTP_200_OK)


class CasePDFView(APIView):
	"""Serve the PDF file for a case."""
	def get(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		if not case.pdf_file:
			return Response({"detail": "No PDF file."}, status=status.HTTP_404_NOT_FOUND)
		return FileResponse(case.pdf_file.open("rb"), content_type="application/pdf")


class CaseReviewSubmitView(APIView):
	"""Submit a review for a case (finds the action plan automatically)."""
	def post(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		try:
			action_plan = case.action_plan
		except ActionPlan.DoesNotExist:
			return Response({"detail": "No action plan to review."}, status=status.HTTP_404_NOT_FOUND)

		review_level = request.data.get("review_level", "field")
		action = request.data.get("action", "approve")
		changes = request.data.get("changes")
		reason = request.data.get("reason", "")

		log = ReviewLog.objects.create(
			action_plan=action_plan,
			reviewer=request.user,
			review_level=review_level,
			action=action,
			changes=changes,
			notes=reason,
		)

		# Update verification status based on review level and action
		if action == "approve":
			level_map = {
				"field": "field_approved",
				"directive": "directive_approved",
				"case": "case_approved",
			}
			action_plan.verification_status = level_map.get(review_level, "pending")
			action_plan.save(update_fields=["verification_status", "updated_at"])

			# If case-level approval, mark case as verified
			if review_level == "case":
				case.status = Case.Status.VERIFIED
				case.save(update_fields=["status", "updated_at"])
		elif action == "reject":
			action_plan.verification_status = "rejected"
			action_plan.save(update_fields=["verification_status", "updated_at"])

		return Response(ReviewLogSerializer(log).data, status=status.HTTP_201_CREATED)


class CaseReviewHistoryView(APIView):
	def get(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		logs = ReviewLog.objects.filter(action_plan__case=case).select_related("reviewer").order_by("-created_at")
		return Response(ReviewLogSerializer(logs, many=True).data)