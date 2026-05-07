# ==============================================================================
# LAPTOP 5: Bombay HC
# ==============================================================================
# Estimated: ~200 PDFs | ~4 hours
# After completion: python manage.py export_for_merge --output C:\export_laptop5
# ==============================================================================

$venv = ".\.venv\Scripts\python"
Write-Host "LAPTOP 5: Bombay HC" -ForegroundColor Cyan

# Bombay HC 2024
Write-Host "`n[1/2] Bombay HC 2024 — 120 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 120 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=1_12/"
Start-Sleep -Seconds 60

# Bombay HC 2023
Write-Host "`n[2/2] Bombay HC 2023 — 80 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 80 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2023/court=1_12/"

# Export
Write-Host "`n[EXPORT] Exporting for merge..." -ForegroundColor Yellow
& $venv manage.py export_for_merge --output ".\export_laptop5"
Write-Host "DONE! Copy the export_laptop5 folder to the master laptop." -ForegroundColor Cyan
