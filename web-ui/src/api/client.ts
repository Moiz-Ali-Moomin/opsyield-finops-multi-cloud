
import axios, { AxiosResponse, AxiosError } from 'axios';

// Types derived from backend models
export interface CloudStatus {
    gcp: {
        installed: boolean;
        authenticated: boolean;
        projects?: { id: string; name: string }[];
    };
    aws: {
        installed: boolean;
        authenticated: boolean;
    };
    azure: {
        installed: boolean;
        authenticated: boolean;
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
    [key: string]: any;
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
    anomalies: any[];
    forecast: any[];
    governance_issues: any[];
    resources: Resource[];
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
