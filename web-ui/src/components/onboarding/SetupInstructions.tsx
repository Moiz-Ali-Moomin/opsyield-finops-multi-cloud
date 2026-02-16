
import { useOpsStore } from '@/store/useOpsStore';

const SETUP_STEPS: Record<string, { title: string; steps: { label: string; command: string }[] }> = {
    gcp: {
        title: 'Setup GCP Connectivity',
        steps: [
            { label: 'Install Google Cloud CLI', command: 'https://cloud.google.com/sdk/docs/install' },
            { label: 'Login & Authenticate', command: 'gcloud auth login' },
            { label: 'Set Active Project', command: 'gcloud config set project YOUR_PROJECT_ID' },
            { label: 'Login Application Default Credentials', command: 'gcloud auth application-default login' },
        ],
    },
    aws: {
        title: 'Setup AWS Connectivity',
        steps: [
            { label: 'Install AWS CLI', command: 'https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html' },
            { label: 'Configure Credentials', command: 'aws configure' },
            { label: 'Verify Identity', command: 'aws sts get-caller-identity' },
            { label: 'Enable Cost Explorer (Console)', command: 'https://console.aws.amazon.com/cost-management/home#/cost-explorer' },
        ],
    },
    azure: {
        title: 'Setup Azure Connectivity',
        steps: [
            { label: 'Install Azure CLI', command: 'https://learn.microsoft.com/en-us/cli/azure/install-azure-cli' },
            { label: 'Login to Azure', command: 'az login' },
            { label: 'Set Active Subscription', command: 'az account set --subscription YOUR_SUBSCRIPTION_ID' },
            { label: 'Verify Account', command: 'az account show' },
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
                    </div>
                ))}
            </div>

            <p className="text-xs text-muted-foreground text-center">
                After completing setup, click the <strong>refresh</strong> button in the top bar to re-check connectivity.
            </p>
        </div>
    );
}
