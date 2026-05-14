"""Re-classify every existing Case using dept_classifier.

Use after seeding departments to assign dept tags to legacy cases that were
extracted before the classifier was wired in.

Usage:
    python manage.py backfill_departments
    python manage.py backfill_departments --only-untagged   # skip cases that already have a primary_department
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import Department
from apps.cases.models import Case
from apps.cases.services.dept_classifier import classify


class Command(BaseCommand):
    help = "Re-classify all existing Cases against the 48-dept taxonomy."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only-untagged",
            action="store_true",
            help="Skip cases that already have a primary_department set.",
        )

    def handle(self, *args, only_untagged=False, **options):
        qs = Case.objects.all()
        if only_untagged:
            qs = qs.filter(primary_department__isnull=True)

        total = qs.count()
        self.stdout.write(f"Backfilling departments for {total} case(s)...")

        hits = 0
        misses = 0
        for case in qs:
            judgment = case.judgments.first()
            operative = (judgment.operative_order_text if judgment else "") or ""
            facts = (judgment.summary_of_facts if judgment else "") or ""
            ratio = (judgment.ratio_decidendi if judgment else "") or ""
            entities: list = []
            if judgment and judgment.entities:
                ents = judgment.entities
                if isinstance(ents, list):
                    entities = list(ents)
                elif isinstance(ents, dict):
                    for v in ents.values():
                        if isinstance(v, list):
                            entities.extend(v)

            haystack = "\n".join([operative, ratio, facts])[:10000]
            result = classify(
                case_text=haystack,
                entities=entities,
                parties=(case.petitioner_name or "", case.respondent_name or ""),
            )

            if result.get("primary"):
                case.primary_department = Department.objects.filter(code=result["primary"]).first()
                case.save()
                case.secondary_departments.set(
                    Department.objects.filter(code__in=result.get("secondary", []))
                )
                hits += 1
                self.stdout.write(
                    f"  {case.case_number[:50]:50}  -> primary={result['primary']:18} "
                    f"secondary={result.get('secondary')} "
                    f"(conf={result.get('confidence')}, {result.get('method')})"
                )
            else:
                misses += 1
                self.stdout.write(
                    self.style.WARNING(f"  {case.case_number[:50]:50}  -> no dept matched")
                )

        self.stdout.write(self.style.SUCCESS(
            f"Backfill complete: {hits} tagged, {misses} unmatched."
        ))
