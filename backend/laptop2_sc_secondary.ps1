# ==============================================================================
# LAPTOP 2: Supreme Court — Secondary Benches (hcaurdb + hcbgoa + kolhcdb)
# ==============================================================================
# Estimated: ~200 PDFs | ~4 hours
# After completion: python manage.py export_for_merge --output C:\export_laptop2
# ==============================================================================

$venv = ".\.venv\Scripts\python"
Write-Host "LAPTOP 2: Supreme Court (hcaurdb + hcbgoa + kolhcdb)" -ForegroundColor Cyan

# SC hcaurdb 2022 (988 > 150KB — huge!)
Write-Host "`n[1/4] SC hcaurdb 2022 — 80 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 80 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2022/court=27_1/bench=hcaurdb/"
Start-Sleep -Seconds 60

# SC hcaurdb 2024
Write-Host "`n[2/4] SC hcaurdb 2024 — 50 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 50 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2024/court=27_1/bench=hcaurdb/"
Start-Sleep -Seconds 60

# SC hcbgoa 2023
Write-Host "`n[3/4] SC hcbgoa 2023 — 40 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 40 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2023/court=27_1/bench=hcbgoa/"
Start-Sleep -Seconds 60

# SC kolhcdb 2024
Write-Host "`n[4/4] SC kolhcdb 2024 — 30 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 30 --min-size 150 --gov-only `
    --prefix "data/pdf/year=2024/court=27_1/bench=kolhcdb/"

# Export
Write-Host "`n[EXPORT] Exporting for merge..." -ForegroundColor Yellow
& $venv manage.py export_for_merge --output ".\export_laptop2"
Write-Host "DONE! Copy the export_laptop2 folder to the master laptop." -ForegroundColor Cyan
