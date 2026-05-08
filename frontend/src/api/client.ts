const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function getToken(): string | null {
  return localStorage.getItem('access_token');
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = { ...extra };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: authHeaders({ 'Content-Type': 'application/json' }),
  });
  if (res.status === 401) {
    authLogout();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    authLogout();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`POST ${path} failed: ${res.status} — ${err}`);
  }
  return res.json();
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'PATCH',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(body),
  });
  if (res.status === 401) {
    authLogout();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PATCH ${path} failed: ${res.status} - ${err}`);
  }
  return res.json();
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: authHeaders(), // no Content-Type — browser sets multipart boundary
    body: formData,
  });
  if (res.status === 401) {
    authLogout();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`POST (form) ${path} failed: ${res.status} — ${err}`);
  }
  return res.json();
}

// ─── Auth helpers ────────────────────────────────────────────────────────────

export interface LoginResponse {
  access: string;
  refresh: string;
  user: { id: number; username: string; email: string; role: string; department: string };
}

export async function authLogin(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || 'Login failed');
  }
  const data: LoginResponse = await res.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  return data;
}

export function authLogout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

// ─── Cases API (Updated for new backend with UUID IDs) ───────────────────────

export interface JudgmentData {
  id: string;
  case: string;
  date_of_order: string;
  document_type: string;
  presiding_judges: string[];
  disposition: string;
  winning_party_type: string;
  operative_order_text: string;
  summary_of_facts: string;
  issues_framed: string[];
  ratio_decidendi: string;
  court_directions: any[];
  entities: any[];
  contempt_indicators: any[];
  contempt_risk: string;
  financial_implications: Record<string, any>;
  appeal_type: string;
  extraction_confidence: number;
  ocr_confidence: number | null;
  pdf_file: string;
  pdf_storage_url: string;
  processing_status: string;
  outgoing_citations: any[];
  action_plan: any | null;
  created_at: string;
  updated_at: string;
}

export interface CaseData {
  id: string; // UUID
  matter_id: string;
  cnr_number: string | null;
  court_name: string;
  case_type: string;
  case_number: string;
  case_year: number;
  petitioner_name: string;
  respondent_name: string;
  status: string;
  area_of_law: string;
  primary_statute: string;
  judgments: JudgmentData[];
  appeals: any[];
  incoming_citations: any[];
  created_at: string;
  updated_at: string;
}

export interface CaseListResponse {
  count: number;
  results: CaseData[];
}

export async function fetchCases(): Promise<CaseData[]> {
  const resp = await apiGet<CaseListResponse | CaseData[]>('/api/cases/');
  if (Array.isArray(resp)) return resp;
  if ('results' in (resp as any)) return (resp as CaseListResponse).results;
  return [];
}

export async function fetchCase(caseId: string): Promise<CaseData> {
  return apiGet<CaseData>(`/api/cases/${caseId}/`);
}

/**
 * Call the RAG Recommendation Pipeline for a specific case.
 * POST /api/action-plans/{caseId}/recommend/
 */
export async function fetchRecommendation(caseId: string, forceRegenerate: boolean = false): Promise<any> {
  return apiPost<any>(`/api/action-plans/${caseId}/recommend/`, { force_regenerate: forceRegenerate });
}

/**
 * Upload a PDF and run the full extraction pipeline.
 * POST /api/cases/extract/ with multipart form containing pdf_file.
 * Returns the fully extracted CaseData.
 */
export async function updateJudgment(judgmentId: string, data: Partial<JudgmentData>): Promise<JudgmentData> {
  return apiPatch<JudgmentData>(`/api/cases/judgments/${judgmentId}/`, data);
}

export async function extractCase(pdfFile: File): Promise<CaseData> {
  const formData = new FormData();
  formData.append('pdf_file', pdfFile);
  return apiPostForm<CaseData>('/api/cases/extract/', formData);
}

/**
 * Re-annotate source locations for court directions using PyMuPDF.
 * POST /api/cases/{caseId}/re-annotate/
 * Call this for cases extracted before source highlighting was implemented.
 */
export async function reAnnotateSource(caseId: string): Promise<any> {
  return apiPost<any>(`/api/cases/${caseId}/re-annotate/`, {});
}
