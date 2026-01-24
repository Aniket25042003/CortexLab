/**
 * API Client
 * 
 * Centralized API configuration and request utilities.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: `${API_BASE_URL}/api`,
    withCredentials: true, // Include cookies in requests
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor for adding auth token if stored in memory
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('session_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Flag to prevent multiple redirects
let isRedirecting = false;

// Response interceptor for handling errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && !isRedirecting) {
            isRedirecting = true;

            // Clear all auth-related storage
            localStorage.removeItem('session_token');
            localStorage.removeItem('user');
            localStorage.removeItem('cortexlab-auth'); // Clear zustand persisted state

            // Use a small delay to ensure storage is cleared before redirect
            setTimeout(() => {
                window.location.href = '/login';
            }, 100);
        }
        return Promise.reject(error);
    }
);

// API Types
export interface User {
    id: string;
    email: string;
    name: string;
    avatar_url?: string;
}

export interface Project {
    id: string;
    title: string;
    description?: string;
    domain_tags?: { tags?: string[] };
    status: string;
    created_at: string;
    updated_at: string;
    artifact_count?: number;
    source_count?: number;
    experiment_count?: number;
}


export interface AgentRun {
    id: string;
    project_id: string;
    run_type: 'discovery' | 'deep_dive' | 'paper';
    status: 'pending' | 'running' | 'completed' | 'failed';
    config?: Record<string, any>;
    result?: Record<string, any>;
    error_message?: string;
    started_at?: string;
    finished_at?: string;
    created_at: string;
}

export interface Artifact {
    id: string;
    project_id: string;
    artifact_type: string;
    title: string;
    content_markdown: string;
    version: number;
    created_at: string;
    updated_at: string;
}

// API Functions
export const authApi = {
    googleAuth: (idToken: string) =>
        api.post<{ user: User; session_token: string }>('/auth/google', { id_token: idToken }),
    logout: () => api.post('/auth/logout'),
    getMe: () => api.get<User>('/auth/me'),
};

export const projectsApi = {
    list: () => api.get<{ projects: Project[]; total: number }>('/projects'),
    get: (id: string) => api.get<Project>(`/projects/${id}`),
    create: (data: { title: string; description?: string; domain_tags?: string[] }) =>
        api.post<Project>('/projects', data),
    update: (id: string, data: Partial<Project>) => api.put<Project>(`/projects/${id}`, data),
    delete: (id: string) => api.delete(`/projects/${id}`),
};


export const runsApi = {
    list: (projectId: string) => api.get<{ runs: AgentRun[]; total: number }>(`/projects/${projectId}/runs`),
    get: (runId: string) => api.get<AgentRun>(`/runs/${runId}`),
    startDiscovery: (projectId: string, query: string) =>
        api.post<AgentRun>(`/projects/${projectId}/runs/discovery`, { query }),
    startDeepDive: (projectId: string, directionId: string, directionSummary: string) =>
        api.post<AgentRun>(`/projects/${projectId}/runs/deep-dive`, {
            direction_id: directionId,
            direction_summary: directionSummary,
        }),
    startPaper: (projectId: string, experimentIds: string[] = []) =>
        api.post<AgentRun>(`/projects/${projectId}/runs/paper`, { include_experiments: experimentIds }),
};

export const artifactsApi = {
    list: (projectId: string) => api.get<{ artifacts: Artifact[]; total: number }>(`/projects/${projectId}/artifacts`),
    get: (artifactId: string) => api.get<Artifact>(`/artifacts/${artifactId}`),
    update: (artifactId: string, data: { title?: string; content_markdown?: string }) =>
        api.put<Artifact>(`/artifacts/${artifactId}`, data),
    revise: (artifactId: string, instructions: string) =>
        api.post<Artifact>(`/artifacts/${artifactId}/revise`, { instructions }),
    exportDocx: (artifactId: string) =>
        api.post(`/artifacts/${artifactId}/export/docx`, {}, { responseType: 'blob' }),
};

export const experimentsApi = {
    list: (projectId: string) => api.get<{ experiments: any[]; total: number }>(`/projects/${projectId}/experiments`),
    upload: (projectId: string, file: File, description?: string) => {
        const formData = new FormData();
        formData.append('file', file);
        if (description) {
            formData.append('description', description);
        }
        return api.post(`/projects/${projectId}/experiments/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
    },
    delete: (id: string, projectId: string) => api.delete(`/projects/${projectId}/experiments/${id}`),
};
