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
                title: '1. Authentication',
                items: [
                    { code: 'gcloud auth login' },
                    { code: 'gcloud auth list' },
                    {
                        note: 'Ensure the ACTIVE account has Billing Account permissions.'
                    }
                ]
            },

            {
                title: '2. Get Billing Account ID',
                items: [
                    {
                        code: 'gcloud beta billing accounts list'
                    },
                    {
                        note: 'Copy the "ACCOUNT_ID" (e.g., 012345-6789AB-CDEF01) for the next steps.'
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
                title: '4. Enable BigQuery Billing Export (MANDATORY)',
                items: [
                    {
                        text: 'Billing Export MUST be enabled before cost data can be queried.'
                    },
                    {
                        label: 'Option A: Automated Setup (Recommended)',
                        code: 'opsyield gcp setup --project-id YOUR_PROJECT_ID --billing-account BILLING_ACCOUNT_ID',
                        note: 'Creates dataset and verifies configuration.'
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
                        note: 'Historical data is NOT backfilled. Data appears in 4–24 hours.'
                    }
                ]
            },

            {
                title: '5. Verify Billing Link',
                items: [
                    {
                        code: 'gcloud beta billing projects describe YOUR_PROJECT_ID'
                    },
                    {
                        note: 'Must show billingEnabled: true'
                    }
                ]
            },

            {
                title: '5.1 Link Billing Account (If billingEnabled is false)',
                items: [
                    {
                        code: `gcloud beta billing projects link YOUR_PROJECT_ID \\
  --billing-account BILLING_ACCOUNT_ID`
                    },
                    {
                        code: 'gcloud beta billing projects describe YOUR_PROJECT_ID'
                    },
                    {
                        note: 'Billing MUST be linked or export will not work.'
                    }
                ]
            },

            {
                title: '6. Enable Required APIs',
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
                title: '7. Required IAM Roles',
                items: [
                    {
                        label: 'Billing Account',
                        list: [
                            'roles/billing.admin OR roles/billing.viewer'
                        ]
                    },
                    {
                        label: 'Project',
                        list: [
                            'roles/bigquery.dataViewer',
                            'roles/bigquery.jobUser'
                        ]
                    }
                ]
            },

            {
                title: '8. Application Default Credentials (ADC)',
                items: [
                    { code: 'gcloud auth application-default login' },
                    {
                        note: 'Required for OpsYield CLI and automation.'
                    }
                ]
            },

            {
                title: '9. Verification',
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
                        note: 'Numeric result confirms OpsYield readiness.'
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
            'OpsYield retrieves cost data using the AWS Cost Explorer API. Cost Explorer must be enabled and IAM permissions configured.',

        sections: [

            {
                title: '1. Enable Cost Explorer',
                items: [
                    {
                        list: [
                            'Login to AWS Console',
                            'Go to Cost Management > Cost Explorer',
                            'Click Enable'
                        ]
                    },
                    {
                        note: 'Activation takes up to 24 hours.'
                    }
                ]
            },

            {
                title: '2. Enable IAM Billing Access',
                items: [
                    {
                        list: [
                            'Go to Account Settings',
                            'Enable IAM Billing Access'
                        ]
                    }
                ]
            },

            {
                title: '3. Create IAM Policy',
                items: [
                    {
                        code: `{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetDimensionValues"
      ],
      "Resource": "*"
    }
  ]
}`
                    }
                ]
            },

            {
                title: '4. Configure CLI',
                items: [
                    { code: 'aws configure' },
                    { code: 'aws sts get-caller-identity' }
                ]
            },

            {
                title: '5. Set Default Region',
                items: [
                    {
                        code: 'aws configure set region us-east-1'
                    },
                    {
                        note: 'Cost Explorer works globally but requires a region set.'
                    }
                ]
            },

            {
                title: '6. Verification',
                items: [
                    {
                        code: `aws ce get-cost-and-usage \\
--time-period Start=2024-01-01,End=2024-02-01 \\
--granularity=MONTHLY \\
--metrics UnblendedCost`
                    },
                    {
                        note: 'Successful output confirms OpsYield readiness.'
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
            'OpsYield retrieves cost data using Azure Cost Management API. Subscription RBAC access is required.',

        sections: [

            {
                title: '1. Login',
                items: [
                    { code: 'az login' }
                ]
            },

            {
                title: '2. Select Subscription',
                items: [
                    { code: 'az account list --output table' },
                    { code: 'az account set --subscription YOUR_SUBSCRIPTION_ID' },
                    { code: 'az account show --output table' }
                ]
            },

            {
                title: '3. Assign Required Role',
                items: [
                    {
                        code: 'az ad signed-in-user show --query id -o tsv'
                    },
                    {
                        code: `az role assignment create \\
--assignee YOUR_USER_ID \\
--role "Cost Management Reader" \\
--scope "/subscriptions/YOUR_SUBSCRIPTION_ID"`
                    },
                    {
                        note: 'Role MUST be at Subscription scope.'
                    }
                ]
            },

            {
                title: '4. Verify Billing Access',
                items: [
                    {
                        code: `az rest --method post \\
--uri "https://management.azure.com/subscriptions/YOUR_SUBSCRIPTION_ID/providers/Microsoft.CostManagement/query?api-version=2023-03-01" \\
--body "{\\"type\\":\\"ActualCost\\",\\"timeframe\\":\\"MonthToDate\\",\\"dataset\\":{\\"granularity\\":\\"Daily\\"}}"`
                    },
                    {
                        note: 'Successful response confirms OpsYield readiness.'
                    }
                ]
            }
        ]
    }
};
