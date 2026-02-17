import { create } from 'zustand';
import axios from 'axios';
import { api, AnalysisResult, CloudStatus } from '../api/client';

interface OpsState {
    provider: string;
    projectId: string | undefined;
    subscriptionId: string | undefined;
    data: AnalysisResult | null;
    cloudStatus: CloudStatus | null;
    loading: boolean;
    error: string | null;
    isAggregate: boolean;
    executiveMode: boolean;

    selectedProjectId: string | null;
    setSelectedProject: (id: string) => void;
    setProvider: (provider: string) => void;
    setAggregateMode: (enabled: boolean) => void;
    setExecutiveMode: (enabled: boolean) => void;
    fetchData: () => Promise<void>;
    fetchCloudStatus: () => Promise<void>;
}

export const useOpsStore = create<OpsState>((set, get) => ({
    provider: 'gcp',
    selectedProjectId: null,
    projectId: undefined,
    subscriptionId: undefined,
    data: null,
    cloudStatus: null,
    loading: false,
    error: null,
    isAggregate: false,
    executiveMode: false,

    setProvider: (provider: string) => {
        set({ provider, isAggregate: false });
        const status = get().cloudStatus;
        if (status) {
            if (provider === 'azure' && status.azure.subscriptions?.length) {
                set({ subscriptionId: status.azure.subscriptions[0].id });
            }
            if (provider === 'gcp' && status.gcp.projects?.length) {
                set({ selectedProjectId: status.gcp.projects[0].id });
            }
        }
        get().fetchData();
    },

    setSubscriptionId: (subscriptionId: string) => {
        set({ subscriptionId });
    },

    setSelectedProject: (id: string) => {
        set({ selectedProjectId: id });
        get().fetchData();
    },

    setAggregateMode: (enabled: boolean) => {
        set({ isAggregate: enabled });
        get().fetchData();
    },

    setExecutiveMode: (enabled: boolean) => {
        set({ executiveMode: enabled });
    },

    fetchCloudStatus: async () => {
        try {
            const response = await api.get<CloudStatus>('/cloud/status');
            const data = response.data;
            console.log("Cloud Status Update:", data);

            set({ cloudStatus: data });

            // Auto-select if nothing selected yet and we are on GCP
            const current = get();
            if (current.provider === 'gcp' && !current.selectedProjectId && data.gcp.projects?.length) {
                set({ selectedProjectId: data.gcp.projects[0].id });
                current.fetchData();
            }
        } catch (err) {
            console.error("Failed to fetch cloud status", err);
        }
    },

    fetchData: async () => {
        set({ loading: true, error: null });

        const { provider, subscriptionId, isAggregate } = get();

        try {
            let url = '';

            if (isAggregate) {
                url = `/aggregate?providers=gcp,aws,azure&days=30`;
                if (subscriptionId) url += `&subscription_id=${subscriptionId}`;
            } else {
                url = `/analyze?provider=${provider}&days=30`;

                if (provider === 'gcp' && get().selectedProjectId) {
                    url += `&project_id=${get().selectedProjectId}`;
                }

                if (subscriptionId && provider === 'azure') {
                    url += `&subscription_id=${subscriptionId}`;
                }
            }

            const response = await api.get(url);

            let normalizedData = response.data;

            // 🔥 Normalize aggregate response to match AnalysisResult shape
            if (isAggregate) {
                normalizedData = {
                    ...response.data,
                    meta: {
                        generated_at: response.data.meta.generated_at,
                        provider: "aggregate",
                        period: "30 days",
                    }
                };
            }

            set({ data: normalizedData, loading: false });

        } catch (err: unknown) {
            console.error(err);
            let message = 'Failed to fetch data';
            if (axios.isAxiosError(err)) {
                const detail = (err.response?.data as any)?.detail;
                message = detail || err.message || message;
            } else if (err && typeof err === 'object' && 'message' in err) {
                message = String((err as any).message || message);
            }
            set({
                error: message,
                loading: false,
                data: null
            });
        }
    }

}));
