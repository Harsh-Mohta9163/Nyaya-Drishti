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

export interface UserShape {
  id: number;
  username: string;
  email: string;
  role: string;
  language?: string;
  department_id: number | null;
  department_code: string | null;
  department_name: string | null;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: UserShape;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  sector: string;
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
  primary_department: Department | null;
  secondary_departments: Department[];
  judgments: JudgmentData[];
  appeals: any[];
  incoming_citations: any[];
  created_at: string;
  updated_at: string;
}

export interface DeptDashboardRow {
  id: number;
  code: string;
  name: string;
  sector: string;
  total_cases: number;
  high_risk: number;
  pending: number;
}

export interface CaseListResponse {
  count: number;
  results: CaseData[];
}

export async function fetchCases(deptCode?: string | null): Promise<CaseData[]> {
  const qs = deptCode ? `?department=${encodeURIComponent(deptCode)}` : '';
  const resp = await apiGet<CaseListResponse | CaseData[]>(`/api/cases/${qs}`);
  if (Array.isArray(resp)) return resp;
  if ('results' in (resp as any)) return (resp as CaseListResponse).results;
  return [];
}

export async function fetchCase(caseId: string): Promise<CaseData> {
  return apiGet<CaseData>(`/api/cases/${caseId}/`);
}

// ─── Department APIs ─────────────────────────────────────────────────────────

export async function fetchDepartments(): Promise<Department[]> {
  const resp = await fetch(`${BASE_URL}/api/auth/departments/`).then(r => r.json());
  // /api/auth/departments/ is public; uses default pagination
  if (Array.isArray(resp)) return resp;
  if ('results' in resp) return resp.results;
  return [];
}

export async function fetchByDepartmentDashboard(): Promise<DeptDashboardRow[]> {
  return apiGet<DeptDashboardRow[]>('/api/dashboard/by-department/');
}

export async function updateCaseDepartment(
  caseId: string,
  primaryCode: string,
  secondaryCodes: string[],
): Promise<CaseData> {
  return apiPatch<CaseData>(`/api/cases/${caseId}/department/`, {
    primary_department: primaryCode,
    secondary_departments: secondaryCodes,
  });
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

export async function updateActionPlanDeadline(planId: string, newDate: string): Promise<any> {
  return apiPatch<any>(`/api/action-plans/${planId}/`, { statutory_appeal_deadline: newDate });
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

// ─── LCO Execution dashboard ─────────────────────────────────────────────────

export type ExecutionStatus = 'pending' | 'in_progress' | 'completed' | 'blocked';

export interface DirectiveExecution {
  id: string;
  action_plan: number;
  directive_index: number;
  directive_text: string;
  responsible_entity: string;
  action_required: string;
  deadline_mentioned: string;
  status: ExecutionStatus;
  executed_by: number | null;
  executed_by_name: string | null;
  completed_at: string | null;
  proof_file: string | null;
  proof_file_url: string | null;
  notes: string;
  case_id: string;
  case_number: string;
  case_title: string;
  department_code: string | null;
  department_name: string | null;
  compliance_deadline: string | null;
  // Government-perspective enrichment
  actor_type: string | null;
  gov_action_required: boolean | null;
  implementation_steps: string[];
  display_note: string;
  govt_summary: string;
  created_at: string;
  updated_at: string;
}

export async function fetchExecutions(opts?: {
  department?: string | null;
  status?: ExecutionStatus | null;
}): Promise<DirectiveExecution[]> {
  const params = new URLSearchParams();
  if (opts?.department) params.set('department', opts.department);
  if (opts?.status) params.set('status', opts.status);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiGet<DirectiveExecution[]>(`/api/action-plans/execution/${qs}`);
}

export async function updateExecution(
  executionId: string,
  patch: { status?: ExecutionStatus; notes?: string; proof_file?: File | null },
): Promise<DirectiveExecution> {
  const fd = new FormData();
  if (patch.status) fd.append('status', patch.status);
  if (typeof patch.notes === 'string') fd.append('notes', patch.notes);
  if (patch.proof_file) fd.append('proof_file', patch.proof_file);

  const res = await fetch(`${BASE_URL}/api/action-plans/execution/${executionId}/`, {
    method: 'PATCH',
    headers: authHeaders(), // no Content-Type — browser sets multipart boundary
    body: fd,
  });
  if (res.status === 401) {
    authLogout();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PATCH execution failed: ${res.status} - ${err}`);
  }
  return res.json();
}

// ─── Nodal Officer Deadlines ─────────────────────────────────────────────────

export interface DeadlineRow {
  action_plan_id: number;
  case_id: string;
  case_number: string;
  case_title: string;
  department_code: string | null;
  department_name: string | null;
  recommendation: string;
  verification_status: string;
  compliance_deadline: string | null;
  internal_compliance_deadline: string | null;
  statutory_appeal_deadline: string | null;
  internal_appeal_deadline: string | null;
  statutory_period_type: string;
  contempt_risk: string;
  next_deadline: string | null;
  next_deadline_label: string;
  days_remaining: number | null;
  urgency: 'overdue' | 'critical' | 'warning' | 'safe' | 'unknown';
}

export async function fetchDeadlines(department?: string | null): Promise<DeadlineRow[]> {
  const qs = department ? `?department=${encodeURIComponent(department)}` : '';
  return apiGet<DeadlineRow[]>(`/api/dashboard/deadlines-monitor/${qs}`);
}
