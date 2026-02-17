# Fix bq CLI Error - Run this script
# This fixes the absl-py dependency conflict

Write-Host "=== Fixing bq CLI Error ===" -ForegroundColor Cyan
Write-Host ""

# Find Google Cloud SDK installation
$gcpSdkPath = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk"
$altPath = "C:\Users\Haxor\tools\gcp-sdk\google-cloud-sdk"

if (Test-Path $altPath) {
    $sdkPath = $altPath
    Write-Host "[OK] Found SDK at: $sdkPath" -ForegroundColor Green
} elseif (Test-Path $gcpSdkPath) {
    $sdkPath = $gcpSdkPath
    Write-Host "[OK] Found SDK at: $sdkPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Could not find Google Cloud SDK" -ForegroundColor Red
    Write-Host "Please check your installation path" -ForegroundColor Yellow
    exit 1
}

$bundledPython = "$sdkPath\platform\bundledpython\python.exe"

if (-not (Test-Path $bundledPython)) {
    Write-Host "[ERROR] Bundled Python not found at: $bundledPython" -ForegroundColor Red
    Write-Host ""
    Write-Host "Trying alternative fix: Reinstalling absl-py in system Python..." -ForegroundColor Yellow
    
    # Option: Fix in system Python
    Write-Host "Step 1: Uninstalling conflicting absl-py..." -ForegroundColor Yellow
    python -m pip uninstall absl-py -y
    
    Write-Host "Step 2: Reinstalling absl-py..." -ForegroundColor Yellow
    python -m pip install absl-py --force-reinstall
    
    Write-Host ""
    Write-Host "[SUCCESS] Try running 'bq ls' again" -ForegroundColor Green
    exit 0
}

Write-Host "[OK] Found bundled Python at: $bundledPython" -ForegroundColor Green
Write-Host ""

# Check current absl-py version
Write-Host "Checking current absl-py installation..." -ForegroundColor Yellow
& $bundledPython -m pip show absl-py 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] absl-py not found in bundled Python, installing..." -ForegroundColor Yellow
} else {
    Write-Host "[INFO] absl-py found, reinstalling to fix conflicts..." -ForegroundColor Yellow
}

# Fix: Reinstall absl-py in bundled Python
Write-Host ""
Write-Host "Step 1: Uninstalling absl-py from bundled Python..." -ForegroundColor Yellow
& $bundledPython -m pip uninstall absl-py -y 2>&1 | Out-Null

Write-Host "Step 2: Installing compatible absl-py..." -ForegroundColor Yellow
& $bundledPython -m pip install absl-py --no-deps 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[SUCCESS] Fix applied!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Try running this command now:" -ForegroundColor Cyan
    Write-Host "  bq ls ecommerce-microservice-53:billing_export" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "[WARNING] Could not fix automatically" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative solutions:" -ForegroundColor Cyan
    Write-Host "1. Use Python script instead (recommended):" -ForegroundColor White
    Write-Host "   python verify_bigquery_setup.py" -ForegroundColor Green
    Write-Host ""
    Write-Host "2. Use gcloud commands instead:" -ForegroundColor White
    Write-Host "   gcloud alpha bq datasets list --project=ecommerce-microservice-53" -ForegroundColor Green
    Write-Host ""
    Write-Host "3. Reinstall Google Cloud SDK:" -ForegroundColor White
    Write-Host "   Download from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Green
}
