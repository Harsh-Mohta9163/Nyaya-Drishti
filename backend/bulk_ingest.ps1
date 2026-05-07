# ==============================================================================
# NyayaDrishti Overnight Bulk Ingestion Script
# ==============================================================================
# Run this script and leave it overnight. It will:
#   1. Reset the database and ChromaDB (fresh start)
#   2. Ingest 700 government judgments from 6 court sources
#   3. Run citation reconciliation at the end
#
# Estimated time: ~14-15 hours
# Usage: .\bulk_ingest.ps1
# ==============================================================================

$ErrorActionPreference = "Continue"
$venv = ".\.venv\Scripts\python"
$startTime = Get-Date

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  NyayaDrishti Bulk Ingestion — Starting"      -ForegroundColor Cyan
Write-Host "  Start Time: $startTime"                       -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# --- STEP 0: Full Reset ---
Write-Host "`n[STEP 0] Full database + ChromaDB reset..." -ForegroundColor Yellow
& $venv manage.py populate_rag --count 0 --full-reset

# --- BATCH 1: Karnataka HC Bengaluru (300 PDFs) ---
Write-Host "`n[BATCH 1/6] Karnataka HC Bengaluru — 300 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 300 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=29_3/bench=karnataka_bng_old/"
Write-Host "  Batch 1 complete. Cooling down 60s..." -ForegroundColor DarkGray
Start-Sleep -Seconds 60

# --- BATCH 2: Karnataka HC Dharwad (50 PDFs) ---
Write-Host "`n[BATCH 2/6] Karnataka HC Dharwad — 50 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 50 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=29_3/bench=karhcdharwad/"
Write-Host "  Batch 2 complete. Cooling down 60s..." -ForegroundColor DarkGray
Start-Sleep -Seconds 60

# --- BATCH 3: Karnataka HC Kalaburagi (50 PDFs) ---
Write-Host "`n[BATCH 3/6] Karnataka HC Kalaburagi — 50 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 50 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=29_3/bench=karhckalaburagi/"
Write-Host "  Batch 3 complete. Cooling down 60s..." -ForegroundColor DarkGray
Start-Sleep -Seconds 60

# --- BATCH 4: Delhi HC (100 PDFs) ---
Write-Host "`n[BATCH 4/6] Delhi HC — 100 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 100 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=7_26/"
Write-Host "  Batch 4 complete. Cooling down 60s..." -ForegroundColor DarkGray
Start-Sleep -Seconds 60

# --- BATCH 5: Bombay HC (100 PDFs) ---
Write-Host "`n[BATCH 5/6] Bombay HC — 100 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 100 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=1_12/"
Write-Host "  Batch 5 complete. Cooling down 60s..." -ForegroundColor DarkGray
Start-Sleep -Seconds 60

# --- BATCH 6: Supreme Court (100 PDFs) — NO gov-only filter ---
Write-Host "`n[BATCH 6/6] Supreme Court — 100 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 100 --min-size 200 `
    --prefix "data/pdf/year=2024/court=27_1/bench=newos/"
Write-Host "  Batch 6 complete." -ForegroundColor DarkGray

# --- STEP 7: Citation Reconciliation ---
Write-Host "`n[STEP 7] Running Citation Reconciler..." -ForegroundColor Yellow
& $venv manage.py reconcile_citations

# --- SUMMARY ---
$endTime = Get-Date
$duration = $endTime - $startTime
Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "  BULK INGESTION COMPLETE"                       -ForegroundColor Cyan
Write-Host "  Start: $startTime"                             -ForegroundColor Cyan
Write-Host "  End:   $endTime"                               -ForegroundColor Cyan
Write-Host "  Duration: $($duration.TotalHours.ToString('F1')) hours" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Final stats
& $venv -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; import django; django.setup(); from apps.cases.models import Case, Citation, Judgment; print(f'  Cases: {Case.objects.count()}'); print(f'  Judgments: {Judgment.objects.count()}'); print(f'  Citations: {Citation.objects.count()}'); linked = Citation.objects.filter(cited_case__isnull=False).count(); print(f'  Linked citations: {linked}')"
