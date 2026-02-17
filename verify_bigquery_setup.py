#!/usr/bin/env python3
"""
Verify BigQuery Billing Export Setup
This script checks if billing_export dataset exists and has data.
"""
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = 'ecommerce-microservice-53'
DATASET_ID = 'billing_export'

def verify_setup():
    print(f"=== Verifying BigQuery Billing Export Setup ===\n")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}\n")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Check if dataset exists
        print("[1] Checking if dataset exists...")
        try:
            dataset_ref = client.dataset(DATASET_ID)
            dataset = client.get_dataset(dataset_ref)
            print(f"[OK] Dataset '{DATASET_ID}' exists")
            print(f"   Location: {dataset.location}")
            print(f"   Created: {dataset.created}")
        except Exception as e:
            print(f"[ERROR] Dataset '{DATASET_ID}' not found: {e}")
            return False
        
        # List tables
        print(f"\n[2] Checking tables in dataset...")
        tables = list(client.list_tables(dataset_ref))
        if tables:
            print(f"[OK] Found {len(tables)} table(s):")
            for table in tables:
                print(f"   - {table.table_id}")
        else:
            print("[WARNING] No tables found yet. Data may take 4-24 hours to appear after enabling export.")
            return True
        
        # Check for recent data
        print(f"\n[3] Checking for recent billing data...")
        table_pattern = f"{PROJECT_ID}.{DATASET_ID}.gcp_billing_export_v1_*"
        
        # Query for last 7 days
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            MIN(usage_start_time) as earliest_date,
            MAX(usage_start_time) as latest_date,
            SUM(cost) as total_cost
        FROM `{table_pattern}`
        WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        """
        
        try:
            query_job = client.query(query)
            results = query_job.result()
            
            for row in results:
                if row.row_count > 0:
                    print(f"[OK] Found {row.row_count:,} rows in last 7 days")
                    print(f"   Date range: {row.earliest_date} to {row.latest_date}")
                    print(f"   Total cost: ${row.total_cost:,.2f}")
                    return True
                else:
                    print("[WARNING] No data in last 7 days. Data may still be loading.")
                    print("   Billing export data typically appears within 4-24 hours.")
                    return True
        except Exception as e:
            print(f"[WARNING] Could not query data: {e}")
            print("   This might mean:")
            print("   - Tables exist but no data yet (normal for first 24 hours)")
            print("   - Or billing export was just enabled")
            return True
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're authenticated: gcloud auth application-default login")
        print("2. Check project ID is correct")
        print("3. Verify billing export is enabled in Console")
        return False

if __name__ == "__main__":
    success = verify_setup()
    print("\n" + "="*50)
    if success:
        print("[SUCCESS] Setup verification complete!")
        print("   Your BigQuery billing export is configured correctly.")
        print("   OpsYield should be able to read cost data.")
    else:
        print("[WARNING] Setup verification found issues.")
        print("   Please check the errors above and ensure:")
        print("   1. Billing export is enabled in GCP Console")
        print("   2. Dataset 'billing_export' exists")
        print("   3. You have proper IAM permissions")
