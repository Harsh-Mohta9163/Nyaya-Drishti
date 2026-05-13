import os
import uuid
import fitz  # PyMuPDF
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.action_plans.models import ActionPlan
from apps.action_plans.serializers import ActionPlanSerializer
from apps.reviews.models import ReviewLog
from apps.reviews.serializers import ReviewLogSerializer

from .models import Case, Judgment, Citation
from .serializers import CaseSerializer, CaseStatusSerializer, JudgmentSerializer
from .services.pdf_processor import extract_text_from_pdf
from .services.section_segmenter import segment_judgment
from .services.extractor import extract_structured_data


def _annotate_source_locations(pdf_path: str, directions: list[dict]) -> list[dict]:
    """
    For each court direction, find ALL bounding boxes in the PDF using PyMuPDF.
    Stores page number, page dimensions (for frontend scaling), and an array
    of rects covering the full paragraph — not just the first line.
    """
    try:
        doc = fitz.open(pdf_path)

        for direction in directions:
            text = (direction.get("text") or "").strip()
            if not text:
                direction["source_location"] = None
                continue

            found = False
            for page in doc:
                # Try progressively shorter snippets for robustness
                for snippet_len in [120, 80, 50, 30]:
                    snippet = text[:snippet_len].strip()
                    if not snippet:
                        continue
                    rects = page.search_for(snippet)
                    if not rects:
                        continue

                    # Collect all rects for the beginning of the text
                    all_rects = [{"x0": round(r.x0, 2), "y0": round(r.y0, 2),
                                  "x1": round(r.x1, 2), "y1": round(r.y1, 2)}
                                 for r in rects]

                    # Search for later parts of the text to cover the full paragraph
                    if len(text) > snippet_len:
                        later = text[snippet_len:snippet_len + 60].strip()
                        if later:
                            for sl in [min(len(later), 50), 30]:
                                more = page.search_for(later[:sl])
                                if more:
                                    for r in more:
                                        rd = {"x0": round(r.x0, 2), "y0": round(r.y0, 2),
                                              "x1": round(r.x1, 2), "y1": round(r.y1, 2)}
                                        if rd not in all_rects:
                                            all_rects.append(rd)
                                    break

                    page_rect = page.rect
                    direction["source_location"] = {
                        "page": page.number + 1,          # 1-indexed
                        "page_width": round(page_rect.width, 2),
                        "page_height": round(page_rect.height, 2),
                        "rects": all_rects,
                    }
                    found = True
                    break  # snippet_len loop
                if found:
                    break  # page loop

            if not found:
                direction["source_location"] = None

        doc.close()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error annotating source locations: {str(e)}")

    return directions


class CaseListCreateView(ListCreateAPIView):
    queryset = Case.objects.all().order_by("-created_at")
    serializer_class = CaseSerializer
    parser_classes = [MultiPartParser, FormParser]


class CaseDetailView(RetrieveAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer


class JudgmentUpdateView(RetrieveUpdateAPIView):
    queryset = Judgment.objects.all()
    serializer_class = JudgmentSerializer
    http_method_names = ['get', 'patch', 'put']

class CaseExtractView(APIView):
    """
    The main ingestion pipeline for a new judgment.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        pdf_file = request.FILES.get("pdf_file")
        if not pdf_file:
            return Response({"error": "No PDF file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Create Judgment (and Case if we don't have metadata yet)
        # We will create a dummy case first, then update it after extraction
        temp_id = uuid.uuid4().hex[:8]
        case = Case.objects.create(
            court_name=f"Pending Extraction {temp_id}",
            case_type="Pending",
            case_number=f"Pending {temp_id}",
            case_year=0,
            status=Case.Status.PENDING,
            uploaded_by=request.user if request.user.is_authenticated else None
        )
        
        judgment = Judgment.objects.create(
            case=case,
            date_of_order="2000-01-01",  # Placeholder
            pdf_file=pdf_file,
            processing_status="parsing"
        )

        try:
            # 2. PyMuPDF4LLM → Markdown
            pdf_path = judgment.pdf_file.path
            markdown_text = extract_text_from_pdf(pdf_path)

            # 3. Regex Segmenter
            segments = segment_judgment(markdown_text)

            # 4. Gemini Extraction (3 calls)
            judgment.processing_status = "extracting"
            judgment.save()
            
            extracted_data = extract_structured_data(
                judgment_id=str(judgment.id),
                header_text=segments.get("header", ""),
                middle_text=segments.get("middle", ""),
                operative_text=segments.get("operative_order", "")
            )

            # Refresh from DB — extract_structured_data saves internally
            # NOTE: The extractor may delete the original temp case and re-point
            # the judgment to an existing case (dedup logic). So we must get the
            # case from the judgment, not refresh the potentially-deleted local var.
            judgment.refresh_from_db()
            case = judgment.case

            # 5. Source Highlighting — annotate with PyMuPDF bounding boxes
            if judgment.court_directions:
                judgment.court_directions = _annotate_source_locations(pdf_path, judgment.court_directions)
                judgment.save()

            # Ensure status is set (extractor sets "completed", normalize to "complete")
            if judgment.processing_status not in ("failed",):
                judgment.processing_status = "complete"
                judgment.save()

            return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            judgment.processing_status = "failed"
            judgment.save()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CaseStatusView(APIView):
    def get(self, request, pk, *args, **kwargs):
        case = get_object_or_404(Case, pk=pk)
        return Response(CaseStatusSerializer(case).data)


class ServePdfView(APIView):
    # Public — PDFs need to be fetchable by react-pdf without auth headers
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk, *args, **kwargs):
        judgment = get_object_or_404(Judgment, pk=pk)
        if not judgment.pdf_file:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        file_path = judgment.pdf_file.path
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
            # Explicit CORS header for cross-origin PDF loading (react-pdf)
            response["Access-Control-Allow-Origin"] = "*"
            return response
        return Response(status=status.HTTP_404_NOT_FOUND)


class CaseActionPlanView(APIView):
    def get(self, request, pk, *args, **kwargs):
        judgment = get_object_or_404(Judgment, case_id=pk)
        try:
            action_plan = judgment.action_plan
            return Response(ActionPlanSerializer(action_plan).data)
        except ActionPlan.DoesNotExist:
            return Response({"detail": "Action plan not generated yet."}, status=404)


class ActionPlanReviewView(APIView):
    def post(self, request, pk, *args, **kwargs):
        action_plan = get_object_or_404(ActionPlan, pk=pk)
        
        review_level = request.data.get("review_level", "L1")
        action = request.data.get("action", "approved")
        notes = request.data.get("notes", "")

        ReviewLog.objects.create(
            action_plan=action_plan,
            reviewer=request.user if request.user.is_authenticated else None,
            review_level=review_level,
            action=action,
            notes=notes,
        )

        if action == "approved":
            action_plan.verification_status = f"approved_by_{review_level.lower()}"
            action_plan.save()

        return Response({"status": "Review recorded"})


class AppealStrategyView(APIView):
    def post(self, request, case_id, judgment_id, *args, **kwargs):
        judgment = get_object_or_404(Judgment, id=judgment_id, case_id=case_id)
        from apps.action_plans.services.appeal_strategist import generate_appeal_strategy
        
        strategy = generate_appeal_strategy(str(judgment.id))
        
        # Save to ActionPlan if exists
        action_plan, _ = ActionPlan.objects.get_or_create(judgment=judgment)
        action_plan.appeal_viability = strategy.get("appeal_viability", "")
        action_plan.appeal_strategy = strategy.get("appeal_strategy", "")
        action_plan.appeal_precedents = strategy.get("appeal_precedents", [])
        action_plan.save()
        
        return Response(strategy)


class ReAnnotateSourceView(APIView):
    """Re-run PyMuPDF source annotation on existing court_directions for a case."""
    authentication_classes = []
    permission_classes = []

    def post(self, request, pk, *args, **kwargs):
        case = get_object_or_404(Case, pk=pk)
        judgment = case.judgments.first()
        if not judgment:
            return Response({"error": "No judgment found"}, status=404)
        if not judgment.court_directions:
            return Response({"error": "No court directions to annotate"}, status=400)
        if not judgment.pdf_file:
            return Response({"error": "No PDF file associated"}, status=400)

        try:
            pdf_path = judgment.pdf_file.path
            judgment.court_directions = _annotate_source_locations(
                pdf_path, judgment.court_directions
            )
            judgment.save()
            return Response(JudgmentSerializer(judgment).data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)