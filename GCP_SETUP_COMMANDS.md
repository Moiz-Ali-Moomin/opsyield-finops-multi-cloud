# GCP Setup Commands for OpsYield

## Prerequisites
- ✅ Python 3.13.6 installed
- ✅ OpsYield CLI installed
- ✅ Google Cloud Python libraries installed
- ⏳ Google Cloud SDK (gcloud) - **Installing now...**

## Step-by-Step Setup Commands

After Google Cloud SDK is installed, run these commands in order:

### 1. Authenticate with Google Cloud
```powershell
gcloud auth login
```
This will open a browser window for you to sign in with your Google account.

### 2. Get Your Billing Account ID
```powershell
gcloud beta billing accounts list
```
Copy the `ACCOUNT_ID` (format `XXXXXX-XXXXXX-XXXXXX`) for use in later steps.

### 3. Set Your GCP Project
```powershell
gcloud config set project YOUR_PROJECT_ID
```
Replace `YOUR_PROJECT_ID` with your actual GCP project ID.

### 4. Enable Required APIs
```powershell
gcloud services enable bigquery.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable cloudbilling.googleapis.com --project=YOUR_PROJECT_ID
```

### 5. Set Up Application Default Credentials
```powershell
gcloud auth application-default login
```
This allows Python libraries to authenticate automatically.

### 6. Run OpsYield Automated Setup
```powershell
opsyield gcp setup --project-id YOUR_PROJECT_ID --billing-account YOUR_BILLING_ACCOUNT_ID
```
Replace:
- `YOUR_PROJECT_ID` with your GCP project ID
- `YOUR_BILLING_ACCOUNT_ID` with your billing account (format: `01A2B3-C4D5E6-F7G8H9`)

Or without billing account (will verify existing setup):
```powershell
opsyield gcp setup --project-id YOUR_PROJECT_ID
```

### 7. Verify BigQuery Dataset
```powershell
bq ls YOUR_PROJECT_ID:billing_export
```

### 8. Verify Cost Data (Optional)
```powershell
bq query --use_legacy_sql=false "SELECT SUM(cost) as total_cost FROM `YOUR_PROJECT_ID.billing_export.gcp_billing_export_v1_*` WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)"
```

## Important: Enable Billing Export in Console

Even after running the automated setup, you **MUST** enable billing export in the GCP Console:

1. Go to: https://console.cloud.google.com/billing/export
2. Select your billing account
3. Under "BigQuery export", click "Edit settings"
4. Set project to your project ID
5. Set dataset to `billing_export`
6. Enable "Standard usage cost" export
7. Click "Save"

**Note:** Data typically appears within 4-24 hours after enabling export. Historical data is NOT backfilled.

## Quick Setup Script

After gcloud is installed, you can also run:
```powershell
.\setup_gcp.ps1
```

This script will guide you through all steps interactively.

## Troubleshooting

### If gcloud command not found after installation:
- Restart your terminal/PowerShell
- Or add gcloud to PATH manually:
  ```powershell
  $env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin"
  ```

### If authentication fails:
- Make sure you have the correct Google account with access to the GCP project
- Check IAM permissions: You need `roles/billing.admin`, `roles/bigquery.dataEditor`, `roles/bigquery.jobUser`

### If BigQuery dataset not found:
- Billing export must be enabled in Console (see step above)
- Wait 4-24 hours for first data to appear
