import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

export interface AnalyzePayload {
  repo_url: string;
  branch?: string;
  deep_analysis?: boolean;
}

export const analyzeRepo = (payload: AnalyzePayload) =>
  api.post('/analyze/', payload).then(res => res.data);

export const getAnalysis = (id: string) =>
  api.get(`/analyze/${id}`).then(res => res.data);

export const getAnalysisSummary = (id: string) =>
  api.get(`/analyze/${id}/summary`).then(res => res.data);

export const deleteAnalysis = (id: string) =>
  api.delete(`/analyze/${id}`).then(res => res.data);

export const getDiagram = (analysisId: string, diagramType: string) =>
  api.post('/diagrams/', { analysis_id: analysisId, diagram_type: diagramType }).then(res => res.data);

export const getAllDiagrams = (analysisId: string) =>
  api.get(`/diagrams/${analysisId}`).then(res => res.data);

export const getDiagramTypes = () =>
  api.get('/diagrams/types').then(res => res.data);

export const getHealthScore = (analysisId: string) =>
  api.get(`/health/${analysisId}`).then(res => res.data);

export interface ChatPayload {
  analysis_id: string;
  message: string;
  history?: { role: string; content: string }[];
}

export const chatWithRepo = (payload: ChatPayload) =>
  api.post('/chat/', payload).then(res => res.data);


