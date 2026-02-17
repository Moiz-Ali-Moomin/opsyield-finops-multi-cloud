export interface InstructionSection {
    title: string;
    content?: string[];
    items: {
        label?: string;
        text?: string;
        code?: string;
        note?: string;
        list?: string[];
    }[];
}

export interface CloudInstruction {
    title: string;
    overview: string;
    sections: InstructionSection[];
}

export const CLOUD_INSTRUCTIONS: Record<'gcp' | 'aws' | 'azure', CloudInstruction> = {

    /* =========================
       GCP
    ========================== */

    gcp: {
        title: 'Google Cloud Platform (GCP)',
        overview:
            'GCP does NOT expose granular cost data via a direct API. You MUST enable BigQuery Billing Export FIRST. OpsYield reads cost data directly from the exported BigQuery dataset. The project must be linked to an active billing account.',

        sections: [

            {
                title: '1. Enable BigQuery Billing Export (MANDATORY)',
                items: [
                    {
                        text: 'Billing Export MUST be enabled before cost data can be queried. You can use automated setup or manual Console setup.'
                    },
                    {
                        label: 'Option A: Automated Setup (Recommended)',
                        code: 'opsyield gcp setup --project-id YOUR_PROJECT_ID --billing-account BILLING_ACCOUNT_ID',
                        note: 'This command will create the BigQuery dataset and verify billing configuration. You may still need to enable export in Console if not already done.'
                    },
                    {
                        label: 'Option B: Manual Console Setup',
                        list: [
                            'Go to GCP Console > Billing > Billing Export',
                            'Select "Standard usage cost export"',
                            'Select YOUR_PROJECT_ID',
                            'Create/select dataset named "billing_export"',
                            'Choose Multi-region (US recommended)',
                            'Click Save'
                        ]
                    },
                    {
                        note: 'Historical data is NOT backfilled. First data may take 4–24 hours to appear after enabling export.'
                    }
                ]
            },

            {
                title: '2. Authentication',
                items: [
                    { code: 'gcloud auth login' },
                    { code: 'gcloud auth list' },
                    {
                        note: 'Ensure the ACTIVE account has Billing Account permissions.'
                    }
                ]
            },

            {
                title: '3. Select Project',
                items: [
                    { code: 'gcloud config set project YOUR_PROJECT_ID' },
                    { code: 'gcloud config get-value project' }
                ]
            },

            {
                title: '4. Verify Billing Link',
                items: [
                    {
                        code: 'gcloud beta billing projects describe YOUR_PROJECT_ID'
                    },
                    {
                        note: 'Output must show "billingEnabled": true and a valid "billingAccountName".'
                    }
                ]
            },

            {
                title: '5. Enable Required APIs',
                items: [
                    {
                        code: 'gcloud services enable bigquery.googleapis.com cloudbilling.googleapis.com --project=YOUR_PROJECT_ID'
                    },
                    {
                        code: 'gcloud services list --enabled --project=YOUR_PROJECT_ID'
                    }
                ]
            },

            {
                title: '6. Required IAM Roles',
                items: [
                    {
                        label: 'Billing Account Scope',
                        list: ['roles/billing.admin']
                    },
                    {
                        label: 'Project Scope',
                        list: ['roles/bigquery.dataViewer', 'roles/bigquery.jobUser']
                    }
                ]
            },

            {
                title: '7. Application Default Credentials (ADC)',
                items: [
                    { code: 'gcloud auth application-default login' },
                    {
                        note: 'For CI/CD, use a Service Account and set GOOGLE_APPLICATION_CREDENTIALS.'
                    }
                ]
            },

            {
                title: '8. Verification',
                items: [
                    { code: 'bq ls YOUR_PROJECT_ID' },
                    { code: 'bq ls YOUR_PROJECT_ID:billing_export' },
                    {
                        code: `bq query --use_legacy_sql=false "
SELECT SUM(cost) as total_cost
FROM \`YOUR_PROJECT_ID.billing_export.gcp_billing_export_v1_*\`
WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
"`
                    },
                    {
                        note: 'If this returns a numeric value (including 0.0), configuration is correct.'
                    }
                ]
            }
        ]
    },

    /* =========================
       AWS
    ========================== */

    aws: {
        title: 'Amazon Web Services (AWS)',
        overview:
            'AWS cost data is retrieved using the Cost Explorer API. Cost Explorer must be enabled in the AWS Console before API access works. For Organizations, this must be done in the Management Account.',

        sections: [

            {
                title: '1. Enable Cost Explorer (Console Required)',
                items: [
                    {
                        list: [
                            'Login to AWS Console (Management Account if using Organizations).',
                            'Go to AWS Cost Management > Cost Explorer.',
                            'Click "Enable Cost Explorer".'
                        ]
                    },
                    {
                        note: 'Activation can take up to 24 hours.'
                    }
                ]
            },

            {
                title: '2. Enable IAM Billing Access',
                items: [
                    {
                        list: [
                            'Go to Account Settings.',
                            'Enable "IAM User and Role Access to Billing Information".'
                        ]
                    }
                ]
            },

            {
                title: '3. Required IAM Permissions',
                items: [
                    {
                        code: `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetDimensionValues",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}`
                    }
                ]
            },

            {
                title: '4. CLI Setup',
                items: [
                    { code: 'aws configure' },
                    { code: 'aws sts get-caller-identity' },
                    { code: 'aws configure set region us-east-1' }
                ]
            },

            {
                title: '5. Verification',
                items: [
                    {
                        code: `aws ce get-cost-and-usage \\
  --time-period Start=YYYY-MM-DD,End=YYYY-MM-DD \\
  --granularity=MONTHLY \\
  --metrics UnblendedCost`
                    },
                    {
                        note: 'Use a valid past date range. OpsYield uses UnblendedCost metric for consistency.'
                    }
                ]
            }
        ]
    },

    /* =========================
       AZURE
    ========================== */

    azure: {
        title: 'Microsoft Azure',
        overview:
            'Azure cost data is retrieved via the Cost Management API. No export is required. RBAC must be assigned at Subscription scope.',

        sections: [

            {
                title: '1. Verify Subscription',
                items: [
                    {
                        list: [
                            'Go to Azure Portal > Cost Management + Billing.',
                            'Ensure Subscription is active.',
                            'Ensure Subscription is linked to a Billing Account.'
                        ]
                    }
                ]
            },

            {
                title: '2. Required RBAC Role',
                items: [
                    {
                        list: [
                            'Cost Management Reader (Recommended)',
                            'Reader',
                            'Contributor'
                        ]
                    },
                    {
                        note: 'Role MUST be assigned at Subscription scope.'
                    }
                ]
            },

            {
                title: '3. CLI Setup',
                items: [
                    { code: 'az login' },
                    { code: 'az account list --output table' },
                    { code: 'az account set --subscription YOUR_SUBSCRIPTION_ID' },
                    { code: 'az account show --output table' }
                ]
            },

            {
                title: '4. Assign Role',
                items: [
                    { code: 'az ad signed-in-user show --query id -o tsv' },
                    {
                        code: `az role assignment create \\
  --assignee YOUR_USER_ID \\
  --role "Cost Management Reader" \\
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID"`
                    }
                ]
            },

            {
                title: '5. Verification',
                items: [
                    {
                        code: `az rest --method post \\
  --uri "https://management.azure.com/subscriptions/YOUR_SUBSCRIPTION_ID/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \\
  --body "{\\"type\\":\\"ActualCost\\",\\"timeframe\\":\\"MonthToDate\\",\\"dataset\\":{\\"granularity\\":\\"Daily\\"}}"`
                    },
                    {
                        note: 'Successful response contains properties.rows with numeric cost values.'
                    }
                ]
            }
        ]
    }
};
