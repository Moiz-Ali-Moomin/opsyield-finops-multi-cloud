
import axios, { AxiosResponse, AxiosError } from 'axios';

// Types derived from backend models
export interface CloudStatus {
    gcp: {
        installed: boolean;
        authenticated: boolean;
        error?: string;
        projects?: { id: string; name: string }[];
    };
    aws: {
        installed: boolean;
        authenticated: boolean;
        error?: string;
    };
    azure: {
        installed: boolean;
        authenticated: boolean;
        error?: string;
        subscriptions?: { id: string; name: string }[];
    };
}

export interface Resource {
    id: string;
    name: string;
    type: string;
    provider: string;
    region?: string;
    creation_date?: string;
    [key: string]: unknown;
}

export interface NormalizedCost {
    amount: number;
    currency: string;
    date: string;
    service: string;
    provider: string;
    account?: string;
    region?: string;
    tags?: Record<string, string>;
}

export interface AnalysisResult {
    meta: {
        provider: string;
        period: string;
        generated_at?: string;
    };
    summary: {
        total_cost: number;
        resource_count: number;
        risk_score: number;
        currency?: string;
    };
    trends: NormalizedCost[];
    anomalies: unknown[];
    forecast: unknown[];
    governance_issues: unknown[];
    resources: Resource[];
    // Optional enrichment fields from backend
    cost_drivers?: { service: string; cost: number; currency?: string }[];
    resource_types?: Record<string, number>;
    running_count?: number;
    high_cost_resources?: unknown[];
    idle_resources?: unknown[];
    waste_findings?: unknown[];
}

export const api = axios.create({
    baseURL: '/api',
    timeout: 90000, // 90s timeout for real CLI calls (gcloud/aws/az)
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
        console.error('API Error:', error.response || error.message);
        return Promise.reject(error);
    }
);
