"""
export_for_merge.py — Export local DB + PDFs into a portable folder for merging.

Usage:
  python manage.py export_for_merge --output C:\export_laptop1
  
This creates:
  C:\export_laptop1\
    cases.json       (Django fixture)
    judgments.json
    citations.json
    pdfs\             (copies of all judgment PDFs)
"""
import os
import shutil
import json
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from apps.cases.models import Case, Judgment, Citation


class Command(BaseCommand):
    help = "Export all cases, judgments, citations and PDFs into a portable folder for merging across laptops."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=str, required=True,
                          help="Output directory for the export bundle")

    def handle(self, *args, **options):
        out_dir = options["output"]
        os.makedirs(out_dir, exist_ok=True)
        pdf_dir = os.path.join(out_dir, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)

        # 1. Export Cases
        cases = Case.objects.all()
        data = serializers.serialize("json", cases, indent=2)
        with open(os.path.join(out_dir, "cases.json"), "w") as f:
            f.write(data)
        self.stdout.write(f"Exported {cases.count()} cases")

        # 2. Export Judgments
        judgments = Judgment.objects.all()
        data = serializers.serialize("json", judgments, indent=2)
        with open(os.path.join(out_dir, "judgments.json"), "w") as f:
            f.write(data)
        self.stdout.write(f"Exported {judgments.count()} judgments")

        # 3. Export Citations
        citations = Citation.objects.all()
        data = serializers.serialize("json", citations, indent=2)
        with open(os.path.join(out_dir, "citations.json"), "w") as f:
            f.write(data)
        self.stdout.write(f"Exported {citations.count()} citations")

        # 4. Copy PDFs
        copied = 0
        for j in judgments:
            if j.pdf_file:
                src = os.path.join(settings.MEDIA_ROOT, j.pdf_file.name)
                if os.path.exists(src):
                    dst = os.path.join(pdf_dir, os.path.basename(j.pdf_file.name))
                    shutil.copy2(src, dst)
                    copied += 1
        self.stdout.write(f"Copied {copied} PDF files")

        self.stdout.write(self.style.SUCCESS(
            f"\nExport complete -> {out_dir}\n"
            f"  Cases: {cases.count()}\n"
            f"  Judgments: {judgments.count()}\n"
            f"  Citations: {citations.count()}\n"
            f"  PDFs: {copied}"))
