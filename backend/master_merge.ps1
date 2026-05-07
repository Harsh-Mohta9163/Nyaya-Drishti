# ==============================================================================
# MASTER LAPTOP: Merge all 5 laptop exports + rebuild ChromaDB + reconcile
# ==============================================================================
# Prerequisites:
#   1. Copy export_laptop1 through export_laptop5 folders into this backend dir
#   2. Run this script
# ==============================================================================

$venv = ".\.venv\Scripts\python"
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  MASTER MERGE — Combining all 5 laptops"     -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Step 0: Full reset (clean slate on master)
Write-Host "`n[STEP 0] Full reset..." -ForegroundColor Yellow
& $venv manage.py populate_rag --count 0 --full-reset

# Step 1: Import each laptop's data
for ($i = 1; $i -le 5; $i++) {
    $dir = ".\export_laptop$i"
    if (Test-Path $dir) {
        Write-Host "`n[STEP 1.$i] Importing from laptop $i..." -ForegroundColor Green
        & $venv manage.py import_merged_data --input $dir
    } else {
        Write-Host "`n[STEP 1.$i] SKIP — $dir not found" -ForegroundColor DarkGray
    }
}

# Step 2: Rebuild ChromaDB from merged DB
Write-Host "`n[STEP 2] Rebuilding ChromaDB from merged database..." -ForegroundColor Yellow
& $venv manage.py rebuild_chromadb

# Step 3: Reconcile citations across all courts
Write-Host "`n[STEP 3] Running citation reconciliation..." -ForegroundColor Yellow
& $venv manage.py reconcile_citations

# Step 4: Final stats
Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "  MERGE COMPLETE — Final Statistics"            -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
& $venv -c "import os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; import django; django.setup(); from apps.cases.models import Case, Citation, Judgment; print(f'  Total Cases: {Case.objects.count()}'); print(f'  Total Judgments: {Judgment.objects.count()}'); print(f'  Total Citations: {Citation.objects.count()}'); linked = Citation.objects.filter(cited_case__isnull=False).count(); print(f'  Linked Citations: {linked}'); courts = Case.objects.values_list('court_name', flat=True).distinct(); print(f'  Courts: {list(courts)}')"
