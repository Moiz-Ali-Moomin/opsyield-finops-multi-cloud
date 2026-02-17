
import { useOpsStore } from '@/store/useOpsStore';

export const SETUP_STEPS: Record<string, { title: string; steps: { label: string; command: string; note?: string }[] }> = {
    gcp: {
        title: 'Setup GCP Connectivity',
        steps: [
            { 
                label: 'Enable BigQuery Billing Export (MANDATORY)', 
                command: 'https://console.cloud.google.com/billing/export',
                note: 'Go to GCP Console > Billing > Billing Export. Select "Standard usage cost export", choose your project, create/select dataset "billing_export", and click Save. This MUST be done first - OpsYield reads cost data from BigQuery, not a direct API. Alternatively, use automated setup: opsyield gcp setup --project-id YOUR_PROJECT_ID --billing-account BILLING_ACCOUNT_ID'
            },
            { label: 'Install Google Cloud CLI', command: 'https://cloud.google.com/sdk/docs/install' },
            { label: 'Login & Authenticate', command: 'gcloud auth login' },
            { label: 'Set Active Project', command: 'gcloud config set project YOUR_PROJECT_ID' },
            { label: 'Enable Required APIs', command: 'gcloud services enable bigquery.googleapis.com cloudbilling.googleapis.com --project=YOUR_PROJECT_ID' },
            { label: 'Set Application Default Credentials', command: 'gcloud auth application-default login', note: 'Required for Python libraries to access BigQuery.' },
            { label: 'Verify BigQuery Dataset Exists', command: 'bq ls YOUR_PROJECT_ID:billing_export', note: 'Should show the billing_export dataset. If not found, billing export was not enabled in Console.' },
            { label: 'Verify Cost Data (BigQuery)', command: 'bq query --use_legacy_sql=false "SELECT SUM(cost) as total_cost FROM `YOUR_PROJECT_ID.billing_export.gcp_billing_export_v1_*` WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)"', note: 'If table not found: Billing Export not enabled. First data may take 4-24 hours to appear after enabling export.' },
        ],
    },
    aws: {
        title: 'Setup AWS Connectivity',
        steps: [
            { label: 'Enable Cost Explorer (MANDATORY - Console Required)', command: 'https://console.aws.amazon.com/cost-management/home#/cost-explorer', note: 'Cost Explorer MUST be enabled in AWS Console before API access works. For Organizations, enable in Management Account. Activation can take up to 24 hours.' },
            { label: 'Enable IAM Billing Access', command: 'https://console.aws.amazon.com/billing/home#/account', note: 'Go to Account Settings > Enable "IAM User and Role Access to Billing Information".' },
            { label: 'Install AWS CLI', command: 'https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html' },
            { label: 'Configure Credentials', command: 'aws configure' },
            { label: 'Verify Identity', command: 'aws sts get-caller-identity' },
            {
                label: 'Verify Cost Data (AWS CLI)',
                command: 'aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity=MONTHLY --metrics UnblendedCost',
                note: 'If AccessDeniedException: Cost Explorer not enabled or missing permissions. Required IAM permissions: ce:GetCostAndUsage, ce:GetDimensionValues, ce:GetCostForecast. Note: OpsYield uses UnblendedCost metric.'
            },
        ],
    },
    azure: {
        title: 'Setup Azure Connectivity',
        steps: [
            { label: 'Verify Subscription & Billing', command: 'https://portal.azure.com/#view/Microsoft_Azure_Billing/SubscriptionsBlade', note: 'Ensure subscription is active and linked to a billing account. Go to Azure Portal > Cost Management + Billing.' },
            { label: 'Install Azure CLI', command: 'https://docs.microsoft.com/cli/azure/install-azure-cli' },
            { label: 'Login to Azure', command: 'az login' },
            { label: 'Set Active Subscription', command: 'az account set --subscription YOUR_SUBSCRIPTION_ID' },
            { label: 'Get User ID', command: 'az ad signed-in-user show --query id -o tsv' },
            { label: 'Assign Cost Reader Role', command: 'az role assignment create --assignee YOUR_USER_ID --role "Cost Management Reader" --scope "/subscriptions/YOUR_SUBSCRIPTION_ID"', note: 'Role MUST be assigned at Subscription scope. Alternative roles: Reader, Contributor.' },
            {
                label: 'Verify Cost Data (Azure REST)',
                command: 'az rest --method post --uri "https://management.azure.com/subscriptions/YOUR_SUBSCRIPTION_ID/providers/Microsoft.CostManagement/query?api-version=2023-03-01" --body "{\\"type\\":\\"ActualCost\\",\\"timeframe\\":\\"MonthToDate\\",\\"dataset\\":{\\"granularity\\":\\"Daily\\"}}"',
                note: 'If 403: RBAC missing. If empty: Billing delay (up to 24h). No export required - Azure Cost Management API provides direct access.'
            },
        ],
    },
};

export function SetupInstructions() {
    const { provider, cloudStatus } = useOpsStore();
    const config = SETUP_STEPS[provider] || SETUP_STEPS.gcp;
    const currentStatus = cloudStatus?.[provider as keyof typeof cloudStatus];

    const isUrl = (s: string) => s.startsWith('http');

    return (
        <div className="max-w-2xl mx-auto py-12 space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">{config.title}</h1>
                <p className="text-muted-foreground mt-2">
                    OpsYield could not detect a valid configuration for your cloud environment.
                    Please follow these steps to connect.
                </p>
                {currentStatus?.error && (
                    <div className="mt-4 p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
                        {currentStatus.error}
                    </div>
                )}
            </div>

            <div className="space-y-4">
                {config.steps.map((step, i) => (
                    <div key={i} className="bg-card border rounded-xl p-5 space-y-3">
                        <div className="flex items-center gap-3">
                            <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center text-primary-foreground text-sm font-bold">
                                {i + 1}
                            </div>
                            <h3 className="font-semibold">{step.label}</h3>
                        </div>
                        {isUrl(step.command) ? (
                            <a
                                href={step.command}
                                target="_blank"
                                rel="noreferrer"
                                className="block bg-black/40 rounded-lg px-4 py-2.5 font-mono text-sm text-green-400 hover:text-green-300 transition"
                            >
                                {step.command}
                            </a>
                        ) : (
                            <div className="bg-black/40 rounded-lg px-4 py-2.5 font-mono text-sm text-green-400 select-all">
                                {step.command}
                            </div>
                        )}
                        {step.note && (
                            <p className="text-xs text-muted-foreground italic border-l-2 border-primary/50 pl-2 mt-1">
                                {step.note}
                            </p>
                        )}
                    </div>
                ))}
            </div>

            <p className="text-xs text-muted-foreground text-center">
                After completing setup, click the <strong>refresh</strong> button in the top bar to re-check connectivity.
            </p>
        </div>
    );
}
