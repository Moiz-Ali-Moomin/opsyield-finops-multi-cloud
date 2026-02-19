import axios, { AxiosResponse, AxiosError } from 'axios';

// =====================================================
// API BASE URL
// =====================================================
// Uses environment variable if available, otherwise defaults to local backend

const API_BASE =
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// =====================================================
// TYPES FROM BACKEND MODELS
// =====================================================

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

    cost_drivers?: { service: string; cost: number; currency?: string }[];
    resource_types?: Record<string, number>;
    running_count?: number;
    high_cost_resources?: unknown[];
    idle_resources?: unknown[];
    waste_findings?: unknown[];
}

// =====================================================
// AXIOS INSTANCE
// =====================================================

export const api = axios.create({
    baseURL: API_BASE,
    timeout: 90000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// =====================================================
// REQUEST INTERCEPTOR
// =====================================================

api.interceptors.request.use(
    (config) => {
        console.log(
            `API Request → ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`
        );
        return config;
    },
    (error) => {
        console.error('Request Error:', error.message);
        return Promise.reject(error);
    }
);

// =====================================================
// RESPONSE INTERCEPTOR
// =====================================================

api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {

        if (error.response) {
            console.error(
                `API Error ${error.response.status}:`,
                error.response.data
            );
        } else if (error.request) {
            console.error(
                'Backend not reachable. Is opsyield backend running on port 8000?'
            );
        } else {
            console.error('Axios Error:', error.message);
        }

        return Promise.reject(error);
    }
);
