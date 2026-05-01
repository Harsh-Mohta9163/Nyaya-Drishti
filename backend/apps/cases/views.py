from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.action_plans.services.plan_generator import generate_or_refresh_action_plan
from apps.reviews.models import ReviewLog
from apps.reviews.serializers import ReviewLogSerializer

from .models import Case, ExtractedData
from .serializers import CaseSerializer, CaseStatusSerializer


class CaseListCreateView(ListCreateAPIView):
	queryset = Case.objects.select_related("uploaded_by").all().order_by("-created_at")
	serializer_class = CaseSerializer

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


class CaseExtractView(APIView):
	def post(self, request, pk):
		case = get_object_or_404(Case, pk=pk)

		from .services.extractor import extract_structured_data
		from .services.pdf_processor import extract_text_from_pdf
		from .services.section_segmenter import segment_judgment

		pdf_text = extract_text_from_pdf(case.pdf_file.path)
		sections = segment_judgment(pdf_text)
		extracted_payload = extract_structured_data(case=case, sections=sections)

		ExtractedData.objects.update_or_create(
			case=case,
			defaults={
				"header_data": extracted_payload.get("header_data", {}),
				"operative_order": extracted_payload.get("operative_order", ""),
				"court_directions": extracted_payload.get("court_directions", []),
				"order_type": extracted_payload.get("order_type", "unknown"),
				"entities": extracted_payload.get("entities", []),
				"extraction_confidence": extracted_payload.get("extraction_confidence", 0.0),
				"source_references": extracted_payload.get("source_references", []),
			},
		)

		case.status = Case.Status.EXTRACTED
		case.ocr_confidence = extracted_payload.get("ocr_confidence", 0.0)
		case.save(update_fields=["status", "ocr_confidence", "updated_at"])

		return Response(CaseSerializer(case).data, status=status.HTTP_200_OK)


class CaseActionPlanView(APIView):
	def post(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		action_plan = generate_or_refresh_action_plan(case)
		return Response({"action_plan": action_plan.id}, status=status.HTTP_200_OK)


class CaseReviewHistoryView(APIView):
	def get(self, request, pk):
		case = get_object_or_404(Case, pk=pk)
		logs = ReviewLog.objects.filter(action_plan__case=case).order_by("-created_at")
		return Response(ReviewLogSerializer(logs, many=True).data)