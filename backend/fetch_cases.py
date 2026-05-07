import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.cases.models import Case, Judgment

# Filter out the temp failed files by finding cases that don't start with tmp
cases = Case.objects.exclude(case_number__startswith='tmp')
out = []

for c in cases:
    # Get associated judgment
    j = c.judgments.first()
    if not j:
        continue
        
    out.append(f"## Case: {c.case_number}")
    out.append(f"**Court**: {c.court_name}")
    out.append(f"**Case Type**: {c.case_type}")
    out.append(f"**Petitioner**: {c.petitioner_name}")
    out.append(f"**Respondent**: {c.respondent_name}")
    out.append(f"**Disposition**: {j.disposition}")
    out.append(f"**Contempt Risk**: {j.contempt_risk}")
    
    out.append(f"\n### Summary of Facts\n{j.summary_of_facts}")
    
    out.append(f"\n### Issues Framed")
    if j.issues_framed:
        for i in j.issues_framed:
            out.append(f"- {i}")
    else:
        out.append("None")
        
    out.append(f"\n### Ratio Decidendi\n{j.ratio_decidendi}")
    
    out.append(f"\n### Directives")
    if j.court_directions:
        for d in j.court_directions:
            text = d.get('text', '')
            entity = d.get('responsible_entity', '')
            deadline = d.get('deadline_date_iso') or d.get('deadline_mentioned') or 'None'
            out.append(f"- **To {entity} (Deadline: {deadline})**:\n  > {text}")
    else:
        out.append("None")
        
    out.append("\n---\n")

output_path = r"C:\Users\HARSH MOHTA\.gemini\antigravity\brain\cf8fcdcb-5f1f-4c71-a1d5-9a37508fe65c\artifacts\extracted_cases.md"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    
print(f"Wrote {len(cases)} cases to {output_path}")
