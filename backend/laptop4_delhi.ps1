# ==============================================================================
# LAPTOP 4: Delhi HC
# ==============================================================================
# Estimated: ~200 PDFs | ~4 hours
# After completion: python manage.py export_for_merge --output C:\export_laptop4
# ==============================================================================

$venv = ".\.venv\Scripts\python"
Write-Host "LAPTOP 4: Delhi HC" -ForegroundColor Cyan

# Delhi HC 2024
Write-Host "`n[1/2] Delhi HC 2024 — 120 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 120 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=7_26/"
Start-Sleep -Seconds 60

# Delhi HC 2023
Write-Host "`n[2/2] Delhi HC 2023 — 80 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 80 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2023/court=7_26/"

# Export
Write-Host "`n[EXPORT] Exporting for merge..." -ForegroundColor Yellow
& $venv manage.py export_for_merge --output ".\export_laptop4"
Write-Host "DONE! Copy the export_laptop4 folder to the master laptop." -ForegroundColor Cyan
