// ─── Auth ─────────────────────────────────────────────────────────────
export type Role = 'reviewer' | 'dept_officer' | 'dept_head' | 'legal_advisor';

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
  department: string;
  language_preference: 'en' | 'kn';
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role: Role;
  department?: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

// ─── Cases ────────────────────────────────────────────────────────────
export type CaseStatus =
  | 'uploaded'
  | 'processing'
  | 'extracted'
  | 'review_pending'
  | 'verified'
  | 'action_created';

export type CaseType = 'WP' | 'Appeal' | 'SLP' | 'CCP' | 'LPA';

export type ContemptRisk = 'High' | 'Medium' | 'Low';

export interface Case {
  id: number;
  case_number: string;
  court: string;
  bench: string;
  petitioner: string;
  respondent: string;
  case_type: CaseType;
  judgment_date: string;
  status: CaseStatus;
  ocr_confidence: number | null;
  created_at: string;
}

export interface CaseListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Case[];
}

export interface CaseListParams {
  page?: number;
  page_size?: number;
  status?: CaseStatus;
  case_type?: CaseType;
  contempt_risk?: ContemptRisk;
  search?: string;
  ordering?: string;
}

// ─── Extracted Data ────────────────────────────────────────────────────
export interface SourceReference {
  page: number;
  paragraph: number;
  char_offset: number;
  text_snippet: string;
}

export interface CourtDirection {
  id: string;
  verbatim_text: string;
  direction_type: string;
  responsible_entity: string;
  confidence: number;
  source_reference: SourceReference;
}

export interface ExtractedData {
  id: number;
  case: number;
  header_data: {
    case_number: string;
    court: string;
    bench: string;
    petitioner: string;
    respondent: string;
    judgment_date: string;
  };
  operative_order: string;
  court_directions: CourtDirection[];
  order_type: string;
  entities: string[];
  extraction_confidence: number;
  source_references: SourceReference[];
}

// ─── Action Plan ───────────────────────────────────────────────────────
export type Recommendation = 'Comply' | 'Appeal';

export interface ComplianceAction {
  id: string;
  step_number: number;
  action: string;
  responsible_department: string;
  depends_on: string[];
  is_complete: boolean;
}

export interface SimilarCase {
  case_number: string;
  outcome: string;
  similarity_score: number;
  summary: string;
}

export interface ActionPlan {
  id: number;
  case: number;
  recommendation: Recommendation;
  recommendation_confidence: number;
  compliance_actions: ComplianceAction[];
  legal_deadline: string;
  internal_deadline: string;
  statutory_basis: string;
  responsible_departments: string[];
  ccms_stage: string;
  contempt_risk: ContemptRisk;
  similar_cases: SimilarCase[];
  verification_status: 'pending' | 'field_approved' | 'directive_approved' | 'case_approved';
}

// ─── Review ────────────────────────────────────────────────────────────
export type ReviewLevel = 'field' | 'directive' | 'case';
export type ReviewAction = 'approve' | 'edit' | 'reject';

export interface ReviewRequest {
  review_level: ReviewLevel;
  action: ReviewAction;
  changes?: Record<string, unknown>;
  reason?: string;
}

export interface ReviewLog {
  id: number;
  action_plan: number;
  reviewer: User;
  review_level: ReviewLevel;
  action: ReviewAction;
  changes: Record<string, unknown> | null;
  reason: string | null;
  created_at: string;
}

export interface PendingReview {
  case_id: number;
  case_number: string;
  court: string;
  contempt_risk: ContemptRisk;
  review_level: ReviewLevel;
  created_at: string;
}

// ─── Dashboard ─────────────────────────────────────────────────────────
export interface DashboardStats {
  total_cases: number;
  pending_review: number;
  high_risk: number;
  upcoming_deadlines_7d: number;
  verified_this_month: number;
  avg_extraction_confidence: number;
}

export interface DeadlineItem {
  case_id: number;
  case_number: string;
  case_type: CaseType;
  legal_deadline: string;
  internal_deadline: string;
  contempt_risk: ContemptRisk;
  ccms_stage: string;
  days_remaining: number;
}

export interface HighRiskCase {
  case_id: number;
  case_number: string;
  court: string;
  petitioner: string;
  contempt_risk: ContemptRisk;
  legal_deadline: string;
  days_remaining: number;
  ccms_stage: string;
}

// ─── Notifications ─────────────────────────────────────────────────────
export type NotificationType =
  | 'deadline_warning'
  | 'high_risk_alert'
  | 'review_assigned'
  | 'case_verified'
  | 'escalation';

export interface Notification {
  id: number;
  case: number;
  case_number: string;
  notification_type: NotificationType;
  message: string;
  is_read: boolean;
  created_at: string;
}

// ─── Translation ───────────────────────────────────────────────────────
export interface TranslateRequest {
  text: string;
  source_lang: 'en' | 'kn';
  target_lang: 'en' | 'kn';
}

export interface TranslateResponse {
  translated_text: string;
}
