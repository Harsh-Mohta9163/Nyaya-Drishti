"""
populate_rag.py — Nyaya-Drishti RAG ingestion pipeline
=======================================================
Downloads PDFs from AWS Open Data, extracts structured legal data via LLM,
stores in Django models, and indexes into ChromaDB.

IMPORTANT:
- --count N means "download and attempt exactly N PDFs", not "keep trying until N succeed"
- --full-reset wipes DB + PDFs + ChromaDB before starting
- --min-size filters PDFs by file size (KB) to skip short interim orders
- Only creates DB records AFTER successful LLM extraction (no zombies)
"""
import os
import glob
import logging
import time
import uuid
from django.core.management.base import BaseCommand
from apps.action_plans.services.rag_engine import HybridRAGEngine, reset_collection
from apps.cases.models import Case, Judgment

logger = logging.getLogger(__name__)

# Minimum PDF size in bytes to consider for ingestion (skip short orders)
DEFAULT_MIN_SIZE_KB = 100  # 100KB ~ 5+ page judgment


class Command(BaseCommand):
    help = "Populate the RAG vector store and database with Karnataka HC judgments"

    def add_arguments(self, parser):
        parser.add_argument("--source", type=str, default="aws_s3", choices=["pdfs", "aws_s3"])
        parser.add_argument("--path", type=str, default="")
        parser.add_argument("--prefix", type=str,
                          default="data/pdf/year=2024/court=29_3/bench=karnataka_bng_old/")
        parser.add_argument("--count", type=int, default=2,
                          help="Exact number of PDFs to download and process")
        parser.add_argument("--min-size", type=int, default=DEFAULT_MIN_SIZE_KB,
                          help="Minimum PDF size in KB (skip small interim orders). Default 100KB")
        parser.add_argument("--reset", action="store_true",
                          help="Reset ChromaDB only")
        parser.add_argument("--full-reset", action="store_true",
                          help="Reset ChromaDB + DB + media PDFs")
        parser.add_argument("--provider", type=str, default="",
                          choices=["", "gemini", "nvidia", "groq"])
        parser.add_argument("--gov-only", action="store_true",
                          help="Only keep cases where government is a party")

    def handle(self, *args, **options):
        if options.get("provider"):
            from django.conf import settings
            settings.LLM_PROVIDER = options["provider"]
            self.stdout.write(self.style.WARNING(
                f"Using LLM provider: {options['provider']}"))

        if options.get("full_reset") or options.get("reset"):
            self.stdout.write(self.style.WARNING("Resetting ChromaDB collection..."))
            reset_collection()
            self.stdout.write(self.style.SUCCESS("Collection reset."))

        if options.get("full_reset"):
            self._do_full_reset()

        rag = HybridRAGEngine()
        source = options["source"]

        if source == "pdfs":
            self._load_pdfs(rag, options["path"], options.get("gov_only", False))
        elif source == "aws_s3":
            self._load_aws_s3(rag, options["prefix"], options["count"],
                            options["min_size"], options.get("gov_only", False))

    def _do_full_reset(self):
        """Delete all DB records AND physical PDF files."""
        self.stdout.write(self.style.WARNING("Deleting all Case/Judgment DB records..."))
        count_cases = Case.objects.count()
        Case.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count_cases} DB records."))

        from django.conf import settings
        media_judgments = os.path.join(settings.MEDIA_ROOT, "judgments")
        if os.path.exists(media_judgments):
            pdf_files = [f for f in os.listdir(media_judgments) if f.lower().endswith(".pdf")]
            self.stdout.write(self.style.WARNING(
                f"Deleting {len(pdf_files)} PDFs from {media_judgments}..."))
            for f in pdf_files:
                try:
                    os.remove(os.path.join(media_judgments, f))
                except OSError:
                    pass
            self.stdout.write(self.style.SUCCESS(f"Deleted {len(pdf_files)} old PDFs."))

    # Government party keywords for --gov-only filter
    _GOV_KEYWORDS = [
        "state of", "union of india", "government", "commissioner",
        "secretary", "municipal", "collector", "district magistrate",
        "superintendent of police", "chief secretary", "director general",
        "registrar", "controller", "inspector general", "deputy commissioner",
        "sub-divisional", "tehsildar", "ministry of", "department of",
        "corporation of", "panchayat", "nagar", "zilla",
    ]

    def _is_government_party(self, header_text: str) -> bool:
        """Fast check for government entities in the header before wasting LLM calls."""
        text = header_text.lower()
        return any(kw in text for kw in self._GOV_KEYWORDS)

    def _process_pdf_file(self, pdf_path: str, rag: HybridRAGEngine, gov_only: bool = False) -> bool:
        """
        Process a single PDF. Returns True on success, False on failure.
        
        KEY DESIGN: All DB writes happen ONLY after successful LLM extraction.
        If anything fails, nothing is written to DB and no orphan PDF is left.
        """
        from apps.cases.services.pdf_processor import extract_text_from_pdf
        from apps.cases.services.section_segmenter import segment_judgment
        from apps.cases.services.extractor import extract_structured_data
        from django.core.files import File

        filename = os.path.basename(pdf_path)

        # ===== STEP 1: Extract text (no DB writes) =====
        self.stdout.write("  [Step 1/4] Extracting text from PDF...")
        text = extract_text_from_pdf(pdf_path)
        char_count = len(text)
        page_est = max(1, char_count // 3000)
        self.stdout.write(f"  Extracted {char_count} characters (~{page_est} pages)")

        if char_count < 1000:
            self.stdout.write(self.style.WARNING(
                f"  SKIPPING: Too short ({char_count} chars). Likely a cover page or notice."))
            return False

        # ===== STEP 2: Segment (no DB writes) =====
        self.stdout.write("  [Step 2/4] Segmenting judgment...")
        sections = segment_judgment(text)
        h_len = len(sections.get("header", ""))
        m_len = len(sections.get("middle", ""))
        o_len = len(sections.get("operative_order", ""))
        self.stdout.write(
            f"  Header: {h_len} | Middle: {m_len} | Operative: {o_len}")

        # ===== FAST FAIL: Government Party Check =====
        if gov_only:
            if not self._is_government_party(sections.get("header", "")):
                self.stdout.write(self.style.WARNING(
                    "  SKIPPING: No government keywords found in the header text."))
                return False

        # ===== STEP 3: Create TEMP DB records + LLM extraction =====
        # We must create the records because extractor.py needs a judgment_id to save to.
        # If LLM fails, we delete them.
        self.stdout.write("  [Step 3/4] LLM structured extraction (3 calls)...")

        temp_id = str(uuid.uuid4())[:8]
        case = Case.objects.create(
            court_name=f"_temp_{temp_id}",
            case_number=filename,
            case_year=2024,
            case_type="PDF Import",
            status="disposed",
            petitioner_name="",
            respondent_name="",
        )
        judgment = Judgment.objects.create(
            case=case,
            date_of_order="2024-01-01",
            processing_status="extracting",
        )
        # Save PDF file
        with open(pdf_path, "rb") as f:
            judgment.pdf_file.save(filename, File(f))

        try:
            extracted = extract_structured_data(
                judgment_id=str(judgment.id),
                header_text=sections.get("header", ""),
                middle_text=sections.get("middle", ""),
                operative_text=sections.get("operative_order", ""),
            )
        except Exception as e:
            # LLM FAILED — clean up everything, leave no trace
            self.stderr.write(self.style.ERROR(f"  LLM FAILED: {e}"))
            self._cleanup_failed(judgment, case)
            return False

        # ===== STEP 4: LLM succeeded — refresh & vectorize =====
        judgment.refresh_from_db()
        case.refresh_from_db()

        # Verify it actually extracted something
        if case.court_name.startswith("_temp_"):
            self.stderr.write(self.style.ERROR(
                "  LLM returned data but Case was not updated. Cleaning up."))
            self._cleanup_failed(judgment, case)
            return False

        self.stdout.write(f"  Case: {case.case_number} | {case.court_name}")

        self.stdout.write("  [Step 4/4] Embedding into ChromaDB...")
        doc_text = f"{judgment.summary_of_facts}\n\n{judgment.ratio_decidendi}"
        if len(doc_text.strip()) < 10:
            doc_text = sections.get("operative_order", text[-3000:])

        doc = {
            "text": doc_text,
            "metadata": {
                "id": str(judgment.id),
                "case_id": str(case.id),
                "case_number": case.case_number,
                "court_name": case.court_name,
                "disposition": judgment.disposition,
                "winning_party_type": judgment.winning_party_type,
                "document_type": judgment.document_type,
                "case_type": case.case_type,
                "year": case.case_year,
                "contempt_risk": judgment.contempt_risk,
                "appeal_type": judgment.appeal_type,
                "has_financial_implications": bool(judgment.financial_implications),
                "area_of_law": case.area_of_law,
                "precedent_status": judgment.precedent_status,
            },
        }
        rag.add_documents([doc])

        self.stdout.write(self.style.SUCCESS(
            f"  [DONE] {case.case_number} | "
            f"Disposition: {judgment.disposition} | "
            f"Risk: {judgment.contempt_risk}"))
        return True

    def _cleanup_failed(self, judgment, case):
        """Remove DB records and physical PDF for a failed extraction."""
        if judgment.pdf_file:
            try:
                path = judgment.pdf_file.path
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
        judgment.delete()
        case.delete()

    def _load_pdfs(self, rag, path, gov_only=False):
        if not path or not os.path.isdir(path):
            self.stderr.write(f"Invalid path: {path}")
            return

        pdf_files = glob.glob(os.path.join(path, "*.pdf"))
        self.stdout.write(f"Found {len(pdf_files)} PDF files in {path}")

        for i, pdf_path in enumerate(pdf_files):
            self.stdout.write(
                f"\n  [{i+1}/{len(pdf_files)}] Processing {os.path.basename(pdf_path)}...")
            self._process_pdf_file(pdf_path, rag, gov_only)

    def _load_aws_s3(self, rag, prefix, count, min_size_kb, gov_only=False):
        try:
            import boto3
            from botocore import UNSIGNED
            from botocore.config import Config
        except ImportError:
            self.stderr.write("boto3 not installed. Run: pip install boto3")
            return

        import tempfile

        min_size_bytes = min_size_kb * 1024
        self.stdout.write(
            f"Fetching from AWS Open Data, prefix: '{prefix}'")
        self.stdout.write(
            f"  Filter: min PDF size = {min_size_kb}KB | count = {count}")

        s3 = boto3.client("s3", region_name="ap-south-1",
                         config=Config(signature_version=UNSIGNED))
        bucket = "indian-high-court-judgments"

        try:
            paginator = s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

            downloaded = 0
            scanned = 0
            skipped_small = 0

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    if downloaded >= count:
                        break

                    key = obj["Key"]
                    if not key.lower().endswith(".pdf"):
                        continue

                    scanned += 1
                    file_size = obj["Size"]
                    file_kb = file_size / 1024

                    # FILTER: Skip small PDFs (interim orders, bail orders, etc.)
                    if file_size < min_size_bytes:
                        skipped_small += 1
                        continue

                    downloaded += 1
                    self.stdout.write(
                        f"\n  [{downloaded}/{count}] Downloading {key.split('/')[-1]} "
                        f"({file_kb:.0f} KB)...")

                    tmp_path = None
                    try:
                        response = s3.get_object(Bucket=bucket, Key=key)
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".pdf"
                        ) as tmp:
                            tmp.write(response["Body"].read())
                            tmp_path = tmp.name

                        success = self._process_pdf_file(tmp_path, rag, gov_only)

                        # Clean up temp download
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                        # Sleep between successful extractions
                        if success and downloaded < count:
                            self.stdout.write(self.style.WARNING(
                                "  Sleeping 30s for NVIDIA rate limits..."))
                            time.sleep(30)

                    except Exception as e:
                        self.stderr.write(f"  FATAL: {key}: {e}")
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                if downloaded >= count:
                    break

            # Summary
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(
                f"=== COMPLETE ===\n"
                f"  Scanned:  {scanned} PDFs in S3\n"
                f"  Skipped:  {skipped_small} (under {min_size_kb}KB)\n"
                f"  Processed: {downloaded}"))

        except Exception as e:
            self.stderr.write(f"AWS S3 fetch failed: {e}")
