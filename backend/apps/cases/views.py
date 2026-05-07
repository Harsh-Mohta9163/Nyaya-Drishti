import os
import uuid
import fitz  # PyMuPDF
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
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
    For each court direction, find its bounding box and char offset in the PDF.
    Uses PyMuPDF page.search_for() for spatial location.
    """
    try:
        doc = fitz.open(pdf_path)
        char_offset = 0  # running char count across pages

        # Build a page-text map for char offsets
        page_texts = []
        for page in doc:
            t = page.get_text("text")
            page_texts.append((page.number, t, char_offset))
            char_offset += len(t)

        for direction in directions:
            snippet = (direction.get("text") or "")[:80]  # use first 80 chars to search
            if not snippet:
                continue

            found = False
            for page in doc:
                rects = page.search_for(snippet)
                if rects:
                    r = rects[0]  # first occurrence
                    # Character offset in full text
                    page_num, page_text, page_char_start = page_texts[page.number]
                    local_idx = page_text.find(snippet[:40])
                    char_start = page_char_start + local_idx if local_idx != -1 else -1

                    direction["source_location"] = {
                        "page": page.number + 1,  # 1-indexed for frontend
                        "x0": round(r.x0, 2),
                        "y0": round(r.y0, 2),
                        "x1": round(r.x1, 2),
                        "y1": round(r.y1, 2),
                        "char_start": char_start,
                        "char_end": char_start + len(snippet) if char_start != -1 else -1,
                    }
                    found = True
                    break

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

            # 5. Update Case with Header info
            if "header" in extracted_data:
                h = extracted_data["header"]
                case.case_number = h.get("case_number", "")
                case.court_name = h.get("court_name", "")
                case.case_type = h.get("case_type", "")
                case.petitioner_name = h.get("petitioner_name", "")
                case.respondent_name = h.get("respondent_name", "")
                try:
                    case.case_year = int(h.get("date_of_order", "2000")[:4])
                except:
                    case.case_year = 2000
                case.save()
                
                judgment.date_of_order = h.get("date_of_order", "2000-01-01")
                judgment.save()

            # 6. Source Highlighting
            if judgment.court_directions:
                judgment.court_directions = _annotate_source_locations(pdf_path, judgment.court_directions)
                judgment.save()
                
            # 7. Citations creation
            if "_cases_cited" in extracted_data:
                for cited_raw in extracted_data["_cases_cited"]:
                    Citation.objects.create(
                        citing_judgment=judgment,
                        cited_case_name_raw=cited_raw
                    )

            judgment.processing_status = "complete"
            judgment.save()
            
            # (TODO) Vectorize here in Phase 6.

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
    def get(self, request, pk, *args, **kwargs):
        judgment = get_object_or_404(Judgment, pk=pk)
        if not judgment.pdf_file:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        file_path = judgment.pdf_file.path
        if os.path.exists(file_path):
            return FileResponse(open(file_path, "rb"), content_type="application/pdf")
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