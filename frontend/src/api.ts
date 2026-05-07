/**
 * NyayaDrishti — Centralized API Service Layer
 * All backend communication flows through here.
 * Handles JWT auth, token refresh, and base URL configuration.
 */

const API_BASE = 'http://127.0.0.1:8000/api';

// ---------- Token Management ----------
export function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

export function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token');
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

// ---------- Core Fetch Wrapper ----------
async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // If 401, attempt token refresh
  if (response.status === 401) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${API_BASE}/auth/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken }),
        });

        if (refreshRes.ok) {
          const data = await refreshRes.json();
          setTokens(data.access, data.refresh || refreshToken);
          headers['Authorization'] = `Bearer ${data.access}`;
          // Retry the original request
          response = await fetch(`${API_BASE}${path}`, { ...options, headers });
        } else {
          clearTokens();
        }
      } catch {
        clearTokens();
      }
    }
  }

  return response;
}

// ---------- Auth APIs ----------
export async function apiLogin(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }

  const data = await res.json();
  setTokens(data.access, data.refresh);
  return data;
}

export async function apiRegister(userData: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  department?: string;
  role?: string;
}) {
  const res = await fetch(`${API_BASE}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(JSON.stringify(err));
  }

  const data = await res.json();
  // Registration returns tokens too
  if (data.access) {
    setTokens(data.access, data.refresh);
  }
  return data;
}

export async function apiGetMe() {
  const res = await apiFetch('/auth/me/');
  if (!res.ok) throw new Error('Session expired');
  return res.json();
}

// ---------- Case APIs ----------
export async function apiGetCases() {
  const res = await apiFetch('/cases/');
  if (!res.ok) throw new Error('Failed to fetch cases');
  return res.json();
}

export async function apiGetCase(id: string) {
  const res = await apiFetch(`/cases/${id}/`);
  if (!res.ok) throw new Error('Failed to fetch case');
  return res.json();
}

export async function apiUploadCase(pdfFile: File) {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append('pdf_file', pdfFile);

  const res = await fetch(`${API_BASE}/cases/extract/`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!res.ok) throw new Error('Failed to upload case');
  return res.json();
}

// ---------- Action Plan APIs ----------
export async function apiGetActionPlans() {
  const res = await apiFetch('/action-plans/');
  if (!res.ok) throw new Error('Failed to fetch action plans');
  return res.json();
}

export async function apiGenerateActionPlan(caseId: string) {
  const res = await apiFetch(`/action-plans/${caseId}/generate/`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to generate action plan');
  return res.json();
}

// ---------- RAG Recommendation API ----------
export async function apiGetRecommendation(params: {
  case_id?: string;
  case_text?: string;
  area_of_law?: string;
  court?: string;
}) {
  const res = await apiFetch('/action-plans/recommend/', {
    method: 'POST',
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to fetch AI recommendation');
  return res.json();
}

// ---------- Dashboard APIs ----------
export async function apiGetDashboardStats() {
  const res = await apiFetch('/dashboard/');
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}
