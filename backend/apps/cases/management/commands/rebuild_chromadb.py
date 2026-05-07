"""
rebuild_chromadb.py — Rebuild ChromaDB from all Judgments in the database.

Usage:
  python manage.py rebuild_chromadb

Run this after merging data from multiple laptops. It will:
  1. Reset ChromaDB
  2. Re-index every Judgment in the database
"""
from django.core.management.base import BaseCommand
from apps.action_plans.services.rag_engine import HybridRAGEngine, reset_collection
from apps.cases.models import Case, Judgment


class Command(BaseCommand):
    help = "Rebuild ChromaDB from all Judgments in the database."

    def handle(self, *args, **options):
        self.stdout.write("Resetting ChromaDB...")
        reset_collection()
        rag = HybridRAGEngine()

        judgments = Judgment.objects.select_related("case").exclude(
            processing_status="failed"
        ).exclude(case__court_name__startswith="_temp_")

        total = judgments.count()
        self.stdout.write(f"Re-indexing {total} judgments into ChromaDB...")

        indexed = 0
        for i, judgment in enumerate(judgments, 1):
            case = judgment.case
            doc_text = f"{judgment.summary_of_facts}\n\n{judgment.ratio_decidendi}"
            
            if len(doc_text.strip()) < 10:
                self.stdout.write(self.style.WARNING(
                    f"  [{i}/{total}] SKIP {case.case_number[:40]} — no text to index"))
                continue

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
            indexed += 1

            if i % 50 == 0:
                self.stdout.write(f"  [{i}/{total}] indexed...")

        self.stdout.write(self.style.SUCCESS(
            f"\nChromaDB rebuild complete: {indexed}/{total} judgments indexed."))
