# OpsYield — Multi-Cloud FinOps Platform

OpsYield is a production-grade multi-cloud financial operations (FinOps) tool that provides unified cost analysis, anomaly detection, forecasting, and governance across **GCP**, **AWS**, and **Azure**.

## Quick Start

```bash
# Install
pip install -e .
pip install -r requirements.txt

# Start the backend + frontend
opsyield serve --port 8000
cd web-ui && npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

---

## GCP Automated Setup

OpsYield can automatically configure GCP billing export to BigQuery.

### One Command Setup

```bash
opsyield gcp setup --project-id <PROJECT_ID> --billing-account <BILLING_ACCOUNT_ID>
```

This will:
1. Authenticate via Application Default Credentials (ADC)
2. Create the `billing_export` BigQuery dataset if it doesn't exist
3. Verify billing is linked to the project
4. Check if export tables already exist
5. Print next steps if manual Console action is needed

### Required IAM Roles

| Role | Purpose |
|------|---------|
| `roles/billing.admin` | Configure billing export |
| `roles/bigquery.dataEditor` | Create datasets |
| `roles/bigquery.dataViewer` | Read billing export tables |
| `roles/bigquery.jobUser` | Execute BigQuery queries |

Grant roles:
```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="user:<YOUR_EMAIL>" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="user:<YOUR_EMAIL>" \
  --role="roles/bigquery.jobUser"
```

### Required APIs

```bash
gcloud services enable bigquery.googleapis.com --project=<PROJECT_ID>
gcloud services enable cloudbilling.googleapis.com --project=<PROJECT_ID>
```

### Authentication

OpsYield uses Google Application Default Credentials — no subprocess to `gcloud`:

```bash
# User credentials (development)
gcloud auth application-default login

# Service account (production)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Important Notes

> **Note:** Historical cost data is **NOT** backfilled. Data appears within 24 hours after enabling export.

> **Note:** Without billing export enabled, GCP cost analysis will return an error:
> `"Billing export not enabled. Please run: opsyield gcp setup"`

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Billing export not enabled` | BigQuery export not configured | Run `opsyield gcp setup` |
| `Permission denied` | Missing IAM roles | Grant `bigquery.dataViewer` + `bigquery.jobUser` |
| `NotFound: Dataset` | Dataset doesn't exist | Run `opsyield gcp setup` (auto-creates) |
| `google-cloud-bigquery not installed` | Missing dependency | `pip install google-cloud-bigquery` |
| Empty cost data | Export just enabled | Wait 24 hours for first data |
| `403` on billing API | Missing `billing.admin` | Grant `roles/billing.admin` |

---

## AWS Cost Analysis Setup

AWS cost retrieval uses the **Cost Explorer API** via `boto3`.

### Prerequisites

1. Authenticate via AWS CLI: `aws configure`
2. IAM permission: `ce:GetCostAndUsage`

---

## Azure Cost Analysis Setup

OpsYield uses the **Azure Cost Management API** to retrieve cost data. No manual export configuration is required, but permissions must be set correctly at the Subscription level.

### Prerequisites

1.  **Azure CLI** installed (`az`)
2.  **Owner** or **User Access Administrator** role (to assign permissions)
3.  Target Subscription ID

### 1. Interactive Setup (Local)

Run the following commands to authenticate and set up your environment.

```bash
# 1. Login to Azure
az login

# 2. List available subscriptions
az account list --output table

# 3. Set the target subscription
az account set --subscription <SUBSCRIPTION_ID>

# 4. Verify current context
az account show
```

### 2. Grant Permissions (RBAC)

OpsYield requires **Reader** level access to cost data. The permission must be assigned at the **Subscription** scope, not Resource Group.

**Recommended Roles:**
-   `Cost Management Reader` (Least Privilege)
-   `Reader` (Access to resources + costs)
-   `Contributor` (Full access)

**Assign Role via CLI:**

```bash
# Get your User Principal Name (Email) or Object ID
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Assign 'Cost Management Reader' role at Subscription scope
az role assignment create \
    --assignee $USER_ID \
    --role "Cost Management Reader" \
    --scope "/subscriptions/<SUBSCRIPTION_ID>"
```

### 3. Verify Access

Test connectivity by querying the Cost Management API directly:

```bash
az rest --method get --url "https://management.azure.com/subscriptions/<SUBSCRIPTION_ID>/providers/Microsoft.CostManagement/query?api-version=2019-11-01" --body '{"type":"Usage","timeframe":"TheLastMonth","dataset":{"granularity":"None","aggregation":{"totalCost":{"name":"PreTaxCost","function":"Sum"}}}}'
```

If this returns a JSON response with cost data, setup is complete.

### 4. Automated Setup (Service Principal)

For CI/CD or production environments, use a Service Principal.

```bash
# Create Service Principal with Reader access
az ad sp create-for-rbac --name "OpsYield-FinOps" --role "Cost Management Reader" --scopes "/subscriptions/<SUBSCRIPTION_ID>"
```

Output:
```json
{
  "appId": "...",
  "displayName": "OpsYield-FinOps",
  "password": "...",
  "tenant": "..."
}
```

**Environment Variables:**

Set these variables for OpsYield to authenticate automatically:

```bash
export AZURE_CLIENT_ID="<appId>"
export AZURE_CLIENT_SECRET="<password>"
export AZURE_TENANT_ID="<tenant>"
export AZURE_SUBSCRIPTION_ID="<SUBSCRIPTION_ID>"
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `AuthorizationFailed` | Role missing or wrong scope | Assign `Cost Management Reader` at **Subscription** level |
| `No subscriptions found` | Wrong Tenant | `az login --tenant <TENANT_ID>` |
| Empty Results | Billing Data Delay | Wait 8-24 hours for new subscriptions |
| `Reader` role not working | Role propagation delay | Wait 5-10 minutes after assignment |
| `InteractiveBrowserCredential` | CI/CD environment | Use Service Principal (env vars) |

### Important Notes

> **Note:** Azure cost data typically has a latency of **8–24 hours**. Real-time data is not supported by the standard Cost Management API.

> **Note:** The Cost Management API is enabled by default for EA, MCA, and MPA accounts. No export configuration is required.

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  React UI   │────▶│  FastAPI API  │────▶│  Orchestrator  │
│  (Vite)     │     │  /cloud/status│     │  analyze()     │
│             │     │  /analyze     │     │  aggregate()   │
└─────────────┘     └──────────────┘     └────────────────┘
                                                  │
                          ┌───────────────────────┼───────────────────────┐
                          ▼                       ▼                       ▼
                    ┌───────────┐          ┌───────────┐          ┌───────────┐
                    │    GCP    │          │    AWS    │          │   Azure   │
                    │ Provider  │          │ Provider  │          │ Provider  │
                    │ (BigQuery)│          │ (boto3)   │          │ (az CLI)  │
                    └───────────┘          └───────────┘          └───────────┘

opsyield/
├── automation/       # Cloud setup automation (gcp_setup.py)
├── providers/        # Cloud provider implementations
├── cli/              # CLI commands (argparse)
├── api/              # FastAPI endpoints
├── core/             # Orchestrator, models, snapshot
├── analytics/        # Cost analytics engine
└── web-ui/           # React + Vite frontend
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `opsyield analyze --provider gcp` | Analyze cloud costs |
| `opsyield serve --port 8000` | Start API server |
| `opsyield gcp setup` | Configure GCP billing export |
| `opsyield snapshot save <file>` | Save cost baseline |
| `opsyield diff <baseline>` | Compare against baseline |

## License

MIT
