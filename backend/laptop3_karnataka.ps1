# ==============================================================================
# LAPTOP 3: Karnataka HC — All 3 Benches (Bengaluru + Dharwad + Kalaburagi)
# ==============================================================================
# Estimated: ~200 PDFs | ~4 hours
# After completion: python manage.py export_for_merge --output C:\export_laptop3
# ==============================================================================

$venv = ".\.venv\Scripts\python"
Write-Host "LAPTOP 3: Karnataka HC (all benches)" -ForegroundColor Cyan

# Karnataka Bengaluru 2024
Write-Host "`n[1/4] Karnataka Bengaluru 2024 — 100 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 100 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=29_3/bench=karnataka_bng_old/"
Start-Sleep -Seconds 60

# Karnataka Bengaluru 2023
Write-Host "`n[2/4] Karnataka Bengaluru 2023 — 50 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 50 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2023/court=29_3/bench=karnataka_bng_old/"
Start-Sleep -Seconds 60

# Karnataka Dharwad 2024
Write-Host "`n[3/4] Karnataka Dharwad 2024 — 30 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 30 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=29_3/bench=karhcdharwad/"
Start-Sleep -Seconds 60

# Karnataka Kalaburagi 2024
Write-Host "`n[4/4] Karnataka Kalaburagi 2024 — 20 PDFs" -ForegroundColor Green
& $venv manage.py populate_rag --count 20 --min-size 200 --gov-only `
    --prefix "data/pdf/year=2024/court=29_3/bench=karhckalaburagi/"

# Export
Write-Host "`n[EXPORT] Exporting for merge..." -ForegroundColor Yellow
& $venv manage.py export_for_merge --output ".\export_laptop3"
Write-Host "DONE! Copy the export_laptop3 folder to the master laptop." -ForegroundColor Cyan
