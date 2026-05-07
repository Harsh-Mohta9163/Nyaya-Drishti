from django.core.management.base import BaseCommand
from apps.cases.models import Case, Citation, Judgment

class Command(BaseCommand):
    help = "Reconciles ghost citations by linking them to actual Case records if they exist in the DB."

    def handle(self, *args, **options):
        self.stdout.write("Starting Citation Reconciliation...")

        # 1. Reconcile Citations (Ghost Nodes)
        ghost_citations = Citation.objects.filter(cited_case__isnull=True)
        total_ghosts = ghost_citations.count()
        self.stdout.write(f"Found {total_ghosts} ghost citations to reconcile.")

        linked_count = 0
        for citation in ghost_citations:
            # We try to match by case number if it's extracted,
            # but currently we only have cited_case_name_raw and citation_id_raw.
            # A simple heuristic: check if citation_id_raw matches any case_number
            # OR if cited_case_name_raw matches petitioner vs respondent.
            # For a hackathon, we can do a naive string match on case_number if it looks like one,
            # or just match petitioner name.
            
            # Since High Court cases are often cited as "WA 541/2026", we can check if that string is in raw.
            # A better way is to do a reverse lookup: find all cases, and if a case's number is in the raw text.
            pass
            
        # Simplified: for the hackathon, we will just iterate over all cases and see if their case_number
        # appears in the cited_case_name_raw.
        all_cases = list(Case.objects.all())
        
        for citation in ghost_citations:
            raw_text = (citation.cited_case_name_raw + " " + citation.citation_id_raw).lower()
            best_match = None
            
            for c in all_cases:
                # E.g. "WP 123/2024"
                c_num = c.case_number.lower()
                if c_num and c_num in raw_text and len(c_num) > 4:
                    best_match = c
                    break
                    
            if best_match:
                citation.cited_case = best_match
                citation.save()
                linked_count += 1
                
                # If overruled, mark the cited case as overruled
                if citation.citation_context.lower() == "overruled":
                    for j in best_match.judgments.all():
                        j.precedent_status = "overruled"
                        j.save()
                        self.stdout.write(self.style.WARNING(f"  [!] Marked {best_match.case_number} as OVERRULED"))

        self.stdout.write(self.style.SUCCESS(f"Successfully linked {linked_count} ghost citations."))

        # 2. Build Appeal Chains
        # Find cases where is_appeal_from_lower_court is True (stored in raw_json)
        self.stdout.write("Building Appeal Chains...")
        judgments_with_appeals = Judgment.objects.exclude(raw_extracted_json={})
        appeal_links = 0
        
        for j in judgments_with_appeals:
            raw = j.raw_extracted_json
            if "registry" in raw:
                is_appeal = raw["registry"].get("is_appeal_from_lower_court", False)
                lc_num = raw["registry"].get("lower_court_case_number", "")
                
                if is_appeal and lc_num:
                    # Look for the lower court case
                    lc_case = Case.objects.filter(case_number__icontains=lc_num).first()
                    if lc_case and lc_case != j.case:
                        j.case.appealed_from_case = lc_case
                        j.case.save()
                        appeal_links += 1
                        
                        # If this appeal was allowed, the lower court is reversed
                        if j.disposition.lower() in ("allowed", "partly allowed"):
                            for lc_j in lc_case.judgments.all():
                                lc_j.precedent_status = "reversed"
                                lc_j.save()
                                self.stdout.write(self.style.WARNING(f"  [!] Marked {lc_case.case_number} as REVERSED by {j.case.case_number}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully built {appeal_links} appeal links."))
