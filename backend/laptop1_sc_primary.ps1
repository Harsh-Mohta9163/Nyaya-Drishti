# ==============================================================================
# LAPTOP 1: Supreme Court — Primary Bench (newos + newas)
# ==============================================================================
# Estimated: ~200 PDFs | ~4 hours
# After completion: python manage.py export_for_merge --output C:\export_laptop1
# ==============================================================================

$venv = ".\.venv\Scripts\python"
Write-Host "LAPTOP 1: Supreme Court (newos + newas)" -ForegroundColor Cyan

# SC newos 2022 (richest: 1161 > 150KB)
Write-Host "`n[1/4] SC newos 2022 — 80 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 80 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2022/court=27_1/bench=newos/"
Start-Sleep -Seconds 60

# SC newos 2023
Write-Host "`n[2/4] SC newos 2023 — 40 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 40 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2023/court=27_1/bench=newos/"
Start-Sleep -Seconds 60

# SC newas 2023 (appellate side — 417 > 150KB)
Write-Host "`n[3/4] SC newas 2023 — 50 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 50 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2023/court=27_1/bench=newas/"
Start-Sleep -Seconds 60

# SC newas 2024
Write-Host "`n[4/4] SC newas 2024 — 30 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 30 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2024/court=27_1/bench=newas/"

# Export for merging
Write-Host "`n[EXPORT] Exporting for merge..." -ForegroundColor Yellow
& $venv manage.py export_for_merge --output ".\export_laptop1"
Write-Host "DONE! Copy the export_laptop1 folder to the master laptop." -ForegroundColor Cyan
