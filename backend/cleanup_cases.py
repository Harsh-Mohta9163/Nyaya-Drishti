"""
Clean up duplicate/test cases from DB.
Keep only cases with PDFs that are fully extracted.
Delete test artifacts that have no PDF or are duplicates.
"""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.cases.models import Case, Judgment

cases = Case.objects.all().order_by('-created_at')
print(f"\nTotal cases before cleanup: {cases.count()}")

# Cases to keep: ones with PDFs that are complete or the latest uploading one
# Cases to delete: duplicates without PDFs, or test artifacts
to_delete = []
seen = {}  # track by case_number to detect duplicates

for c in cases:
    j = c.judgments.first()
    key = c.case_number or str(c.id)
    has_pdf = bool(j and j.pdf_file)
    
    if key in seen:
        # Duplicate — keep the one with PDF, delete the other
        if not has_pdf:
            to_delete.append(c)
            print(f"  DELETE (dup, no PDF): {c.id} | {c.case_number}")
        else:
            # This one has PDF but we already have one — delete the older one if it also has no directions
            existing = seen[key]
            existing_j = existing.judgments.first()
            existing_dirs = len(existing_j.court_directions) if existing_j and existing_j.court_directions else 0
            current_dirs = len(j.court_directions) if j and j.court_directions else 0
            
            if existing_dirs == 0 and current_dirs == 0:
                to_delete.append(c)
                print(f"  DELETE (dup): {c.id} | {c.case_number}")
            elif current_dirs > existing_dirs:
                # Current one is better, delete existing
                to_delete.append(existing)
                seen[key] = c
                print(f"  DELETE (dup, worse): {existing.id} | {existing.case_number}")
    else:
        seen[key] = c

print(f"\nWill delete {len(to_delete)} cases")
for c in to_delete:
    cid = c.id
    c.delete()
    print(f"  Deleted: {cid}")

remaining = Case.objects.count()
print(f"\nRemaining cases: {remaining}")
