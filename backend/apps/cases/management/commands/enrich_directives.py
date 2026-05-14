"""Re-frame court directives from the government's perspective for existing cases.

Calls the directive_enricher on every Case (or a filtered subset). Idempotent
unless --force is passed.

Usage:
    python manage.py enrich_directives
    python manage.py enrich_directives --force
    python manage.py enrich_directives --case-number-prefix CRL.A
"""
import time
from django.core.management.base import BaseCommand

from apps.cases.models import Case
from apps.cases.services.directive_enricher import enrich_case_directives


class Command(BaseCommand):
    help = "Run the government-perspective directive enricher on existing cases."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true",
            help="Re-enrich even if directives already have actor_type tags.",
        )
        parser.add_argument(
            "--case-number-prefix", default="",
            help="Filter cases whose case_number startswith this prefix.",
        )
        parser.add_argument(
            "--sleep", type=int, default=6,
            help="Seconds to sleep between cases (NVIDIA NIM rate-limit friendly).",
        )

    def handle(self, *args, force, case_number_prefix, sleep, **options):
        qs = Case.objects.all().order_by("created_at")
        if case_number_prefix:
            qs = qs.filter(case_number__startswith=case_number_prefix)

        total = qs.count()
        self.stdout.write(f"Enriching directives for {total} case(s)...\n")

        ok = skipped = failed = 0
        for i, case in enumerate(qs, 1):
            label = case.case_number[:50]
            self.stdout.write(f"[{i}/{total}] {label}")
            try:
                result = enrich_case_directives(case, force=force)
                method = result.get("method", "")
                if method.startswith("llm"):
                    ok += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"  ok ({method}) — updated {result['updated']} directive(s)"
                    ))
                elif method == "skipped" and result.get("skipped"):
                    skipped += 1
                    self.stdout.write(self.style.WARNING(
                        f"  skip — already enriched (use --force to re-run)"
                    ))
                else:
                    skipped += 1
                    self.stdout.write(self.style.WARNING("  skip — no directives or LLM unavailable"))
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  fail — {type(e).__name__}: {e}"))

            if i < total and sleep:
                time.sleep(sleep)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {ok} enriched, {skipped} skipped, {failed} failed."
        ))
