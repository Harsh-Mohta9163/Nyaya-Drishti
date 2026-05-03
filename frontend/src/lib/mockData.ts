import type {
  Case, ExtractedData, ActionPlan, DashboardStats,
  DeadlineItem, HighRiskCase, Notification, PendingReview, ReviewLog
} from '../types';

export const mockUser = {
  id: 1, username: 'priya_reviewer', email: 'priya@karnataka.gov.in',
  role: 'reviewer' as const, department: 'Revenue Department',
  language_preference: 'en' as const,
};

export const mockCases: Case[] = [
  {
    id: 1, case_number: 'WP/12345/2024', court: 'Karnataka High Court',
    bench: 'Hon. Justice R. Nataraj', petitioner: 'ABC Industries Ltd.',
    respondent: 'State of Karnataka & Ors.', case_type: 'WP',
    judgment_date: '2024-11-15', status: 'review_pending',
    ocr_confidence: 0.94, created_at: '2024-11-15T10:30:00Z',
  },
  {
    id: 2, case_number: 'SLP/4567/2024', court: 'Karnataka High Court',
    bench: 'Division Bench', petitioner: 'Ramaiah & Sons',
    respondent: 'Revenue Department', case_type: 'SLP',
    judgment_date: '2024-11-10', status: 'action_created',
    ocr_confidence: 0.88, created_at: '2024-11-10T09:00:00Z',
  },
  {
    id: 3, case_number: 'Appeal/789/2024', court: 'Supreme Court of India',
    bench: 'Hon. Justice S. Kumar & Hon. Justice M. Rao', petitioner: 'State of Karnataka',
    respondent: 'XYZ Corporation Pvt. Ltd.', case_type: 'Appeal',
    judgment_date: '2024-10-25', status: 'verified',
    ocr_confidence: 0.97, created_at: '2024-10-25T14:00:00Z',
  },
  {
    id: 4, case_number: 'CCP/234/2024', court: 'Karnataka High Court',
    bench: 'Hon. Justice P. Reddy', petitioner: 'Farmers Union Karnataka',
    respondent: 'Dept. of Agriculture & Ors.', case_type: 'CCP',
    judgment_date: '2024-12-01', status: 'processing',
    ocr_confidence: null, created_at: '2024-12-01T08:15:00Z',
  },
  {
    id: 5, case_number: 'WP/6789/2024', court: 'Karnataka High Court',
    bench: 'Hon. Justice V. Sharma', petitioner: 'Municipal Workers Association',
    respondent: 'BBMP & State of Karnataka', case_type: 'WP',
    judgment_date: '2024-11-28', status: 'extracted',
    ocr_confidence: 0.91, created_at: '2024-11-28T11:45:00Z',
  },
  {
    id: 6, case_number: 'LPA/112/2024', court: 'Karnataka High Court',
    bench: 'Division Bench - Justice A. Patil & Justice K. Gowda',
    petitioner: 'Green Earth Foundation', respondent: 'State Pollution Control Board',
    case_type: 'LPA', judgment_date: '2024-11-20', status: 'uploaded',
    ocr_confidence: null, created_at: '2024-11-20T16:30:00Z',
  },
  {
    id: 7, case_number: 'WP/9012/2024', court: 'Karnataka High Court',
    bench: 'Hon. Justice L. Hegde', petitioner: 'Karnataka Teachers Federation',
    respondent: 'Dept. of Education', case_type: 'WP',
    judgment_date: '2024-12-05', status: 'review_pending',
    ocr_confidence: 0.85, created_at: '2024-12-05T09:30:00Z',
  },
];

export const mockExtractedData: ExtractedData = {
  id: 1, case: 1,
  header_data: {
    case_number: 'WP/12345/2024',
    court: 'Karnataka High Court',
    bench: 'Hon. Justice R. Nataraj',
    petitioner: 'ABC Industries Ltd.',
    respondent: 'State of Karnataka & Ors.',
    judgment_date: '2024-11-15',
  },
  operative_order: `1. The Writ Petition is allowed.\n2. The State Government is directed to pay compensation of Rs. 15,00,000 to the petitioner within 60 days from the date of this order.\n3. The respondent Revenue Department shall file a compliance report within 90 days.\n4. Costs of Rs. 25,000 shall be paid to the petitioner.`,
  court_directions: [
    {
      id: 'd1', verbatim_text: 'The State Government is directed to pay compensation of Rs. 15,00,000 to the petitioner within 60 days from the date of this order.',
      direction_type: 'payment', responsible_entity: 'Revenue Department',
      confidence: 0.96,
      source_reference: { page: 1, paragraph: 4, char_offset: 1204, text_snippet: 'traditional compilers' },
    },
    {
      id: 'd2', verbatim_text: 'The respondent Revenue Department shall file a compliance report within 90 days.',
      direction_type: 'compliance', responsible_entity: 'Revenue Department',
      confidence: 0.92,
      source_reference: { page: 4, paragraph: 5, char_offset: 1380, text_snippet: 'nested loop structure' },
    },
    {
      id: 'd3', verbatim_text: 'Costs of Rs. 25,000 shall be paid to the petitioner.',
      direction_type: 'payment', responsible_entity: 'Revenue Department',
      confidence: 0.89,
      source_reference: { page: 10, paragraph: 1, char_offset: 1520, text_snippet: 'interpreter state' },
    },
  ],
  order_type: 'Compliance',
  entities: ['Revenue Department', 'Finance Department', 'Law Department'],
  extraction_confidence: 0.93,
  source_references: [],
};

export const mockActionPlan: ActionPlan = {
  id: 1, case: 1, recommendation: 'Comply', recommendation_confidence: 0.87,
  compliance_actions: [
    { id: 'a1', step_number: 1, action: 'Prepare LCO Proposal for compensation payment of Rs. 15,00,000',
      responsible_department: 'Revenue Department', depends_on: [], is_complete: false },
    { id: 'a2', step_number: 2, action: 'Obtain GA/LCO Authorization from Law Department',
      responsible_department: 'Law Department', depends_on: ['a1'], is_complete: false },
    { id: 'a3', step_number: 3, action: 'Release funds via Finance Department',
      responsible_department: 'Finance Department', depends_on: ['a2'], is_complete: false },
    { id: 'a4', step_number: 4, action: 'Process payment to petitioner ABC Industries Ltd.',
      responsible_department: 'Revenue Department', depends_on: ['a3'], is_complete: false },
    { id: 'a5', step_number: 5, action: 'File compliance report with the Court',
      responsible_department: 'Law Department', depends_on: ['a4'], is_complete: false },
  ],
  legal_deadline: '2025-01-15',
  internal_deadline: '2024-12-31',
  statutory_basis: 'Writ compliance — 60 days from judgment date (court order)',
  responsible_departments: ['Revenue Department', 'Finance Department', 'Law Department'],
  ccms_stage: 'Order Compliance Stage',
  contempt_risk: 'High',
  similar_cases: [
    { case_number: 'WP/9876/2023', outcome: 'Compliance ordered', similarity_score: 0.91,
      summary: 'Similar compensation dispute; department complied within 45 days. Payment of Rs. 12 lakhs processed through Finance Department.' },
    { case_number: 'WP/5432/2023', outcome: 'Compliance with delay', similarity_score: 0.84,
      summary: 'Delayed compliance led to contempt notice. Eventually complied after 90 days with additional costs.' },
    { case_number: 'WP/1111/2022', outcome: 'Appealed to Supreme Court', similarity_score: 0.78,
      summary: 'State appealed the HC order. SLP dismissed. Had to comply with additional penalty.' },
    { case_number: 'CCP/222/2023', outcome: 'Contempt proceedings initiated', similarity_score: 0.75,
      summary: 'Non-compliance beyond 60 days resulted in contempt. Department fined Rs. 50,000.' },
  ],
  verification_status: 'pending',
};

export const mockDashboardStats: DashboardStats = {
  total_cases: 142, pending_review: 23, high_risk: 8,
  upcoming_deadlines_7d: 5, verified_this_month: 31, avg_extraction_confidence: 0.91,
};

export const mockDeadlines: DeadlineItem[] = [
  { case_id: 1, case_number: 'WP/12345/2024', case_type: 'WP',
    legal_deadline: '2025-01-15', internal_deadline: '2024-12-31',
    contempt_risk: 'High', ccms_stage: 'Order Compliance Stage', days_remaining: 3 },
  { case_id: 2, case_number: 'SLP/4567/2024', case_type: 'SLP',
    legal_deadline: '2025-02-20', internal_deadline: '2025-01-31',
    contempt_risk: 'Medium', ccms_stage: 'GA/LCO Authorization', days_remaining: 12 },
  { case_id: 5, case_number: 'WP/6789/2024', case_type: 'WP',
    legal_deadline: '2025-01-28', internal_deadline: '2025-01-15',
    contempt_risk: 'High', ccms_stage: 'LCO Proposal', days_remaining: 5 },
  { case_id: 7, case_number: 'WP/9012/2024', case_type: 'WP',
    legal_deadline: '2025-03-05', internal_deadline: '2025-02-20',
    contempt_risk: 'Low', ccms_stage: 'Draft PWR', days_remaining: 25 },
  { case_id: 3, case_number: 'Appeal/789/2024', case_type: 'Appeal',
    legal_deadline: '2025-01-25', internal_deadline: '2025-01-10',
    contempt_risk: 'Medium', ccms_stage: 'Affidavit Filing', days_remaining: 8 },
];

export const mockHighRisk: HighRiskCase[] = [
  { case_id: 1, case_number: 'WP/12345/2024', court: 'Karnataka High Court',
    petitioner: 'ABC Industries Ltd.', contempt_risk: 'High',
    legal_deadline: '2025-01-15', days_remaining: 3, ccms_stage: 'Order Compliance Stage' },
  { case_id: 5, case_number: 'WP/6789/2024', court: 'Karnataka High Court',
    petitioner: 'Municipal Workers Association', contempt_risk: 'High',
    legal_deadline: '2025-01-28', days_remaining: 5, ccms_stage: 'LCO Proposal' },
  { case_id: 4, case_number: 'CCP/234/2024', court: 'Karnataka High Court',
    petitioner: 'Farmers Union Karnataka', contempt_risk: 'High',
    legal_deadline: '2025-01-20', days_remaining: 2, ccms_stage: 'Order Compliance Stage' },
];

export const mockNotifications: Notification[] = [
  { id: 1, case: 1, case_number: 'WP/12345/2024', notification_type: 'deadline_warning',
    message: 'Legal deadline in 3 days. Immediate action required for compensation payment.',
    is_read: false, created_at: new Date().toISOString() },
  { id: 2, case: 5, case_number: 'WP/6789/2024', notification_type: 'high_risk_alert',
    message: 'High contempt risk — compliance deadline approaching for WP/6789/2024.',
    is_read: false, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 3, case: 7, case_number: 'WP/9012/2024', notification_type: 'review_assigned',
    message: 'New case WP/9012/2024 assigned for field-level review.',
    is_read: false, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 4, case: 3, case_number: 'Appeal/789/2024', notification_type: 'case_verified',
    message: 'Case Appeal/789/2024 has been verified and action plan approved.',
    is_read: true, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 5, case: 4, case_number: 'CCP/234/2024', notification_type: 'escalation',
    message: 'Case CCP/234/2024 escalated — only 2 days remaining for compliance.',
    is_read: false, created_at: new Date(Date.now() - 1800000).toISOString() },
];

export const mockPendingReviews: PendingReview[] = [
  { case_id: 1, case_number: 'WP/12345/2024', court: 'Karnataka High Court',
    contempt_risk: 'High', review_level: 'field', created_at: new Date().toISOString() },
  { case_id: 7, case_number: 'WP/9012/2024', court: 'Karnataka High Court',
    contempt_risk: 'Medium', review_level: 'field', created_at: new Date(Date.now() - 3600000).toISOString() },
  { case_id: 5, case_number: 'WP/6789/2024', court: 'Karnataka High Court',
    contempt_risk: 'High', review_level: 'directive', created_at: new Date(Date.now() - 7200000).toISOString() },
];

export const mockReviewLogs: ReviewLog[] = [
  {
    id: 1, action_plan: 1,
    reviewer: { id: 2, username: 'anil_head', email: 'anil@karnataka.gov.in', role: 'dept_head', department: 'Revenue Department', language_preference: 'en' },
    review_level: 'field', action: 'approve', changes: null, reason: null,
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 2, action_plan: 1,
    reviewer: { id: 1, username: 'priya_reviewer', email: 'priya@karnataka.gov.in', role: 'reviewer', department: 'Revenue Department', language_preference: 'en' },
    review_level: 'field', action: 'edit',
    changes: { petitioner: 'ABC Industries Pvt. Ltd.' },
    reason: 'Corrected company name from Ltd. to Pvt. Ltd.',
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
];
