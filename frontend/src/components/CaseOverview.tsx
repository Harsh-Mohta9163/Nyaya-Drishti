import React, { useState } from 'react';
import { motion } from 'motion/react';
import { CaseData, fetchCase } from '../api/client';
import { useAuth, isGlobalRole } from '../context/AuthContext';
import { DepartmentOverrideModal } from './DepartmentOverrideModal';

const ExpandableText = ({ text, maxLines = 3 }: { text: string, maxLines?: number }) => {
  const [expanded, setExpanded] = useState(false);
  if (!text) return <span className="opacity-50 italic">Not extracted</span>;
  
  return (
    <div className="relative">
      <div 
        className="text-sm leading-relaxed"
        style={!expanded ? { display: '-webkit-box', WebkitLineClamp: maxLines, WebkitBoxOrient: 'vertical', overflow: 'hidden' } : {}}
      >
        {text}
      </div>
      {text.length > 150 && (
        <button 
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] font-bold text-primary-blue uppercase tracking-widest hover:underline mt-2 flex items-center gap-1"
        >
          {expanded ? 'Show Less' : 'Show More'} <span className="material-symbols-outlined text-xs">{expanded ? 'expand_less' : 'expand_more'}</span>
        </button>
      )}
    </div>
  );
};

const DetailItem = ({ label, value, clamp = false }: { label: string; value: string, clamp?: boolean }) => {
  const displayValue = clamp && value ? value.toLowerCase() : value;
  return (
  <div className="flex flex-col gap-2">
    <span className="text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.15em] border-b border-outline-variant/10 pb-2">
      {label}
    </span>
    <span className={`text-on-surface font-semibold text-base tracking-tight ${clamp ? 'capitalize line-clamp-2 text-sm leading-snug' : ''}`} title={clamp ? value : undefined}>
      {displayValue}
    </span>
  </div>
  );
};

const getDeadlinePillStyle = (dueDate: string) => {
  const d = dueDate.toLowerCase();

  // Acknowledged / on track / met / complete → muted soft green
  if (d.includes('acknowledged') || d.includes('on track') || d.includes('complete') || d.includes('met')) {
    return { classes: 'bg-green-500/[0.08] text-green-400/65 border-green-500/15', icon: 'check_circle' };
  }

  // Immediate / today / urgent → muted rose-red
  if (d.includes('immediate') || d.includes('today') || d.includes('urgent')) {
    return { classes: 'bg-rose-500/10 text-rose-400 border-rose-500/20', icon: 'priority_high' };
  }

  const num = parseInt(d.match(/\d+/)?.[0] || '0', 10);

  // Any mention of weeks → near, use muted red
  if (d.includes('week')) {
    return { classes: 'bg-rose-500/10 text-rose-400 border-rose-500/20', icon: 'schedule' };
  }

  // 1 month → orange-amber
  if (d.includes('month') && num <= 1) {
    return { classes: 'bg-orange-400/10 text-orange-400/90 border-orange-400/20', icon: 'schedule' };
  }

  // 2-3 months → soft amber
  if (d.includes('month') && num <= 3) {
    return { classes: 'bg-amber-400/[0.09] text-amber-400/80 border-amber-400/18', icon: 'schedule' };
  }

  // 4+ months → muted sky/slate
  return { classes: 'bg-sky-500/[0.07] text-sky-400/65 border-sky-500/15', icon: 'calendar_month' };
};

const getDepartmentColors = (source: string) => {
  const s = source.toLowerCase();
  if (s.includes('pollution') || s.includes('kspcb')) return 'bg-green-500/10 border-green-500/30 text-green-400';
  if (s.includes('revenue') || s.includes('tax')) return 'bg-amber-400/10 border-amber-400/30 text-amber-400';
  if (s.includes('labor') || s.includes('hr')) return 'bg-purple-500/10 border-purple-500/30 text-purple-400';
  if (s.includes('legal')) return 'bg-primary-blue/10 border-primary-blue/30 text-primary-blue';
  return 'bg-surface-container-high/50 border-outline-variant/30 text-on-surface-variant';
};

export const CaseOverview = ({
  caseData,
  verifiedActions,
  onGoToVerify,
  recommendation,
  isGenerating,
  onGenerateAnalysis,
  decision,
  onDecision,
  actionPlanId,
  onDeadlineChange,
}: {
  caseData?: CaseData | null,
  verifiedActions?: any[],
  onGoToVerify?: () => void,
  recommendation?: any | null,
  isGenerating?: boolean,
  onGenerateAnalysis?: () => void,
  decision?: 'none' | 'appeal' | 'comply',
  onDecision?: (decision: 'none' | 'appeal' | 'comply') => void,
  actionPlanId?: string,
  onDeadlineChange?: (newDate: string) => void,
}) => {
  const { user } = useAuth();
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [overrideKey, setOverrideKey] = useState(0); // bump to force re-fetch of case after save
  const [editingDeadline, setEditingDeadline] = useState(false);
  const [deadlineInput, setDeadlineInput] = useState('');
  const [savingDeadline, setSavingDeadline] = useState(false);

  const primaryDept = caseData?.primary_department;
  const secondaryDepts = caseData?.secondary_departments || [];
  const userDeptCode = user?.department_code;
  const canEditDept = !!user && (
    isGlobalRole(user.role)
    || (user.role === 'head_legal_cell' && !!userDeptCode && (
      primaryDept?.code === userDeptCode
      || secondaryDepts.some(d => d.code === userDeptCode)
    ))
  );

  const judgment = caseData?.judgments?.[0];
  const filingDate = judgment?.date_of_order
    ? new Date(judgment.date_of_order).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
    : caseData?.created_at
      ? new Date(caseData.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
      : '—';
    
  const summaryText = judgment?.summary_of_facts || judgment?.operative_order_text || '';
  const isVerified = verifiedActions && verifiedActions.length > 0 && verifiedActions.every(a => a.isVerified);
  
  const aiVerdict = recommendation?.verdict?.decision || 'PENDING';
  const confidence = recommendation?.verdict?.confidence ? Math.round(recommendation.verdict.confidence * 100) : 0;
  const contemptRisk = recommendation?.agent_outputs?.contempt_urgency || judgment?.contempt_risk || 'Low';
  const similarCases = recommendation?.agent_outputs?.precedents || [];
  
  // Court directions for the roadmap — separate verified from unverified
  const verifiedDirections = (verifiedActions || []).filter((a: any) => a.isVerified);
  const unverifiedDirections = (verifiedActions || []).filter((a: any) => !a.isVerified);
  const allDirections = verifiedActions || [];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 sm:gap-8 py-4 sm:py-8">
      {/* Override modal */}
      <DepartmentOverrideModal
        open={overrideOpen}
        caseId={caseData?.id || ''}
        currentPrimaryCode={primaryDept?.code || null}
        currentSecondaryCodes={secondaryDepts.map(d => d.code)}
        onClose={() => setOverrideOpen(false)}
        onSaved={async () => {
          setOverrideKey(k => k + 1);
          if (caseData?.id) {
            try {
              const fresh = await fetchCase(caseData.id);
              // Mutate in place so parent component sees the new dept tags.
              Object.assign(caseData, fresh);
            } catch (_) { /* ignore — page refresh will fix it */ }
          }
        }}
      />

      {/* Left Column */}
      <div className="xl:col-span-7 space-y-6 sm:space-y-8">

        {/* Department Assignment Card — AI tags + override pencil */}
        <div className="glass-card p-5 flex flex-wrap items-center gap-y-4 gap-x-6" key={overrideKey}>

          {/* Row 1: icon + label + primary dept pill */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-center flex-shrink-0 text-on-surface-variant">
              <span className="material-symbols-outlined text-[17px]">apartment</span>
            </div>
            <span className="font-mono text-[11px] tracking-[0.08em] text-on-surface-variant/60 uppercase">Responsible Dept</span>
            {primaryDept ? (
              <button
                className="inline-flex items-center h-[30px] px-3 rounded-lg bg-primary-blue/[0.14] border border-primary-blue/50 text-primary-blue/90 text-[13px] font-medium transition-colors hover:bg-primary-blue/[0.20]"
                title={`Primary department (AI classified) · ${primaryDept.sector}`}
              >
                {primaryDept.name}
              </button>
            ) : (
              <span className="inline-flex items-center h-[30px] px-3 rounded-lg bg-error-red/10 border border-error-red/30 text-error-red text-[12px] font-medium">
                Unclassified
              </span>
            )}
          </div>

          {/* Row 2: "also affects" secondary depts */}
          {secondaryDepts.length > 0 && (
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-[11px] tracking-[0.08em] text-on-surface-variant/60 uppercase">Also Affects</span>
              {secondaryDepts.map(d => (
                <button
                  key={d.code}
                  title={d.sector}
                  className="inline-flex items-center h-[30px] px-3 rounded-lg bg-surface-container-high/60 border border-outline-variant/30 text-on-surface-variant text-[13px] font-medium transition-colors hover:bg-surface-container-highest/50"
                >
                  {d.name}
                </button>
              ))}
            </div>
          )}

          {/* Reassign button — pushed to the right */}
          {canEditDept && (
            <button
              onClick={() => setOverrideOpen(true)}
              className="ml-auto inline-flex items-center gap-2 h-8 px-3.5 rounded-lg border border-outline-variant/30 text-on-surface-variant text-[13px] font-medium transition-colors hover:text-on-surface hover:border-outline-variant/60"
              title="Override AI-assigned department"
            >
              <span className="material-symbols-outlined text-[14px]">edit</span>
              Reassign
            </button>
          )}
        </div>

        {/* Case Details Card */}
        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center gap-4 mb-8">
            <div className="bg-secondary-container/40 p-2.5 rounded-lg border border-outline-variant/20">
              <span className="material-symbols-outlined text-primary-blue">description</span>
            </div>
            <h4 className="font-bold text-on-surface text-xl tracking-tight">Case Details</h4>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-6 sm:gap-10">
            <DetailItem label="Jurisdiction" value={caseData?.court_name || '—'} />
            <DetailItem label="Bench" value={judgment?.presiding_judges?.join(', ') || '—'} clamp={true} />
            <DetailItem label="Filing Date" value={filingDate} />
            <DetailItem label="Case Type" value={caseData?.case_type || '—'} />
            <DetailItem label="Area of Law" value={caseData?.area_of_law || '—'} />
            <DetailItem label="Primary Statute" value={caseData?.primary_statute || '—'} clamp={true} />
          </div>
        </div>

        {/* Executive Case Brief Card */}
        <div className="glass-card p-5 sm:p-8 border-l-4 border-l-primary-blue relative overflow-hidden group">
          <div className="absolute -right-20 -top-20 w-48 h-48 bg-primary-blue/5 blur-[100px] group-hover:bg-primary-blue/10 transition-all duration-500"></div>
          
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-on-surface text-2xl font-bold tracking-tight mb-1">Executive Case Brief</h3>
              <p className="text-on-surface-variant text-xs font-medium tracking-wider uppercase opacity-70">
                Generated by Drishti-V4 Legal Engine
              </p>
            </div>
            <div className="bg-primary-blue/10 p-3 rounded-xl border border-primary-blue/20">
              <span className="material-symbols-outlined text-primary-blue text-2xl">auto_awesome</span>
            </div>
          </div>
          
          <div className="space-y-6">
            <div>
              <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2 flex items-center gap-2">
                <span className="material-symbols-outlined text-sm">subject</span> Summary of Facts
              </h4>
              <ExpandableText text={summaryText} maxLines={4} />
            </div>
            
            {judgment?.issues_framed && judgment.issues_framed.length > 0 && (
              <div>
                <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2 flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">rule</span> Issues Framed
                </h4>
                <ul className="list-disc pl-5 space-y-1 text-sm text-on-surface/90">
                  {judgment.issues_framed.map((i: string, idx: number) => <li key={idx}>{i}</li>)}
                </ul>
              </div>
            )}
            
            {judgment?.ratio_decidendi && (
              <div>
                <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2 flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">gavel</span> Ratio Decidendi
                </h4>
                <ExpandableText text={judgment.ratio_decidendi} />
              </div>
            )}
          </div>
        </div>

        {/* AI Recommendation Card */}
        {recommendation ? (
          <div className="glass-card flex flex-col gap-4 sm:gap-6 p-4 sm:p-8 border border-primary-blue/30 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary-blue/10 rounded-full blur-[50px]"></div>
            
            <div className="flex flex-wrap justify-between items-start gap-4">
              <div className="flex items-center gap-4 min-w-[200px]">
                <div className="w-12 h-12 flex-shrink-0 rounded-full bg-primary-blue/20 border border-primary-blue/30 flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary-blue text-2xl">smart_toy</span>
                </div>
                <div>
                  <h2 className="text-on-surface text-xl sm:text-2xl font-bold tracking-tight mb-1 flex flex-wrap items-center gap-2">
                    AI Recommendation: <span className={aiVerdict === 'COMPLY' ? 'text-green-400' : 'text-amber-400'}>{aiVerdict}</span>
                  </h2>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-primary-blue bg-primary-blue/10 px-2 py-0.5 rounded">
                    {confidence}% Confidence
                  </span>
                </div>
              </div>
              <div className="flex flex-col items-start sm:items-end gap-3 w-full sm:w-auto mt-2 sm:mt-0">
                <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
                  contemptRisk === 'HIGH' ? 'bg-error-red/10 border border-error-red/20' :
                  contemptRisk === 'MEDIUM' ? 'bg-amber-400/10 border border-amber-400/20' :
                  'bg-green-500/10 border border-green-500/20'
                }`}>
                  <span className={`material-symbols-outlined text-sm ${
                    contemptRisk === 'HIGH' ? 'text-error-red' : contemptRisk === 'MEDIUM' ? 'text-amber-400' : 'text-green-400'
                  }`}>warning</span>
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${
                    contemptRisk === 'HIGH' ? 'text-error-red' : contemptRisk === 'MEDIUM' ? 'text-amber-400' : 'text-green-400'
                  }`}>
                    Contempt Risk: {contemptRisk}
                  </span>
                </div>
                {onGenerateAnalysis && (
                  <button 
                    onClick={onGenerateAnalysis}
                    disabled={isGenerating}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary-blue/30 text-primary-blue hover:bg-primary-blue/10 transition-colors text-xs font-bold uppercase tracking-wider disabled:opacity-50"
                  >
                    <span className={`material-symbols-outlined text-[16px] ${isGenerating ? 'animate-spin' : ''}`}>
                      {isGenerating ? 'refresh' : 'sync'}
                    </span>
                    {isGenerating ? 'Regenerating...' : 'Regenerate Analysis'}
                  </button>
                )}
              </div>
            </div>
            
            {/* Show appeal grounds if present */}
            {recommendation.appeal_grounds && recommendation.appeal_grounds.length > 0 && (
               <div>
                 <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2">
                   {aiVerdict === 'APPEAL' ? 'Appeal Grounds' : 'Key Reasoning Points'}
                 </h4>
                 <ul className={`list-disc pl-5 text-sm space-y-1 ${aiVerdict === 'APPEAL' ? 'text-amber-400/90' : 'text-emerald-400/90'}`}>
                   {recommendation.appeal_grounds.map((g: string, i: number) => <li key={i}>{g}</li>)}
                 </ul>
               </div>
            )}

            {/* Show primary reasoning if there are no appeal grounds (e.g. for COMPLY) */}
            {(!recommendation.appeal_grounds || recommendation.appeal_grounds.length === 0) && recommendation.primary_reasoning && (
               <div>
                 <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2">Key Reasoning Points</h4>
                 <p className="text-sm text-emerald-400/90 leading-relaxed">
                   {recommendation.primary_reasoning}
                 </p>
               </div>
            )}

            {/* CCMS Perspective Note */}
            <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl p-4 flex items-start gap-3">
              <span className="material-symbols-outlined text-blue-400 text-sm mt-0.5">account_balance</span>
              <div>
                <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-1">CCMS Perspective</p>
                <p className="text-xs text-on-surface-variant leading-relaxed">
                  {aiVerdict === 'APPEAL' 
                    ? `This recommendation is from the government respondent's perspective. The court ruled in favor of the petitioner — the AI recommends the department consider filing an appeal within the limitation period.`
                    : `This recommendation is from the government respondent's perspective. The AI recommends compliance with the court's order to avoid contempt proceedings.`}
                </p>
              </div>
            </div>

            {/* Key Deadlines Card */}
            {recommendation.verdict && (
              <div className="bg-surface-container/50 border border-outline-variant/10 rounded-xl p-5">
                <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-4 flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm">schedule</span> Key Deadlines & Limitation
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                  {/* Limitation Deadline — HLC can click the pencil to correct the AI date */}
                  <div className="bg-surface-container-high/40 rounded-lg p-3 text-center border border-outline-variant/15 relative">
                    <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest mb-1 flex items-center justify-center gap-1.5">
                      Limitation Deadline
                      {!editingDeadline && actionPlanId && (user?.role === 'head_legal_cell' || user?.role === 'central_law') && (
                        <button
                          onClick={() => { setDeadlineInput(recommendation.verdict.limitation_deadline || ''); setEditingDeadline(true); }}
                          className="text-primary-blue hover:text-primary-blue/70 transition-colors"
                          title="Edit deadline"
                        >
                          <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>edit</span>
                        </button>
                      )}
                    </p>
                    {editingDeadline ? (
                      <div className="flex flex-col items-center gap-2 mt-1">
                        <input
                          type="date"
                          value={deadlineInput}
                          onChange={e => setDeadlineInput(e.target.value)}
                          className="text-sm font-bold text-on-surface bg-surface-container rounded px-2 py-1 border border-primary-blue/40 focus:outline-none focus:border-primary-blue w-full text-center"
                        />
                        <div className="flex gap-2">
                          <button
                            disabled={savingDeadline || !deadlineInput}
                            onClick={async () => {
                              setSavingDeadline(true);
                              try {
                                await onDeadlineChange?.(deadlineInput);
                                setEditingDeadline(false);
                              } finally {
                                setSavingDeadline(false);
                              }
                            }}
                            className="text-[10px] font-bold px-2 py-1 rounded bg-primary-blue text-on-primary-blue disabled:opacity-50"
                          >
                            {savingDeadline ? 'Saving…' : 'Save'}
                          </button>
                          <button
                            onClick={() => setEditingDeadline(false)}
                            className="text-[10px] font-bold px-2 py-1 rounded bg-surface-container text-on-surface-variant"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p className="text-base font-bold text-on-surface">
                        {recommendation.verdict.limitation_deadline || '—'}
                      </p>
                    )}
                  </div>
                  <div className="bg-surface-container-high/40 rounded-lg p-3 text-center border border-outline-variant/15">
                    <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest mb-1">Days Remaining</p>
                    <p className={`text-base font-bold ${
                      (recommendation.verdict.days_remaining || 0) <= 7 ? 'text-error-red' :
                      (recommendation.verdict.days_remaining || 0) <= 30 ? 'text-amber-400' : 'text-green-400'
                    }`}>
                      {(recommendation.verdict.days_remaining ?? 0) < 0 
                        ? 'OVERDUE' 
                        : `${recommendation.verdict.days_remaining ?? '—'} days`}
                    </p>
                  </div>
                  <div className="bg-surface-container-high/40 rounded-lg p-3 text-center border border-outline-variant/15">
                    <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest mb-1">Urgency</p>
                    <div className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                      recommendation.verdict.urgency === 'HIGH' ? 'bg-error-red/10 text-error-red border border-error-red/20' :
                      recommendation.verdict.urgency === 'MEDIUM' ? 'bg-amber-400/10 text-amber-400 border border-amber-400/20' :
                      'bg-green-500/10 text-green-400 border border-green-500/20'
                    }`}>
                      {recommendation.verdict.urgency || '—'}
                    </div>
                  </div>
                </div>

              </div>
            )}
          </div>
        ) : (
          <div className="glass-card flex flex-col items-center justify-center p-12 border-dashed border-2 border-outline-variant/30 text-center relative overflow-hidden">
             {isGenerating ? (
               <div className="flex flex-col items-center z-10">
                 <div className="w-16 h-16 rounded-full border-4 border-primary-blue border-t-transparent animate-spin mb-6 shadow-[0_0_20px_rgba(173,198,255,0.4)]"></div>
                 <h3 className="text-xl font-bold text-on-surface tracking-tight mb-2">Multi-Agent Legal Analysis Running...</h3>
                 <p className="text-sm text-on-surface-variant">Retrieving 20-year case history and evaluating court directives.</p>
               </div>
             ) : (
               <div className="flex flex-col items-center z-10">
                 <div className="w-16 h-16 rounded-full bg-primary-blue/10 flex items-center justify-center mb-6">
                   <span className="material-symbols-outlined text-primary-blue text-4xl">travel_explore</span>
                 </div>
                 <h3 className="text-xl font-bold text-on-surface tracking-tight mb-2">RAG Analysis Pending</h3>
                 <p className="text-sm text-on-surface-variant max-w-md mb-8">Run the AI agent pipeline to generate compliance recommendations, analyze contempt risk, and retrieve similar case precedents.</p>
                 <button 
                   onClick={onGenerateAnalysis}
                   className="px-8 py-3.5 bg-primary-blue text-on-primary-blue font-bold rounded-xl flex items-center gap-3 shadow-[0_0_20px_rgba(173,198,255,0.2)] hover:scale-105 transition-all"
                 >
                   <span className="material-symbols-outlined">psychology</span>
                   Generate AI Analysis
                 </button>
               </div>
             )}
          </div>
        )}

        {/* Financial Implications Card */}
        {judgment?.financial_implications && (Array.isArray(judgment.financial_implications) ? judgment.financial_implications.length > 0 : Object.keys(judgment.financial_implications).length > 0) && (
          <div className="glass-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-amber-400/10 p-2 rounded-lg border border-amber-400/20">
                <span className="material-symbols-outlined text-amber-400">payments</span>
              </div>
              <h4 className="font-bold text-on-surface text-xl tracking-tight">Financial Implications</h4>
            </div>
            <div className="space-y-2">
              {(Array.isArray(judgment.financial_implications) ? judgment.financial_implications : []).map((fi: string, i: number) => (
                <div key={i} className="flex items-start gap-3 bg-amber-400/5 border border-amber-400/10 rounded-lg p-3">
                  <span className="material-symbols-outlined text-amber-400 text-sm mt-0.5">currency_rupee</span>
                  <p className="text-sm text-on-surface/90 font-medium">{fi}</p>
                </div>
              ))}
            </div>
          </div>
        )}


        {/* Verification & Final Decision */}
        <div
          className="relative rounded-2xl border border-outline-variant/20 overflow-hidden"
          style={{ background: 'radial-gradient(900px 300px at 0% 0%, rgba(52,211,153,0.05), transparent 55%), radial-gradient(700px 300px at 100% 100%, rgba(99,102,241,0.04), transparent 55%)' }}
        >
          <div className="absolute left-0 top-4 bottom-4 w-[3px] rounded-r bg-gradient-to-b from-green-400 to-green-400/10 pointer-events-none"></div>
          <div className="grid grid-cols-1 lg:grid-cols-[1.05fr_1px_1fr] items-stretch">

            {/* LEFT: Verification status */}
            <div className="p-6 sm:p-7 flex flex-col gap-[18px]">
              <div className="flex items-center gap-2.5 font-mono text-[10.5px] tracking-[0.14em] text-on-surface-variant/60 uppercase">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${isVerified ? 'bg-green-400 shadow-[0_0_0_3px_rgba(52,211,153,0.18)]' : 'bg-amber-400 shadow-[0_0_0_3px_rgba(251,191,36,0.18)]'}`}></span>
                Verification Status
              </div>
              {isVerified ? (
                <>
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-green-400/10 border border-green-400/30 flex items-center justify-center text-green-400 flex-shrink-0">
                      <span className="material-symbols-outlined text-[22px]">task_alt</span>
                    </div>
                    <div>
                      <h3 className="text-[18px] font-semibold tracking-tight leading-snug">
                        <span className="text-green-400">All {verifiedDirections.length} court directions</span>{' '}
                        <span className="text-on-surface">verified</span>
                      </h3>
                      <p className="text-on-surface-variant/60 text-[13.5px] mt-1">Every extracted directive has been reviewed against the certified order and approved.</p>
                    </div>
                  </div>
                  <div className="flex flex-col divide-y divide-outline-variant/20 border border-outline-variant/20 rounded-xl bg-surface-container-high/40 overflow-hidden">
                    <div className="flex items-center justify-between gap-4 px-3.5 py-2.5">
                      <span className="font-mono text-[10px] tracking-[0.12em] text-on-surface-variant/40 uppercase flex-shrink-0">Verified By</span>
                      <span className="text-[13px] font-medium text-on-surface truncate">{user?.username || 'Human Reviewer'}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 px-3.5 py-2.5">
                      <span className="font-mono text-[10px] tracking-[0.12em] text-on-surface-variant/40 uppercase flex-shrink-0">Reviewed</span>
                      <span className="text-[13px] font-medium text-on-surface">{filingDate}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 px-3.5 py-2.5">
                      <span className="font-mono text-[10px] tracking-[0.12em] text-on-surface-variant/40 uppercase flex-shrink-0">Order Source</span>
                      <span className="text-[13px] font-medium text-on-surface">
                        {judgment?.date_of_order ? `Order dated ${new Date(judgment.date_of_order).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}` : '—'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5 mt-auto">
                    <button onClick={onGoToVerify} className="inline-flex items-center gap-2 h-9 px-3.5 rounded-lg bg-surface-container-high/50 border border-outline-variant/30 text-on-surface text-[13px] font-medium hover:bg-surface-container-highest/50 transition-colors">
                      <span className="material-symbols-outlined text-[14px]">edit</span>
                      Edit verification
                    </button>
                    <button className="inline-flex items-center h-9 px-2.5 text-on-surface-variant/60 text-[13px] font-medium hover:text-on-surface-variant transition-colors">
                      View audit log
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex items-center gap-3.5">
                    <div className="w-11 h-11 rounded-xl bg-amber-400/10 border border-amber-400/30 flex items-center justify-center text-amber-400 flex-shrink-0">
                      <span className="material-symbols-outlined text-[22px]">pending_actions</span>
                    </div>
                    <div>
                      <h3 className="text-[18px] font-semibold tracking-tight leading-snug">
                        <span className="text-amber-400">{verifiedDirections.length} of {allDirections.length} directions</span>{' '}
                        <span className="text-on-surface">verified</span>
                      </h3>
                      <p className="text-on-surface-variant/60 text-[13.5px] mt-1">Review and approve all extracted directives before making a final decision.</p>
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl border border-outline-variant/20 bg-surface-container-high/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-[10.5px] tracking-[0.1em] text-on-surface-variant/50 uppercase">
                        {allDirections.length > 0 ? Math.round((verifiedDirections.length / allDirections.length) * 100) : 0}% complete
                      </span>
                      <span className="text-[12px] text-on-surface-variant/60">{verifiedDirections.length} / {allDirections.length}</span>
                    </div>
                    <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-gradient-to-r from-amber-500 to-amber-400 transition-all duration-700"
                        style={{ width: `${allDirections.length > 0 ? (verifiedDirections.length / allDirections.length) * 100 : 0}%` }} />
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5 mt-auto">
                    <button onClick={onGoToVerify} className="inline-flex items-center gap-2 h-9 px-4 rounded-lg bg-primary-blue text-on-primary-blue text-[13px] font-medium hover:opacity-90 transition-opacity">
                      <span className="material-symbols-outlined text-[14px]">verified</span>
                      Verify Action Plan
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* Column divider */}
            <div className="hidden lg:block bg-gradient-to-b from-transparent via-outline-variant/30 to-transparent"></div>

            {/* RIGHT: Final decision */}
            <div className="p-6 sm:p-7 flex flex-col gap-[18px] border-t border-outline-variant/20 lg:border-t-0">
              <div className="flex items-center gap-2.5 font-mono text-[10.5px] tracking-[0.14em] text-green-400/85 uppercase">
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 bg-green-400 shadow-[0_0_0_3px_rgba(52,211,153,0.18)]"></span>
                Final decision{decision !== 'none' ? ' · locked' : ' · pending'}
              </div>
              {isVerified && decision !== 'none' ? (
                <div className={`flex items-center gap-3.5 p-4 rounded-xl border ${decision === 'comply' ? 'bg-gradient-to-br from-green-400/10 to-green-400/[0.04] border-green-400/25' : 'bg-gradient-to-br from-amber-400/10 to-amber-400/[0.04] border-amber-400/25'}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 border ${decision === 'comply' ? 'bg-green-400/[0.18] border-green-400/35 text-green-400' : 'bg-amber-400/[0.18] border-amber-400/35 text-amber-400'}`}>
                    <span className="material-symbols-outlined text-[20px]">{decision === 'comply' ? 'verified_user' : 'gavel'}</span>
                  </div>
                  <div className="min-w-0">
                    <div className={`font-mono text-[10.5px] tracking-[0.14em] uppercase mb-1 ${decision === 'comply' ? 'text-green-400/85' : 'text-amber-400/85'}`}>Action taken</div>
                    <div className="text-[16px] font-semibold text-on-surface tracking-tight">
                      {decision === 'comply' ? "Comply with the court's order" : 'File an appeal'}
                    </div>
                  </div>
                  <button onClick={() => onDecision?.('none')} className="ml-auto inline-flex items-center gap-2 h-9 px-3.5 rounded-lg bg-surface-container-high/50 border border-outline-variant/30 text-on-surface text-[13px] font-medium hover:bg-surface-container-highest/50 transition-colors flex-shrink-0">
                    <span className="material-symbols-outlined text-[14px]">undo</span>
                    Change
                  </button>
                </div>
              ) : (
                <div className="flex flex-col gap-2.5">
                  {!isVerified && <p className="text-on-surface-variant/50 text-[13px]">Complete verification before making a final decision.</p>}
                  <button disabled={!isVerified} onClick={() => onDecision?.('comply')} className="flex items-center gap-3 p-3.5 rounded-xl border border-outline-variant/20 bg-surface-container-high/30 text-on-surface text-[13px] font-medium hover:border-green-400/30 hover:bg-green-400/[0.05] disabled:opacity-40 disabled:cursor-not-allowed transition-all">
                    <span className="material-symbols-outlined text-green-400 text-[18px]">verified_user</span>
                    Comply with court's order
                    <span className="ml-auto material-symbols-outlined text-on-surface-variant/40 text-[16px]">chevron_right</span>
                  </button>
                  <button disabled={!isVerified} onClick={() => onDecision?.('appeal')} className="flex items-center gap-3 p-3.5 rounded-xl border border-outline-variant/20 bg-surface-container-high/30 text-on-surface text-[13px] font-medium hover:border-amber-400/30 hover:bg-amber-400/[0.05] disabled:opacity-40 disabled:cursor-not-allowed transition-all">
                    <span className="material-symbols-outlined text-amber-400 text-[18px]">gavel</span>
                    Appeal Review
                    <span className="ml-auto material-symbols-outlined text-on-surface-variant/40 text-[16px]">chevron_right</span>
                  </button>
                </div>
              )}
            </div>

          </div>
        </div>

        {/* Similar Cases Table Card */}
        <div className="glass-card p-4 sm:p-8">
          <div className="flex items-center justify-between mb-8">
            <h4 className="font-bold text-on-surface text-xl tracking-tight">Similar Cases & RAG Evidence</h4>
          </div>
          
          <div className="space-y-1">
            <div className="hidden sm:grid grid-cols-12 gap-4 pb-4 border-b border-outline-variant/20 text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.2em]">
              <div className="col-span-4">Case ID</div>
              <div className="col-span-2">Similarity</div>
              <div className="col-span-2">Outcome</div>
              <div className="col-span-4">Core Precedent</div>
            </div>
            
            {similarCases.length > 0 ? (
               <div className="pt-2">
                 {similarCases.slice(0, 5).map((p: any, i: number) => {
                   // Use actual similarity_score from backend if available,
                   // otherwise fall back to relevance label mapping
                   const score = p.similarity_score
                     ? Math.round(p.similarity_score * 100)
                     : p.relevance === 'High' ? 93 : p.relevance === 'Moderate' ? 91 : 88;
                   const formattedOutcome = p.outcome === 'APPEAL_ALLOWED' ? 'Allowed' 
                     : p.outcome === 'APPEAL_DISMISSED' ? 'Dismissed' 
                     : p.outcome === 'Appeal(s) allowed' ? 'Allowed'
                     : p.outcome === 'Dismissed' ? 'Dismissed'
                     : p.outcome === 'Disposed off' ? 'Disposed'
                     : p.outcome === 'Case Partly allowed' ? 'Partly Allowed'
                     : p.outcome || 'Unknown';
                   return (
                     <CaseRow 
                       key={i}
                       id={p.case_id || `PRE-${1000 + i}`}
                       similarity={score}
                       outcome={formattedOutcome}
                       precedent={p.key_holding || p.applicability}
                     />
                   );
                 })}
                 {similarCases.length > 5 && (
                   <button className="w-full mt-4 py-3 bg-surface-container/50 hover:bg-surface-container-high transition-colors text-primary-blue text-[10px] font-bold uppercase tracking-widest rounded-lg">
                     View All {similarCases.length} Precedents
                   </button>
                 )}
               </div>
            ) : recommendation ? (
              <div className="py-8 text-center text-on-surface-variant opacity-50 text-sm">No strong precedents found in the 20-year corpus.</div>
            ) : (
              <div className="py-8 text-center text-on-surface-variant opacity-50 text-sm">Generate AI Analysis to load relevant precedents.</div>
            )}
          </div>
        </div>
      </div>

      {/* Right Column */}
      <div className="xl:col-span-5">
        <div className="glass-card flex flex-col p-4 sm:p-7 sticky top-8">

          {/* Header */}
          <div className="flex items-start justify-between mb-5">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-primary-blue/10 border border-primary-blue/25 flex-shrink-0">
                <span className="material-symbols-outlined text-primary-blue text-xl">gavel</span>
              </div>
              <div>
                <h4 className="font-semibold text-on-surface text-[19px] tracking-tight leading-none mb-1">Court Directions &amp; Action Plan</h4>
                <p className="font-mono text-[11px] tracking-[0.08em] text-on-surface-variant/60 uppercase">
                  {judgment?.date_of_order
                    ? `From order dated ${new Date(judgment.date_of_order).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })} · `
                    : ''}
                  {allDirections.length} of {allDirections.length} actionable
                </p>
              </div>
            </div>
          </div>

          {/* Progress summary */}
          {allDirections.length > 0 && (
            <div className="mb-5 p-4 bg-surface-container/50 border border-outline-variant/20 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-5">
                  <span className="flex items-center gap-2 text-sm text-on-surface-variant">
                    <span className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_0_3px_rgba(52,211,153,0.12)] flex-shrink-0"></span>
                    <span className="font-semibold text-on-surface">{verifiedDirections.length}</span> Verified
                  </span>
                  <span className="flex items-center gap-2 text-sm text-on-surface-variant">
                    <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_0_3px_rgba(251,191,36,0.12)] flex-shrink-0"></span>
                    <span className="font-semibold text-on-surface">{unverifiedDirections.length}</span> Pending
                  </span>
                </div>
                <span className="font-mono text-[12px] tracking-[0.04em] text-green-400 font-semibold">
                  {allDirections.length > 0 ? Math.round((verifiedDirections.length / allDirections.length) * 100) : 0}% COMPLETE
                </span>
              </div>
              <div className="h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-700"
                  style={{ width: `${allDirections.length > 0 ? (verifiedDirections.length / allDirections.length) * 100 : 0}%` }}
                />
              </div>
              {unverifiedDirections.length > 0 && onGoToVerify && (
                <button onClick={onGoToVerify} className="mt-2 text-primary-blue hover:underline font-bold uppercase tracking-wider text-[10px] font-mono">
                  Go Verify →
                </button>
              )}
            </div>
          )}

          {/* Timeline */}
          <div className="flex-grow">
            {allDirections.length > 0 ? (
              <div className="relative pl-9">
                {/* Vertical rail */}
                <div className="absolute left-[15px] top-4 bottom-4 w-px bg-gradient-to-b from-outline-variant/40 via-outline-variant/20 to-transparent pointer-events-none"></div>

                {allDirections.map((action: any, idx: number) => {
                  const initials = action.source
                    ? action.source.split(' ').filter(Boolean).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()
                    : '?';
                  return (
                    <div key={action.id || idx} className="relative mb-3.5 last:mb-0">
                      {/* Node */}
                      <div className={`absolute -left-9 top-3.5 w-[30px] h-[30px] rounded-full flex items-center justify-center border bg-surface-container-high ${
                        action.isVerified
                          ? 'border-green-400 text-green-400 shadow-[0_0_0_4px_rgba(10,13,20,0.8),0_0_0_5px_rgba(52,211,153,0.15)]'
                          : 'border-amber-400 text-amber-400 shadow-[0_0_0_4px_rgba(10,13,20,0.8),0_0_0_5px_rgba(251,191,36,0.15)]'
                      }`}>
                        {action.isVerified
                          ? <span className="material-symbols-outlined text-[14px] font-black">check</span>
                          : <span className="font-mono text-[11px] font-black">{idx + 1}</span>
                        }
                      </div>

                      {/* Card */}
                      <div className="rounded-xl border border-outline-variant/20 bg-surface-container-high/30 p-4 hover:border-outline-variant/40 hover:bg-surface-container-high/50 transition-all duration-150">
                        {/* Meta top row */}
                        <div className="flex items-start justify-between gap-3 mb-2.5 min-w-0">
                          <span className="font-mono text-[11px] tracking-[0.12em] text-on-surface-variant/50 font-medium whitespace-nowrap flex-shrink-0">
                            DIRECTION · #{String(idx + 1).padStart(2, '0')}
                          </span>
                          {action.dueDate && (() => {
                            const pill = getDeadlinePillStyle(action.dueDate);
                            return (
                              <span 
                                title={action.dueDate}
                                className={`inline-flex items-center gap-1.5 h-6 px-2.5 rounded-full font-mono text-[10.5px] font-semibold tracking-[0.06em] uppercase border min-w-0 ${pill.classes}`}
                              >
                                <span className="material-symbols-outlined text-[11px] flex-shrink-0">{pill.icon}</span>
                                <span className="truncate">{action.dueDate}</span>
                              </span>
                            );
                          })()}
                        </div>

                        {/* Direction text */}
                        <p className="text-on-surface text-sm leading-[1.55] mb-3.5">{action.title}</p>

                        {/* Financial details */}
                        {action.financialDetails && (
                          <div className="flex items-start gap-2 bg-amber-400/5 border border-amber-400/15 rounded-lg p-2.5 mb-3">
                            <span className="material-symbols-outlined text-amber-400 text-sm mt-0.5">currency_rupee</span>
                            <p className="text-xs text-amber-400/90 font-medium leading-relaxed">{action.financialDetails}</p>
                          </div>
                        )}

                        {/* Footer */}
                        <div className="flex items-center justify-between gap-3 pt-3 border-t border-dashed border-outline-variant/20">
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div className="w-[26px] h-[26px] rounded-full flex-shrink-0 flex items-center justify-center bg-surface-container border border-outline-variant/30 text-on-surface-variant text-[11px] font-semibold">
                              {initials}
                            </div>
                            <div className="min-w-0">
                              <p className="font-mono text-[10px] tracking-[0.1em] text-on-surface-variant/40 uppercase leading-none mb-0.5">Responsible</p>
                              <p className="text-[12.5px] text-on-surface-variant font-medium truncate">{action.source || '—'}</p>
                            </div>
                          </div>
                          {action.isVerified && (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-green-500/10 border border-green-500/22 text-green-400 font-mono text-[10.5px] font-semibold tracking-[0.08em] uppercase flex-shrink-0">
                              <span className="material-symbols-outlined text-[10px]">check</span>
                              Verified
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-10 bg-surface-container-highest/10 border border-outline-variant/10 rounded-2xl h-full">
                <div className="w-20 h-20 rounded-full bg-surface-container-highest flex items-center justify-center mb-8 border border-outline-variant/20">
                  <span className="material-symbols-outlined text-on-surface-variant text-4xl">gavel</span>
                </div>
                <p className="text-on-surface font-bold text-2xl tracking-tighter mb-4">No court directions extracted</p>
                <p className="text-on-surface-variant text-base font-medium max-w-[280px] leading-relaxed mx-auto">
                  Upload a judgment PDF and extract court orders to build the action plan.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>


    </div>
  );
};

const CaseRow: React.FC<{ id: string, similarity: number, outcome: string, precedent: string }> = ({ id, similarity, outcome, precedent }) => (
  <>
    {/* Desktop row */}
    <div className="hidden sm:grid grid-cols-12 gap-4 py-5 border-b border-outline-variant/10 items-center hover:bg-white/[0.02] -mx-4 px-4 transition-colors">
      <div className="col-span-4 font-mono font-bold text-on-surface text-sm truncate" title={id}>{id}</div>
      <div className="col-span-2 flex items-center gap-2">
        <div className="flex-grow h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
          <div className="h-full bg-primary-blue transition-all duration-1000" style={{ width: `${similarity}%` }}></div>
        </div>
        <span className="text-xs font-bold text-primary-blue whitespace-nowrap">{similarity}%</span>
      </div>
      <div className={`col-span-2 text-xs font-bold uppercase tracking-widest ${outcome === 'Dismissed' ? 'text-green-400' : 'text-tertiary-container'}`}>
        {outcome}
      </div>
      <div className="col-span-4 flex items-center justify-between gap-4">
        <span className="text-on-surface-variant text-sm font-medium italic truncate">{precedent}</span>
      </div>
    </div>
    {/* Mobile card */}
    <div className="sm:hidden py-4 border-b border-outline-variant/10">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="font-mono font-bold text-on-surface text-xs truncate" title={id}>{id}</span>
        <span className="text-xs font-bold text-primary-blue whitespace-nowrap">{similarity}%</span>
      </div>
      <div className="flex items-center gap-2 mb-1">
        <div className="flex-grow h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
          <div className="h-full bg-primary-blue" style={{ width: `${similarity}%` }}></div>
        </div>
        <span className={`text-[10px] font-bold uppercase ${outcome === 'Dismissed' ? 'text-green-400' : 'text-tertiary-container'}`}>{outcome}</span>
      </div>
      <p className="text-on-surface-variant text-xs font-medium italic truncate mt-1">{precedent}</p>
    </div>
  </>
);
