import logging
import os
import uuid
import fitz  # PyMuPDF
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Department
from apps.accounts.permissions import (
    DepartmentScopedQuerysetMixin,
    GLOBAL_ACCESS_ROLES,
    user_can_verify,
)
from apps.action_plans.models import ActionPlan
from apps.action_plans.serializers import ActionPlanSerializer
from apps.reviews.models import ReviewLog
from apps.reviews.serializers import ReviewLogSerializer

from .models import Case, Judgment, Citation
from .serializers import CaseSerializer, CaseStatusSerializer, JudgmentSerializer
from .services.pdf_processor import extract_text_from_pdf
from .services.section_segmenter import segment_judgment
from .services.extractor import extract_structured_data


def _build_snippets(text: str) -> list[str]:
    """Construct a ranked list of anchor snippets to search for in the PDF.

    We want snippets that are likely to be unique to this directive, so we
    sample from multiple positions in the text (start, ~middle, ~end) at
    multiple lengths. PyMuPDF's `search_for` is exact-match (after some
    whitespace normalization), so shorter snippets are more forgiving when
    the PDF re-flows text with extra whitespace.
    """
    snippets: list[str] = []
    text = text.strip()
    if not text:
        return snippets
    # Beginning chunks — longest first so we prefer a tight match.
    for slen in (140, 100, 70, 45, 28):
        s = text[:slen].strip()
        if s and s not in snippets:
            snippets.append(s)
    # Sample further into the text to skip leading legal-reasoning preamble.
    for offset in (50, 100, 180):
        if len(text) > offset + 30:
            s = text[offset:offset + 70].strip()
            if s and s not in snippets:
                snippets.append(s)
    # Tail chunk — useful when extraction picked up the closing sentence.
    if len(text) > 100:
        tail = text[-80:].strip()
        if tail and tail not in snippets:
            snippets.append(tail)
    return snippets


def _approximate_overlap(haystack: str, needle: str, window: int = 15) -> int:
    """How many chars of `needle` appear as non-overlapping windows in `haystack`."""
    if not haystack or not needle:
        return 0
    h = haystack.lower()
    n = needle.lower()
    total = 0
    for i in range(0, len(n) - window + 1, window):
        if n[i:i + window] in h:
            total += window
    return total


def _block_text(block: dict) -> str:
    """Reconstruct a text block's content from its line/span dict structure."""
    out = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            out.append(span.get("text", ""))
        out.append(" ")
    return "".join(out).strip()


def _block_rects(block: dict) -> list[dict]:
    """Line-level rects for a single PyMuPDF text block."""
    rects = []
    for line in block.get("lines", []):
        bbox = line.get("bbox")
        if not bbox or len(bbox) < 4:
            continue
        lx0, ly0, lx1, ly1 = bbox
        if lx1 - lx0 <= 0 or ly1 - ly0 <= 0:
            continue
        rects.append({
            "x0": round(lx0, 2), "y0": round(ly0, 2),
            "x1": round(lx1, 2), "y1": round(ly1, 2),
        })
    return rects


def _build_paragraph_location(page, anchor_rect, full_text: str) -> dict | None:
    """Given a page and the rect of a matched snippet, return a sourceLocation
    dict whose `rects` cover the FULL paragraph (text block) containing the
    anchor — plus the next block(s) if the directive text overflows.

    Falls back to a single-rect location if block detection fails entirely.
    """
    try:
        page_dict = page.get_text("dict")
    except Exception:
        page_dict = {"blocks": []}

    text_blocks = [b for b in page_dict.get("blocks", []) if b.get("type") == 0]

    # Find the block whose bbox vertically + horizontally contains anchor_rect.
    anchor_idx = None
    for idx, blk in enumerate(text_blocks):
        bx0, by0, bx1, by1 = blk.get("bbox", (0, 0, 0, 0))
        if (bx0 - 3 <= anchor_rect.x0 and anchor_rect.x1 <= bx1 + 3
                and by0 - 3 <= anchor_rect.y0 and anchor_rect.y1 <= by1 + 3):
            anchor_idx = idx
            break

    page_rect = page.rect
    if anchor_idx is None:
        # Couldn't resolve to a paragraph block — return just the snippet rect.
        return {
            "page": page.number + 1,
            "page_width": round(page_rect.width, 2),
            "page_height": round(page_rect.height, 2),
            "rects": [{
                "x0": round(anchor_rect.x0, 2), "y0": round(anchor_rect.y0, 2),
                "x1": round(anchor_rect.x1, 2), "y1": round(anchor_rect.y1, 2),
            }],
        }

    # Start with all line rects from the anchor paragraph.
    rects = list(_block_rects(text_blocks[anchor_idx]))
    covered = _block_text(text_blocks[anchor_idx])

    # If the anchor block doesn't cover a large fraction of the directive
    # text, the directive probably spans into the next paragraph(s).
    # Extend forward as long as each next block has meaningful overlap with
    # the directive text and is vertically adjacent.
    full_lower = full_text.lower()
    target_chars = max(80, int(len(full_text) * 0.55))
    overlap = _approximate_overlap(covered, full_text)
    cursor = anchor_idx
    while overlap < target_chars and cursor + 1 < len(text_blocks):
        next_blk = text_blocks[cursor + 1]
        next_text = _block_text(next_blk)
        next_overlap = _approximate_overlap(next_text, full_text)
        if next_overlap < 15:
            break  # Next paragraph doesn't seem to belong to this directive.
        # Reject blocks too far below the anchor (likely a different paragraph).
        prev_by1 = text_blocks[cursor]["bbox"][3]
        next_by0 = next_blk["bbox"][1]
        if next_by0 - prev_by1 > 60:  # > ~60pt vertical gap = different section
            break
        rects.extend(_block_rects(next_blk))
        covered += " " + next_text
        overlap = _approximate_overlap(covered, full_text)
        cursor += 1

    return {
        "page": page.number + 1,
        "page_width": round(page_rect.width, 2),
        "page_height": round(page_rect.height, 2),
        "rects": rects,
    }


def _annotate_source_locations(pdf_path: str, directions: list[dict]) -> list[dict]:
    """For each directive, find its source paragraph in the PDF and annotate
    `source_location` with page + page dims + line-level rects covering the
    whole paragraph.

    STRATEGY:
      1. Search anchor snippets in REVERSE page order (operative orders sit at
         the end of judgments — this avoids false-positive matches in earlier
         reasoning sections).
      2. Once a match is found, resolve the containing TEXT BLOCK via
         `page.get_text("dict")` and emit ALL line rects for that block.
      3. If the directive's text exceeds what fits in the anchor block,
         walk forward to the next adjacent block(s) and add their lines too.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Could not open PDF %s: %s", pdf_path, e)
        return directions

    total_pages = len(doc)
    # Pass 1 looks at the last 30% of pages — operative orders live here.
    back_threshold = max(1, int(total_pages * 0.70))
    page_ranges = (
        range(total_pages - 1, back_threshold - 1, -1),
        range(back_threshold - 1, -1, -1),
    )

    try:
        for direction in directions:
            # Defensive: Agent 4 sometimes returns a dict where a string is
            # expected (Pydantic schema is prompt-side only, not validated on
            # the response). Coerce non-string values to empty so the upload
            # doesn't crash — that directive simply gets no source highlight.
            raw_text = direction.get("text") or direction.get("description") or ""
            text = raw_text.strip() if isinstance(raw_text, str) else ""
            if not text:
                direction["source_location"] = None
                continue

            snippets = _build_snippets(text)
            location = None

            # Try the EARLIEST-text snippet first across all pages (reverse
            # order so the operative-order section wins over earlier prose).
            # Falling through to later/middle/tail snippets only happens when
            # the start-of-text snippet doesn't appear anywhere. This avoids
            # anchoring on a continuation line of the paragraph that lives on
            # the *next* PDF page (which the start-of-text actually doesn't
            # touch).
            for snippet in snippets:
                if location:
                    break
                for page_range in page_ranges:
                    if location:
                        break
                    for page_idx in page_range:
                        page = doc[page_idx]
                        try:
                            rects = page.search_for(snippet)
                        except Exception:
                            rects = []
                        if not rects:
                            continue
                        # First rect = top-most match on the page.
                        anchor = rects[0]
                        loc = _build_paragraph_location(page, anchor, text)
                        if loc:
                            location = loc
                            break

            # Write BOTH key shapes so the snake_case backend reader and the
            # camelCase frontend mapping both see the fresh location. Once
            # written, the App.tsx mapping (`d.sourceLocation || d.source_location`)
            # will pick this up regardless.
            direction["source_location"] = location
            direction["sourceLocation"] = location
    finally:
        doc.close()

    return directions


class CaseListCreateView(DepartmentScopedQuerysetMixin, ListCreateAPIView):
    queryset = Case.objects.all().order_by("-created_at")
    serializer_class = CaseSerializer
    parser_classes = [MultiPartParser, FormParser]


class CaseDetailView(DepartmentScopedQuerysetMixin, RetrieveAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer


class CaseDepartmentOverrideView(APIView):
    """PATCH /api/cases/<uuid>/department/

    Verifier endpoint to correct an AI department mis-classification.
    Body: {"primary_department": "HEALTH", "secondary_departments": ["FINANCE","PWD"]}

    Permission rules:
      - CENTRAL_LAW / STATE_MONITORING roles: can reassign any case.
      - HEAD_LEGAL_CELL: can reassign only if their dept is the current primary,
        appears in current secondaries, or matches the proposed new primary
        (so an HLC can pull a mis-routed case INTO their dept).
      - Other roles: forbidden.

    Every change writes a ReviewLog with action="department_override" for audit.
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        case = get_object_or_404(Case, pk=pk)
        user = request.user

        new_primary_code = (request.data.get("primary_department") or "").strip().upper()
        new_secondary_codes = [
            (c or "").strip().upper()
            for c in (request.data.get("secondary_departments") or [])
            if c
        ]

        is_global = user.role in GLOBAL_ACCESS_ROLES
        is_hlc_allowed = (
            user.role == "head_legal_cell"
            and user.department_id
            and (
                case.primary_department_id == user.department_id
                or case.secondary_departments.filter(id=user.department_id).exists()
                or (user.department and user.department.code == new_primary_code)
            )
        )
        if not (is_global or is_hlc_allowed):
            return Response(
                {"error": "You don't have permission to reassign this case."},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_primary = case.primary_department.code if case.primary_department else None
        old_secondary = list(case.secondary_departments.values_list("code", flat=True))

        if new_primary_code:
            new_primary = Department.objects.filter(code=new_primary_code, is_active=True).first()
            if not new_primary:
                return Response(
                    {"error": f"Unknown department code: {new_primary_code}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            case.primary_department = new_primary

        case.save()
        # Update the M2M after save() so the new state is committed first.
        if "secondary_departments" in request.data:
            case.secondary_departments.set(
                Department.objects.filter(code__in=new_secondary_codes, is_active=True)
            )

        # Audit row — attaches to the case's action plan if one exists,
        # otherwise we skip (review log model requires an action_plan FK).
        judgment = case.judgments.first()
        action_plan = ActionPlan.objects.filter(judgment=judgment).first() if judgment else None
        if action_plan:
            ReviewLog.objects.create(
                action_plan=action_plan,
                reviewer=user,
                review_level=user.role,
                action="department_override",
                notes=(
                    f"primary: {old_primary} -> {new_primary_code}; "
                    f"secondary: {old_secondary} -> {new_secondary_codes}"
                ),
            )

        case.refresh_from_db()
        return Response(CaseSerializer(case).data)


class JudgmentUpdateView(RetrieveUpdateAPIView):
    queryset = Judgment.objects.all()
    serializer_class = JudgmentSerializer
    http_method_names = ['get', 'patch', 'put']
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        # GET is allowed for any authenticated user (read-only context),
        # but writes (PATCH/PUT) are restricted to verifier roles only.
        if not user_can_verify(request.user):
            return Response(
                {"detail": "Only Head of Legal Cell or Central Law can edit extraction."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

class CaseExtractView(APIView):
    """
    The main ingestion pipeline for a new judgment.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        import hashlib
        pdf_file = request.FILES.get("pdf_file")
        if not pdf_file:
            return Response({"error": "No PDF file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # ─── Dedup: SHA-256 the PDF bytes BEFORE creating any rows ─────────
        # If we've already extracted this exact file, return the existing
        # Case with a "duplicate=true" flag instead of re-running the LLM
        # pipeline (~60s + LLM credit cost).
        hasher = hashlib.sha256()
        for chunk in pdf_file.chunks():
            hasher.update(chunk)
        pdf_file.seek(0)  # rewind so the FileField save() can still read it
        pdf_hash = hasher.hexdigest()

        existing = (
            Judgment.objects
            .filter(pdf_hash=pdf_hash)
            .select_related("case__primary_department")
            .first()
        )
        if existing:
            return Response(
                {
                    **CaseSerializer(existing.case).data,
                    "duplicate": True,
                    "duplicate_message": (
                        f"This PDF was already uploaded (hash match). "
                        f"Returning the existing case extracted on "
                        f"{existing.created_at:%Y-%m-%d %H:%M}."
                    ),
                },
                status=status.HTTP_200_OK,
            )

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
            processing_status="parsing",
            pdf_hash=pdf_hash,
        )

        try:
            # 2. PyMuPDF4LLM → Markdown
            pdf_path = judgment.pdf_file.path
            markdown_text = extract_text_from_pdf(pdf_path)

            # Count pages once — used to route large PDFs through OpenRouter
            # (Groq 8B 413s and NVIDIA NIM read-times-out on long inputs).
            try:
                with fitz.open(pdf_path) as _doc:
                    page_count = _doc.page_count
            except Exception:
                page_count = 0

            # 3. Regex Segmenter
            segments = segment_judgment(markdown_text)

            # 4. LLM Extraction (4 agents)
            judgment.processing_status = "extracting"
            judgment.save()

            extracted_data = extract_structured_data(
                judgment_id=str(judgment.id),
                header_text=segments.get("header", ""),
                middle_text=segments.get("middle", ""),
                operative_text=segments.get("operative_order", ""),
                page_count=page_count,
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

            # ── Second-pass enrichment ─────────────────────────────────────
            # Classify each directive as government-action vs informational
            # and generate implementation steps. Failure here is non-fatal —
            # the user still gets the verbatim directives.
            try:
                from apps.cases.services.directive_enricher import enrich_case_directives
                enrich_result = enrich_case_directives(case)
                print(
                    f"  [Enrichment] case={case.case_number[:40]} "
                    f"updated={enrich_result.get('updated', 0)} "
                    f"method={enrich_result.get('method', '?')}"
                )
            except Exception as enrich_err:
                logging.getLogger(__name__).warning(
                    "Directive enrichment failed for case %s: %s", case.id, enrich_err
                )
                print(f"  [Enrichment] FAILED for case {case.case_number[:40]}: {enrich_err}")

            # ── Auto-create ActionPlan + demo deadlines ───────────────────
            # For the demo, the deadlines must land in the future even though
            # the source PDFs are historical judgments. The shared helper
            # creates an ActionPlan with the demo deadline profile and
            # auto-approves it so the LCO Execution view filter (which
            # requires verification_status startswith "approved") will surface
            # any per-directive isVerified ticks the HLC makes — consistent
            # with how the seeded demo cases behave. The per-directive
            # isVerified checkbox remains the HLC's real verification gate.
            try:
                from apps.action_plans.services.demo_helpers import ensure_demo_plan
                plan, summary = ensure_demo_plan(case, auto_approve=True)
                if plan and summary:
                    print(
                        f"  [DemoDeadlines] case={case.case_number[:40]} "
                        f"internal={summary['internal_compliance']} "
                        f"compliance={summary['compliance']} "
                        f"appeal={summary['statutory_appeal']} "
                        f"did_approve={summary['did_approve']}"
                    )
            except Exception as deadline_err:
                logging.getLogger(__name__).warning(
                    "Demo deadline application failed for case %s: %s",
                    case.id, deadline_err,
                )

            # Ensure status is set (extractor sets "completed", normalize to "complete").
            # CRITICAL: use update_fields so we DON'T overwrite court_directions —
            # enrich_case_directives() above wrote to court_directions via a
            # fresh judgment instance, but our local `judgment` variable is
            # stale and would clobber that enrichment if we did a full save().
            if judgment.processing_status not in ("failed",):
                judgment.processing_status = "complete"
                judgment.save(update_fields=["processing_status", "updated_at"])

            return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            import traceback, logging
            tb = traceback.format_exc()
            logging.getLogger(__name__).error(f"Extraction failed for judgment {judgment.id}:\n{tb}")
            judgment.processing_status = "failed"
            # update_fields keeps us from clobbering any partial extraction
            # that did succeed before the error point.
            judgment.save(update_fields=["processing_status", "updated_at"])
            # Include the exception class + traceback summary so the frontend
            # surfaces something actionable instead of a generic 500.
            return Response(
                {
                    "error": f"{type(e).__name__}: {e}",
                    "judgment_id": str(judgment.id),
                    "case_id": str(judgment.case_id),
                    "stage": judgment.processing_status,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        if not user_can_verify(request.user):
            return Response(
                {"detail": "Only Head of Legal Cell or Central Law can verify Action Plans."},
                status=status.HTTP_403_FORBIDDEN,
            )
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