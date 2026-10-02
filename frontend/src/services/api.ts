import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface ResearchJobCreate {
  user_question: string;
  research_depth?: 'quick' | 'standard' | 'deep';
}

export interface ResearchJob {
  id: string;
  user_question: string;
  research_depth: string;
  status: string;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface Source {
  id: string;
  title?: string;
  url?: string;
  publisher?: string;
  published_at?: string | null;
  source_type?: string;
  relevance_score?: number | null;
}

export interface Evidence {
  id: string;
  text: string;
  source?: Source | null;
}

export interface Claim {
  id: string;
  claim: string;
  confidence: number;
  evidence: Evidence[];
}

export interface Report {
  id: string;
  content: string;
  created_at: string;
}

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const startResearch = async (data: ResearchJobCreate): Promise<ResearchJob> => {
  const response = await apiClient.post<ResearchJob>('/research', data);
  return response.data;
};

export const getResearchJob = async (jobId: string): Promise<ResearchJob> => {
  const response = await apiClient.get<ResearchJob>(`/research/${jobId}`);
  return response.data;
};

export const getResearchSources = async (jobId: string): Promise<Source[]> => {
  const response = await apiClient.get<Source[]>(`/research/${jobId}/sources`);
  return response.data;
};

export const getResearchClaims = async (jobId: string): Promise<Claim[]> => {
  const response = await apiClient.get<Claim[]>(`/research/${jobId}/claims`);
  return response.data;
};

export const getResearchReport = async (jobId: string): Promise<Report> => {
  const response = await apiClient.get<Report>(`/research/${jobId}/report`);
  return response.data;
};

export const getResearchStreamUrl = (jobId: string): string => {
  return `${BASE_URL}/research/${jobId}/stream`;
};

