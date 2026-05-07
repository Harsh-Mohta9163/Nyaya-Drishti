"""
import_merged_data.py — Import exported data from another laptop.

Usage:
  python manage.py import_merged_data --input C:\export_laptop2

Safely merges: skips any Case/Judgment/Citation that already exists (by UUID).
"""
import os
import shutil
import json
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.db import IntegrityError
from apps.cases.models import Case, Judgment, Citation


class Command(BaseCommand):
    help = "Import cases, judgments, citations and PDFs from an exported bundle."

    def add_arguments(self, parser):
        parser.add_argument("--input", type=str, required=True,
                          help="Path to the exported bundle directory")

    def handle(self, *args, **options):
        in_dir = options["input"]
        if not os.path.isdir(in_dir):
            self.stderr.write(f"Directory not found: {in_dir}")
            return

        # Track counts
        stats = {"cases": 0, "judgments": 0, "citations": 0, "pdfs": 0,
                 "skipped": 0}

        # 1. Import Cases (must be first — Judgments have FK to Case)
        cases_file = os.path.join(in_dir, "cases.json")
        if os.path.exists(cases_file):
            with open(cases_file, "r") as f:
                objects = serializers.deserialize("json", f.read())
                for obj in objects:
                    try:
                        # Check if this UUID already exists
                        if not Case.objects.filter(pk=obj.object.pk).exists():
                            obj.save()
                            stats["cases"] += 1
                        else:
                            stats["skipped"] += 1
                    except IntegrityError:
                        stats["skipped"] += 1
            self.stdout.write(f"Imported {stats['cases']} cases (skipped {stats['skipped']} duplicates)")

        # 2. Import Judgments
        skipped_j = 0
        judgments_file = os.path.join(in_dir, "judgments.json")
        if os.path.exists(judgments_file):
            with open(judgments_file, "r") as f:
                objects = serializers.deserialize("json", f.read())
                for obj in objects:
                    try:
                        if not Judgment.objects.filter(pk=obj.object.pk).exists():
                            obj.save()
                            stats["judgments"] += 1
                        else:
                            skipped_j += 1
                    except IntegrityError:
                        skipped_j += 1
            self.stdout.write(f"Imported {stats['judgments']} judgments (skipped {skipped_j} duplicates)")

        # 3. Import Citations
        skipped_c = 0
        citations_file = os.path.join(in_dir, "citations.json")
        if os.path.exists(citations_file):
            with open(citations_file, "r") as f:
                objects = serializers.deserialize("json", f.read())
                for obj in objects:
                    try:
                        if not Citation.objects.filter(pk=obj.object.pk).exists():
                            obj.save()
                            stats["citations"] += 1
                        else:
                            skipped_c += 1
                    except IntegrityError:
                        skipped_c += 1
            self.stdout.write(f"Imported {stats['citations']} citations (skipped {skipped_c} duplicates)")

        # 4. Copy PDFs
        pdf_dir = os.path.join(in_dir, "pdfs")
        if os.path.isdir(pdf_dir):
            media_judgments = os.path.join(settings.MEDIA_ROOT, "judgments")
            os.makedirs(media_judgments, exist_ok=True)
            for fname in os.listdir(pdf_dir):
                if fname.lower().endswith(".pdf"):
                    src = os.path.join(pdf_dir, fname)
                    dst = os.path.join(media_judgments, fname)
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        stats["pdfs"] += 1
            self.stdout.write(f"Copied {stats['pdfs']} new PDF files")

        self.stdout.write(self.style.SUCCESS(
            f"\nImport complete from {in_dir}\n"
            f"  New Cases: {stats['cases']}\n"
            f"  New Judgments: {stats['judgments']}\n"
            f"  New Citations: {stats['citations']}\n"
            f"  New PDFs: {stats['pdfs']}"))
        
        self.stdout.write(self.style.WARNING(
            "\nNEXT STEP: Run 'python manage.py rebuild_chromadb' to re-index everything into ChromaDB."))
