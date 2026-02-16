# OpsYield — Multi-Cloud FinOps Platform

OpsYield is a production-grade multi-cloud financial operations (FinOps) tool that provides unified cost analysis, anomaly detection, forecasting, and governance across **GCP**, **AWS**, and **Azure**.

## Quick Start

```bash
# Install
pip install -e .

# Start the backend + frontend
python main.py serve --port 8000
cd web-ui && npm run dev
```

The frontend runs on `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

---

## GCP Cost Analysis Setup

GCP cost retrieval uses **BigQuery Billing Export** — the standard, production-grade method for accessing GCP billing data programmatically.

### Prerequisites

1. **Enable Billing Export to BigQuery**

   - Go to [GCP Console → Billing → Billing export](https://console.cloud.google.com/billing/export)
   - Select your billing account
   - Under **BigQuery export**, click **Edit settings**
   - Set the dataset to `billing_export` (or your preferred name)
   - Enable **Standard usage cost** export
   - Click **Save**

   > **Note:** Historical cost data will only appear after export is enabled. It may take up to 24 hours for the first data to arrive.

2. **Grant IAM Roles**

   The authenticated account (user or service account) needs these roles on the project:

   | Role | Purpose |
   |------|---------|
   | `roles/bigquery.dataViewer` | Read billing export tables |
   | `roles/bigquery.jobUser` | Execute BigQuery queries |

   ```bash
   gcloud projects add-iam-policy-binding <PROJECT_ID> \
     --member="user:<YOUR_EMAIL>" \
     --role="roles/bigquery.dataViewer"

   gcloud projects add-iam-policy-binding <PROJECT_ID> \
     --member="user:<YOUR_EMAIL>" \
     --role="roles/bigquery.jobUser"
   ```

3. **Install the BigQuery client library**

   ```bash
   pip install google-cloud-bigquery
   ```

4. **Authenticate**

   ```bash
   gcloud auth application-default login
   ```

### How It Works

OpsYield queries the billing export table:
```
<PROJECT_ID>.billing_export.gcp_billing_export_v1_*
```

It aggregates `SUM(cost)` grouped by `service.description` and `currency` for the requested time period, then returns results as `NormalizedCost` objects for the analytics engine.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Empty cost results | Billing export not enabled | Enable in GCP Console → Billing → Billing export |
| `NotFound` error | Dataset/table doesn't exist | Wait 24h after enabling export, or check dataset name |
| `Forbidden` error | Missing IAM roles | Grant `bigquery.dataViewer` + `bigquery.jobUser` |
| `google-cloud-bigquery not installed` | Missing dependency | Run `pip install google-cloud-bigquery` |

---

## AWS Cost Analysis Setup

AWS cost retrieval uses the **Cost Explorer API** via `boto3`.

### Prerequisites

1. Authenticate via AWS CLI: `aws configure`
2. IAM permission: `ce:GetCostAndUsage`

---

## Azure Cost Analysis Setup

Azure cost retrieval uses the **Cost Management API**.

### Prerequisites

1. Authenticate via Azure CLI: `az login`
2. IAM role: `Cost Management Reader` on the subscription

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
```

## License

MIT
