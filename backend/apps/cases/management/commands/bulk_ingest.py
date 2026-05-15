"""Sequentially ingest every PDF in a directory through the extract pipeline.

Avoids the 429 thundering-herd you'd get by hitting `/api/cases/extract/`
concurrently — runs synchronously with a configurable sleep between files.

Usage:
    python manage.py bulk_ingest --dir testcases/
    python manage.py bulk_ingest --dir testcases/ --sleep 5
    python manage.py bulk_ingest --dir testcases/ --skip-dedup
"""
import hashlib
import time
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError

from apps.cases.models import Case, Judgment


class Command(BaseCommand):
    help = "Ingest every PDF in --dir through the extraction pipeline, one at a time."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir", required=True,
            help="Folder containing PDFs. Walked non-recursively.",
        )
        parser.add_argument(
            "--sleep", type=int, default=8,
            help="Seconds to sleep between files (default 8) — keeps you under NVIDIA NIM rate limits.",
        )
        parser.add_argument(
            "--skip-dedup", action="store_true",
            help="Force re-extraction even if the hash already exists in DB.",
        )

    def handle(self, *args, dir, sleep, skip_dedup, **options):
        root = Path(dir).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise CommandError(f"--dir does not point at a directory: {root}")

        pdfs = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
        if not pdfs:
            raise CommandError(f"No .pdf files found in {root}")

        self.stdout.write(f"\nIngesting {len(pdfs)} PDF(s) from {root}")
        self.stdout.write(f"Sleep between files: {sleep}s   Skip dedup: {skip_dedup}\n")

        # Defer importing extraction services until we're sure we have work to
        # do — otherwise this command pays the model-warmup cost just to error out.
        from apps.cases.services.extractor import extract_structured_data
        from apps.cases.services.pdf_processor import extract_text_from_pdf
        from apps.cases.services.section_segmenter import segment_judgment
        from apps.cases.services.directive_enricher import enrich_case_directives
        from apps.cases.services.dept_classifier import classify as classify_dept
        from apps.accounts.models import Department
        import fitz
        from apps.cases.views import _annotate_source_locations

        ok, skipped, failed = 0, 0, 0
        for i, pdf_path in enumerate(pdfs, 1):
            label = pdf_path.name
            self.stdout.write(f"\n[{i}/{len(pdfs)}] {label}")

            # Hash before we touch the DB so we can short-circuit duplicates.
            with open(pdf_path, "rb") as fh:
                data = fh.read()
            pdf_hash = hashlib.sha256(data).hexdigest()

            if not skip_dedup:
                existing = Judgment.objects.filter(pdf_hash=pdf_hash).first()
                if existing:
                    self.stdout.write(self.style.WARNING(
                        f"  skip — already ingested as case {existing.case.case_number[:50]} "
                        f"(judgment id {existing.id})"
                    ))
                    skipped += 1
                    continue

            try:
                # Wrap bytes in a SimpleUploadedFile so Django's FileField is happy
                upload = SimpleUploadedFile(pdf_path.name, data, content_type="application/pdf")

                # Mirror what CaseExtractView does, minus the HTTP layer.
                import uuid
                temp_id = uuid.uuid4().hex[:8]
                case = Case.objects.create(
                    court_name=f"Pending Extraction {temp_id}",
                    case_type="Pending",
                    case_number=f"Pending {temp_id}",
                    case_year=0,
                    status=Case.Status.PENDING,
                )
                judgment = Judgment.objects.create(
                    case=case,
                    date_of_order="2000-01-01",
                    pdf_file=upload,
                    processing_status="parsing",
                    pdf_hash=pdf_hash,
                )

                pdf_full_path = judgment.pdf_file.path
                markdown_text = extract_text_from_pdf(pdf_full_path)
                try:
                    with fitz.open(pdf_full_path) as _doc:
                        page_count = _doc.page_count
                except Exception:
                    page_count = 0

                segments = segment_judgment(markdown_text)
                judgment.processing_status = "extracting"
                judgment.save()

                extract_structured_data(
                    judgment_id=str(judgment.id),
                    header_text=segments.get("header", ""),
                    middle_text=segments.get("middle", ""),
                    operative_text=segments.get("operative_order", ""),
                    page_count=page_count,
                )

                judgment.refresh_from_db()
                case = judgment.case

                # ── Source highlighting ──────────────────────────────────
                if judgment.court_directions:
                    judgment.court_directions = _annotate_source_locations(
                        pdf_full_path, judgment.court_directions
                    )
                    judgment.save()

                # ── Directive enrichment (missing in old bulk_ingest!) ───
                # Classifies each directive as govt-action vs informational
                # and generates implementation steps. Same as CaseExtractView.
                try:
                    enrich_result = enrich_case_directives(case)
                    self.stdout.write(
                        f"  enriched {enrich_result.get('updated', 0)} directives "
                        f"(method={enrich_result.get('method', '?')})"
                    )
                except Exception as enrich_err:
                    self.stdout.write(self.style.WARNING(
                        f"  directive enrichment failed (non-fatal): {enrich_err}"
                    ))

                # ── Department re-classification guard ───────────────────
                # extract_structured_data already runs dept classification,
                # but if it was rate-limited the case ends up with no dept.
                # Retry once here so bulk runs don't lose classification.
                case.refresh_from_db()
                if not case.primary_department:
                    self.stdout.write("  dept was <none> after extraction — retrying classification...")
                    try:
                        dept_haystack = (
                            (segments.get("operative_order", "") or "")[:6000]
                            + "\n"
                            + (segments.get("middle", "") or "")[:4000]
                        )
                        dept_result = classify_dept(
                            case_text=dept_haystack,
                            entities=list(judgment.entities or []),
                            parties=(case.petitioner_name or "", case.respondent_name or ""),
                        )
                        if dept_result.get("primary"):
                            case.primary_department = Department.objects.filter(
                                code=dept_result["primary"]
                            ).first()
                            case.save()
                            case.secondary_departments.set(
                                Department.objects.filter(
                                    code__in=dept_result.get("secondary", [])
                                )
                            )
                            self.stdout.write(self.style.SUCCESS(
                                f"  dept retry ok: primary={dept_result['primary']} "
                                f"method={dept_result.get('method')}"
                            ))
                        else:
                            self.stdout.write(self.style.WARNING(
                                "  dept retry: still no match"
                            ))
                    except Exception as dept_err:
                        self.stdout.write(self.style.WARNING(
                            f"  dept retry failed: {dept_err}"
                        ))

                if judgment.processing_status not in ("failed",):
                    judgment.processing_status = "complete"
                    judgment.save()

                primary = case.primary_department.code if case.primary_department else "<none>"
                self.stdout.write(self.style.SUCCESS(
                    f"  ok  — {case.case_number[:48]:50} -> dept={primary}"
                ))
                ok += 1

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.stdout.write(self.style.ERROR(f"  fail — {type(e).__name__}: {e}"))
                failed += 1

            if i < len(pdfs):
                self.stdout.write(f"  ...sleeping {sleep}s before next file")
                time.sleep(sleep)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done. {ok} extracted, {skipped} skipped (duplicate), {failed} failed."
        ))
