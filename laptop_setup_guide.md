# 5-Laptop Parallel Ingestion — Step-by-Step Guide

## Pre-Requisites

You need **5 different API key pairs**. Each laptop must have its own:
- `GROQ_API_KEY` (get from https://console.groq.com/keys — create 5 accounts if needed)
- `NVIDIA_API_KEY` (get from https://build.nvidia.com — create 5 accounts if needed)

---

## STEP 1: Setup on EVERY Laptop (Same for All 5)

Run these commands on **each** of the 5 laptops:

```powershell
# 1. Clone the repo (or copy the backend folder via USB/cloud)
git clone <your-repo-url>
cd Nyaya-Drishti\backend

# 2. Create virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 3. Create .env file with THIS laptop's unique API keys
# IMPORTANT: Each laptop MUST have DIFFERENT keys!
notepad .env
```

Paste this into `.env` (use the unique keys for THIS laptop):
```
NVIDIA_API_KEY=nvapi-XXXX_UNIQUE_FOR_THIS_LAPTOP
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
GROQ_API_KEY=gsk_XXXX_UNIQUE_FOR_THIS_LAPTOP
SECRET_KEY=your-django-secret-key
DEBUG=True
```

```powershell
# 4. Run migrations
.\.venv\Scripts\python manage.py migrate

# 5. Verify setup works (should show 0 cases)
.\.venv\Scripts\python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; import django; django.setup(); from apps.cases.models import Case; print(f'Cases: {Case.objects.count()}')"
```

---

## STEP 2: Run the Assigned Script on Each Laptop

### Laptop 1 — Supreme Court Primary (200 PDFs, ~4 hours)

```powershell
cd Nyaya-Drishti\backend

# Batch 1: SC newos 2022 — 80 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 80 --min-size 150 --gov-only --prefix "data/pdf/year=2022/court=27_1/bench=newos/"

# Batch 2: SC newos 2023 — 40 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 40 --min-size 150 --gov-only --prefix "data/pdf/year=2023/court=27_1/bench=newos/"

# Batch 3: SC newas 2023 — 50 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 50 --min-size 150 --gov-only --prefix "data/pdf/year=2023/court=27_1/bench=newas/"

# Batch 4: SC newas 2024 — 30 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 30 --min-size 150 --gov-only --prefix "data/pdf/year=2024/court=27_1/bench=newas/"
```

---

### Laptop 2 — Supreme Court Secondary (200 PDFs, ~4 hours)

```powershell
cd Nyaya-Drishti\backend

# Batch 1: SC hcaurdb 2022 — 80 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 80 --min-size 150 --gov-only --prefix "data/pdf/year=2022/court=27_1/bench=hcaurdb/"

# Batch 2: SC hcaurdb 2024 — 50 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 50 --min-size 150 --gov-only --prefix "data/pdf/year=2024/court=27_1/bench=hcaurdb/"

# Batch 3: SC hcbgoa 2023 — 40 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 40 --min-size 150 --gov-only --prefix "data/pdf/year=2023/court=27_1/bench=hcbgoa/"

# Batch 4: SC kolhcdb 2024 — 30 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 30 --min-size 150 --gov-only --prefix "data/pdf/year=2024/court=27_1/bench=kolhcdb/"
```

---

### Laptop 3 — Karnataka HC All Benches (200 PDFs, ~4 hours)

```powershell
cd Nyaya-Drishti\backend

# Batch 1: Karnataka Bengaluru 2024 — 100 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 100 --min-size 200 --gov-only --prefix "data/pdf/year=2024/court=29_3/bench=karnataka_bng_old/"

# Batch 2: Karnataka Bengaluru 2023 — 50 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 50 --min-size 200 --gov-only --prefix "data/pdf/year=2023/court=29_3/bench=karnataka_bng_old/"

# Batch 3: Karnataka Dharwad 2024 — 30 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 30 --min-size 200 --gov-only --prefix "data/pdf/year=2024/court=29_3/bench=karhcdharwad/"

# Batch 4: Karnataka Kalaburagi 2024 — 20 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 20 --min-size 200 --gov-only --prefix "data/pdf/year=2024/court=29_3/bench=karhckalaburagi/"
```

---

### Laptop 4 — Delhi HC (200 PDFs, ~4 hours)

```powershell
cd Nyaya-Drishti\backend

# Batch 1: Delhi HC 2024 — 120 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 120 --min-size 200 --gov-only --prefix "data/pdf/year=2024/court=7_26/"

# Batch 2: Delhi HC 2023 — 80 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 80 --min-size 200 --gov-only --prefix "data/pdf/year=2023/court=7_26/"
```

---

### Laptop 5 — Bombay HC (200 PDFs, ~4 hours)

```powershell
cd Nyaya-Drishti\backend

# Batch 1: Bombay HC 2024 — 120 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 120 --min-size 200 --gov-only --prefix "data/pdf/year=2024/court=1_12/"

# Batch 2: Bombay HC 2023 — 80 PDFs
.\.venv\Scripts\python manage.py populate_rag --count 80 --min-size 200 --gov-only --prefix "data/pdf/year=2023/court=1_12/"
```

---

## STEP 3: Export from Each Laptop (After Ingestion Finishes)

Run this on **each** laptop after all batches complete:

```powershell
cd Nyaya-Drishti\backend

# Export DB + PDFs to a portable folder
.\.venv\Scripts\python manage.py export_for_merge --output .\my_export

# Verify the export
dir .\my_export
dir .\my_export\pdfs | Measure-Object | Select-Object Count
```

This creates a folder with:
- `cases.json` — all Case records
- `judgments.json` — all Judgment records
- `citations.json` — all Citation records
- `pdfs\` — all the PDF files

> [!IMPORTANT]
> **Transfer this `my_export` folder** to the master laptop. Use USB, Google Drive, OneDrive, or any file transfer method. Rename the folder to `export_laptop1`, `export_laptop2`, etc. on the master.

---

## STEP 4: Merge on Master Laptop

On the **master laptop** (can be any of the 5, or your main machine):

```powershell
cd Nyaya-Drishti\backend

# 1. Reset the master DB (fresh start)
.\.venv\Scripts\python manage.py populate_rag --count 0 --full-reset

# 2. Import Laptop 1 data
.\.venv\Scripts\python manage.py import_merged_data --input .\export_laptop1

# 3. Import Laptop 2 data
.\.venv\Scripts\python manage.py import_merged_data --input .\export_laptop2

# 4. Import Laptop 3 data
.\.venv\Scripts\python manage.py import_merged_data --input .\export_laptop3

# 5. Import Laptop 4 data
.\.venv\Scripts\python manage.py import_merged_data --input .\export_laptop4

# 6. Import Laptop 5 data
.\.venv\Scripts\python manage.py import_merged_data --input .\export_laptop5

# 7. Rebuild ChromaDB from the merged database
.\.venv\Scripts\python manage.py rebuild_chromadb

# 8. Link ghost citations across courts
.\.venv\Scripts\python manage.py reconcile_citations

# 9. Verify final stats
.\.venv\Scripts\python -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; import django; django.setup(); from apps.cases.models import Case, Citation, Judgment; print(f'Cases: {Case.objects.count()}'); print(f'Judgments: {Judgment.objects.count()}'); print(f'Citations: {Citation.objects.count()}'); linked = Citation.objects.filter(cited_case__isnull=False).count(); print(f'Linked Citations: {linked}'); from collections import Counter; areas = Counter(Case.objects.values_list('area_of_law', flat=True)); [print(f'  {area}: {cnt}') for area, cnt in areas.most_common(15)]"
```

---

## Domain Variety Analysis

Since we're pulling government cases (`--gov-only`) from 5 different courts, the natural distribution will cover a wide variety of legal domains. Here's what to expect:

| Legal Domain | Expected Count | Which Courts |
|-------------|---------------|-------------|
| **Service Law** (govt employment, pension, gratuity, transfer) | ~200+ | All courts — govt is always a party |
| **Criminal Law** (NDPS, Goonda Act, detention, bail) | ~150+ | All courts |
| **Tax Law** (Income Tax, GST, excise) | ~100+ | Delhi, Bombay, SC |
| **Land & Property** (acquisition, eviction, tenancy) | ~100+ | Karnataka, Bombay, SC |
| **Motor Vehicles** (accident claims vs. govt vehicles) | ~80+ | Karnataka, Delhi |
| **Constitutional** (Article 14, 19, 21, 226 writ petitions) | ~80+ | SC (primary), all HCs |
| **Labour & Industrial** (factories, EPF, ESI) | ~50+ | Karnataka, Bombay, Delhi |
| **Environmental** (mining, pollution, forest) | ~30+ | SC, Karnataka |
| **Education** (university, admissions, reservations) | ~30+ | Karnataka, Delhi |
| **Municipal/Local Govt** (corporations, panchayat) | ~30+ | Karnataka |

> [!TIP]
> The `--gov-only` filter naturally ensures domain variety because government is a party in criminal cases (State vs. accused), service cases (Dept vs. employee), tax cases (Commissioner vs. assessee), land cases (Collector vs. owner), and constitutional cases (State vs. citizen). You will automatically get a rich spread!

### Why This Variety Matters for the Demo

When you upload a new case PDF during the demo:
- **Service Law case** → RAG finds 50+ similar pension/gratuity cases with win/loss patterns
- **Criminal case** → RAG finds detention/bail cases with SC precedents on Article 21/22
- **Tax case** → RAG finds similar assessment disputes from Delhi/Bombay HC + SC rulings
- **Land case** → RAG finds acquisition cases from Karnataka HC + SC landmark judgments

The cross-court citations (HC citing SC) will show the judges that your system understands the **hierarchy of precedent** — a Supreme Court ruling is more authoritative than a High Court one.

### Why SC-Heavy (400/1000 = 40%) is the Right Call

1. **Every HC case cites SC judgments** — having them in your DB means the reconciler can actually link them
2. **SC precedents are binding on all HCs** — so they're relevant regardless of which HC case you demo with
3. **SC cases cover constitutional law deeply** — Article 14, 19, 21, 226 writ petitions are the backbone of government litigation
4. **Demo impact**: "Our system found that the Supreme Court in *XYZ vs. Union of India (2023)* already ruled on this exact issue" is far more impressive than citing a random HC case
