# Fixing bq CLI Error

## Problem
The `bq` command fails with:
```
AttributeError: module 'absl.flags' has no attribute 'FLAGS'
```

This is a Python package conflict between Google Cloud SDK's bundled packages and your system Python packages.

## Solution Options

### Option 1: Use Python BigQuery Library Directly (Recommended)
Since OpsYield uses the Python library, you can verify setup using Python:

```python
from google.cloud import bigquery

client = bigquery.Client(project='ecommerce-microservice-53')
datasets = list(client.list_datasets())
print("Datasets:", [d.dataset_id for d in datasets])

# Check billing_export dataset
dataset_ref = client.dataset('billing_export')
tables = list(client.list_tables(dataset_ref))
print("Tables in billing_export:", [t.table_id for t in tables])
```

### Option 2: Fix bq CLI (If you need it)
1. **Uninstall conflicting absl-py:**
   ```powershell
   pip uninstall absl-py -y
   ```

2. **Or use Google Cloud SDK's bundled Python:**
   The SDK has its own Python. Make sure you're using it:
   ```powershell
   # Check where bq is installed
   where.exe bq
   
   # The SDK's Python should be at:
   # C:\Users\Haxor\tools\gcp-sdk\google-cloud-sdk\platform\bundledpython\python.exe
   ```

3. **Reinstall absl-py in SDK's Python:**
   ```powershell
   C:\Users\Haxor\tools\gcp-sdk\google-cloud-sdk\platform\bundledpython\python.exe -m pip install absl-py
   ```

### Option 3: Use gcloud bq commands instead
```powershell
gcloud alpha bq datasets list --project=ecommerce-microservice-53
gcloud alpha bq tables list --dataset=billing_export --project=ecommerce-microservice-53
```

## Important Note
**This error does NOT affect OpsYield!** OpsYield uses `google-cloud-bigquery` Python library directly, not the `bq` CLI tool. Your setup is correct and OpsYield will work fine.
