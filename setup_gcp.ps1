# GCP Setup Script for OpsYield
# This script will guide you through GCP setup

Write-Host "=== OpsYield GCP Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if gcloud is installed
Write-Host "[1/7] Checking Google Cloud SDK installation..." -ForegroundColor Yellow
$gcloudInstalled = Get-Command gcloud -ErrorAction SilentlyContinue

if (-not $gcloudInstalled) {
    Write-Host "❌ Google Cloud SDK (gcloud) is not installed." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host "Or run this command:" -ForegroundColor Yellow
    Write-Host "  (New-Object Net.WebClient).DownloadFile('https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe', '$env:TEMP\GoogleCloudSDKInstaller.exe'); Start-Process '$env:TEMP\GoogleCloudSDKInstaller.exe'" -ForegroundColor Green
    Write-Host ""
    Write-Host "After installation, restart your terminal and run this script again." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ Google Cloud SDK is installed" -ForegroundColor Green
    gcloud --version
}

Write-Host ""
Write-Host "[2/7] Checking authentication..." -ForegroundColor Yellow
$authResult = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($authResult)) {
    Write-Host "❌ Not authenticated. Please login:" -ForegroundColor Red
    Write-Host "  gcloud auth login" -ForegroundColor Green
    Write-Host ""
    Write-Host "Running authentication now..." -ForegroundColor Yellow
    gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Authentication failed. Please run 'gcloud auth login' manually." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Authenticated as: $authResult" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/7] Checking current project..." -ForegroundColor Yellow
$currentProject = gcloud config get-value project 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($currentProject)) {
    Write-Host "⚠️  No project set. You'll need to set one:" -ForegroundColor Yellow
    Write-Host "  gcloud config set project YOUR_PROJECT_ID" -ForegroundColor Green
    Write-Host ""
    $projectId = Read-Host "Enter your GCP Project ID"
    if (-not [string]::IsNullOrWhiteSpace($projectId)) {
        gcloud config set project $projectId
        Write-Host "✅ Project set to: $projectId" -ForegroundColor Green
    } else {
        Write-Host "❌ Project ID is required. Exiting." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Current project: $currentProject" -ForegroundColor Green
    $projectId = $currentProject
}

Write-Host ""
Write-Host "[4/7] Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable bigquery.googleapis.com --project=$projectId
gcloud services enable cloudbilling.googleapis.com --project=$projectId
Write-Host "✅ APIs enabled" -ForegroundColor Green

Write-Host ""
Write-Host "[5/7] Setting up Application Default Credentials..." -ForegroundColor Yellow
gcloud auth application-default login
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  ADC setup may have failed. Continuing anyway..." -ForegroundColor Yellow
} else {
    Write-Host "✅ Application Default Credentials configured" -ForegroundColor Green
}

Write-Host ""
Write-Host "[6/7] Running OpsYield automated setup..." -ForegroundColor Yellow
Write-Host "Note: You may need to provide billing account ID" -ForegroundColor Yellow
Write-Host ""

$billingAccount = Read-Host "Enter your Billing Account ID (e.g., 01A2B3-C4D5E6-F7G8H9) or press Enter to skip"

if ([string]::IsNullOrWhiteSpace($billingAccount)) {
    Write-Host "Running setup without billing account (will verify existing setup)..." -ForegroundColor Yellow
    opsyield gcp setup --project-id $projectId
} else {
    Write-Host "Running setup with billing account..." -ForegroundColor Yellow
    opsyield gcp setup --project-id $projectId --billing-account $billingAccount
}

Write-Host ""
Write-Host "[7/7] Verification..." -ForegroundColor Yellow
Write-Host "Checking BigQuery dataset..." -ForegroundColor Yellow
$bqCheck = bq ls $projectId`:billing_export 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ BigQuery dataset 'billing_export' exists" -ForegroundColor Green
} else {
    Write-Host "⚠️  BigQuery dataset 'billing_export' not found" -ForegroundColor Yellow
    Write-Host "   You may need to enable Billing Export in Console:" -ForegroundColor Yellow
    Write-Host "   https://console.cloud.google.com/billing/export" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If billing export is not enabled, go to:" -ForegroundColor White
Write-Host "   https://console.cloud.google.com/billing/export" -ForegroundColor Cyan
Write-Host "2. Select 'Standard usage cost export'" -ForegroundColor White
Write-Host "3. Choose project: $projectId" -ForegroundColor White
Write-Host "4. Create/select dataset: billing_export" -ForegroundColor White
Write-Host "5. Click Save" -ForegroundColor White
Write-Host ""
Write-Host "After enabling export, data may take 4-24 hours to appear." -ForegroundColor Yellow
