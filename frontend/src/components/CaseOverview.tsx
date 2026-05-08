import React, { useState } from 'react';
import { motion } from 'motion/react';
import { CaseData } from '../api/client';

const ExpandableText = ({ text, maxLines = 3 }: { text: string, maxLines?: number }) => {
  const [expanded, setExpanded] = useState(false);
  if (!text) return <span className="opacity-50 italic">Not extracted</span>;
  
  return (
    <div className="relative">
      <div className={`text-sm leading-relaxed ${expanded ? '' : `line-clamp-${maxLines}`}`}>
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

const DetailItem = ({ label, value }: { label: string; value: string }) => (
  <div className="flex flex-col gap-2">
    <span className="text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.15em] border-b border-outline-variant/10 pb-2">
      {label}
    </span>
    <span className="text-on-surface font-semibold text-base tracking-tight">
      {value}
    </span>
  </div>
);

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
  onGenerateAnalysis
}: { 
  caseData?: CaseData | null, 
  verifiedActions?: any[], 
  onGoToVerify?: () => void,
  recommendation?: any | null,
  isGenerating?: boolean,
  onGenerateAnalysis?: () => void
}) => {
  const judgment = caseData?.judgments?.[0];
  const filingDate = caseData?.created_at
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
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 py-8">
      {/* Left Column */}
      <div className="xl:col-span-7 space-y-8">
        
        {/* Case Details Card */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-4 mb-8">
            <div className="bg-secondary-container/40 p-2.5 rounded-lg border border-outline-variant/20">
              <span className="material-symbols-outlined text-primary-blue">description</span>
            </div>
            <h4 className="font-bold text-on-surface text-xl tracking-tight">Case Details</h4>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">
            <DetailItem label="Jurisdiction" value={caseData?.court_name || '—'} />
            <DetailItem label="Bench" value={judgment?.presiding_judges?.join(', ') || '—'} />
            <DetailItem label="Filing Date" value={filingDate} />
            <DetailItem label="Case Type" value={caseData?.case_type || '—'} />
            <DetailItem label="Area of Law" value={caseData?.area_of_law || '—'} />
            <DetailItem label="Primary Statute" value={caseData?.primary_statute || '—'} />
          </div>
        </div>

        {/* Executive Case Brief Card */}
        <div className="glass-card p-8 border-l-4 border-l-primary-blue relative overflow-hidden group">
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
          <div className="glass-card flex flex-col gap-6 p-8 border border-primary-blue/30 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary-blue/10 rounded-full blur-[50px]"></div>
            
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-primary-blue/20 border border-primary-blue/30 flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary-blue text-3xl">smart_toy</span>
                </div>
                <div>
                  <h2 className="text-on-surface text-2xl font-bold tracking-tight mb-1 flex items-center gap-3">
                    AI Verdict: <span className={aiVerdict === 'COMPLY' ? 'text-green-400' : 'text-amber-400'}>{aiVerdict}</span>
                  </h2>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-primary-blue bg-primary-blue/10 px-2 py-0.5 rounded">
                    {confidence}% Confidence
                  </span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-3">
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
            
            {/* Primary reasoning removed per user request (redundant with appeal grounds) */}
            {recommendation.appeal_grounds && recommendation.appeal_grounds.length > 0 && (
               <div>
                 <h4 className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2">Appeal Grounds</h4>
                 <ul className="list-disc pl-5 text-sm space-y-1 text-amber-400/90">
                   {recommendation.appeal_grounds.map((g: string, i: number) => <li key={i}>{g}</li>)}
                 </ul>
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
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-surface-container-high/40 rounded-lg p-3 text-center border border-outline-variant/15">
                    <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-widest mb-1">Limitation Deadline</p>
                    <p className="text-base font-bold text-on-surface">
                      {recommendation.verdict.limitation_deadline || '—'}
                    </p>
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
                {/* Urgency heatmap bar */}
                <div className="mt-4">
                  <div className="flex justify-between text-[8px] font-bold uppercase tracking-widest text-on-surface-variant mb-1">
                    <span>Urgent</span><span>Safe</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-container-highest overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-1000 ${
                        (recommendation.verdict.days_remaining || 0) <= 7 ? 'bg-gradient-to-r from-red-500 to-red-400' :
                        (recommendation.verdict.days_remaining || 0) <= 30 ? 'bg-gradient-to-r from-amber-500 to-amber-400' :
                        'bg-gradient-to-r from-green-500 to-green-400'
                      }`}
                      style={{ width: `${Math.max(5, Math.min(100, 100 - ((recommendation.verdict.days_remaining || 0) / 90) * 100))}%` }}
                    />
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

        {/* Verification Alert Card - Only show if not verified */}
        {!isVerified && (
          <div className="bg-surface-container-highest/20 border border-outline-variant/30 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <span className="material-symbols-outlined text-primary-blue mt-1">info</span>
              <div>
                <p className="text-on-surface font-bold text-lg tracking-tight mb-1 uppercase text-sm">Verification Required</p>
                <p className="text-on-surface-variant text-sm">
                  You must verify compliance actions generated before you can comply/choose to appeal.
                </p>
              </div>
            </div>
            <button 
              onClick={onGoToVerify}
              className="whitespace-nowrap px-8 py-3.5 bg-primary-blue text-on-primary-blue font-bold rounded-xl flex items-center gap-3 shadow-[0_0_20px_rgba(173,198,255,0.2)] hover:shadow-[0_0_30px_rgba(173,198,255,0.4)] transition-all transform hover:-translate-y-0.5"
            >
              <span className="material-symbols-outlined">verified</span>
              Verify Action Plan
            </button>
          </div>
        )}

        {/* Verified Status Card - Show when verified */}
        {isVerified && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-6 flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-green-400">task_alt</span>
            </div>
            <div>
              <p className="text-green-400 font-bold text-lg tracking-tight">All Court Directions Verified</p>
              <p className="text-on-surface-variant text-sm">All extracted directives have been reviewed and approved. Verified actions are now visible in the dashboard.</p>
            </div>
          </div>
        )}

        {/* Similar Cases Table Card */}
        <div className="glass-card p-8">
          <div className="flex items-center justify-between mb-8">
            <h4 className="font-bold text-on-surface text-xl tracking-tight">Similar Cases & RAG Evidence</h4>
          </div>
          
          <div className="space-y-1">
            <div className="grid grid-cols-12 gap-4 pb-4 border-b border-outline-variant/20 text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.2em]">
              <div className="col-span-3">Case ID</div>
              <div className="col-span-3">Similarity</div>
              <div className="col-span-2">Outcome</div>
              <div className="col-span-4 text-right sm:text-left">Core Precedent</div>
            </div>
            
            {similarCases.length > 0 ? (
               <div className="pt-2">
                 {similarCases.slice(0, 5).map((p: any, i: number) => {
                   const score = p.relevance === 'High' ? 90 : p.relevance === 'Moderate' ? 75 : 55;
                   const formattedOutcome = p.outcome === 'APPEAL_ALLOWED' ? 'Allowed' : p.outcome === 'APPEAL_DISMISSED' ? 'Dismissed' : p.outcome;
                   return (
                     <CaseRow 
                       key={i}
                       id={p.case_id || `PRE-${1000 + i}`}
                       similarity={score - i}
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
      <div className="xl:col-span-5 h-full">
        <div className="glass-card flex flex-col h-full min-h-[600px] p-8">
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-secondary-container/30 p-2.5 rounded-xl border border-outline-variant/20">
              <span className="material-symbols-outlined text-on-surface-variant">gavel</span>
            </div>
            <h4 className="font-bold text-on-surface text-xl tracking-tight">Court Directions & Action Plan</h4>
          </div>

          {/* Summary badge */}
          <div className="flex items-center gap-3 mb-6 text-xs">
            <span className="px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 font-bold">
              {verifiedDirections.length} Verified
            </span>
            <span className="px-2 py-0.5 rounded-full bg-amber-400/10 border border-amber-400/20 text-amber-400 font-bold">
              {unverifiedDirections.length} Pending
            </span>
            {unverifiedDirections.length > 0 && onGoToVerify && (
              <button onClick={onGoToVerify} className="text-primary-blue hover:underline font-bold uppercase tracking-wider text-[10px]">
                Go Verify →
              </button>
            )}
          </div>
          
          <div className="flex-grow">
            {allDirections.length > 0 ? (
              <div className="space-y-6">
                {allDirections.map((action: any, idx: number) => (
                  <div key={action.id || idx} className="relative pl-8">
                    {idx !== allDirections.length - 1 && (
                      <div className="absolute left-[11px] top-8 bottom-[-24px] w-0.5 bg-outline-variant/20"></div>
                    )}
                    <div className={`absolute left-0 top-1.5 w-6 h-6 rounded-full flex items-center justify-center shadow-[0_0_10px_rgba(173,198,255,0.4)] ${
                      action.isVerified 
                        ? 'bg-green-500' 
                        : 'bg-amber-400/80'
                    }`}>
                      {action.isVerified 
                        ? <span className="material-symbols-outlined text-white text-[14px]">check</span>
                        : <span className="text-[10px] text-white font-black">{idx + 1}</span>
                      }
                    </div>
                    <div className={`border rounded-xl p-4 ${
                      action.isVerified 
                        ? 'bg-green-500/5 border-green-500/20' 
                        : 'bg-surface-container-high/40 border-outline-variant/20'
                    }`}>
                      <div className="flex justify-between items-start mb-2">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <h5 className="font-bold text-on-surface text-sm tracking-tight">{action.title}</h5>
                            <span className={`text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                              action.isVerified 
                                ? 'bg-green-500/10 text-green-400 border border-green-500/20' 
                                : 'bg-amber-400/10 text-amber-400 border border-amber-400/20'
                            }`}>
                              {action.isVerified ? '✓ Verified' : 'Pending Verification'}
                            </span>
                          </div>
                          {action.source && (
                            <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">
                              Responsible: {action.source}
                            </p>
                          )}
                        </div>
                        {action.dueDate && (
                          <span className="text-[9px] font-bold text-error-red bg-error-red/10 px-2 py-0.5 rounded uppercase">{action.dueDate}</span>
                        )}
                      </div>
                      {action.financialDetails && (
                        <div className="flex items-start gap-2 bg-amber-400/5 border border-amber-400/15 rounded-lg p-3 mt-3">
                          <span className="material-symbols-outlined text-amber-400 text-sm mt-0.5">currency_rupee</span>
                          <p className="text-xs text-amber-400/90 font-medium leading-relaxed">{action.financialDetails}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
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

const CaseRow = ({ id, similarity, outcome, precedent }: { id: string, similarity: number, outcome: string, precedent: string }) => (
  <div className="grid grid-cols-12 gap-4 py-5 border-b border-outline-variant/10 items-center hover:bg-white/[0.02] -mx-4 px-4 transition-colors">
    <div className="col-span-3 font-mono font-bold text-on-surface text-base">{id}</div>
    <div className="col-span-3 flex items-center gap-3">
      <div className="flex-grow h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
        <div className="h-full bg-primary-blue transition-all duration-1000" style={{ width: `${similarity}%` }}></div>
      </div>
      <span className="text-xs font-bold text-primary-blue">{similarity}%</span>
    </div>
    <div className={`col-span-2 text-xs font-bold uppercase tracking-widest ${outcome === 'Dismissed' ? 'text-green-400' : 'text-tertiary-container'}`}>
      {outcome}
    </div>
    <div className="col-span-4 flex items-center justify-between gap-4">
      <span className="text-on-surface-variant text-sm font-medium italic truncate">{precedent}</span>
    </div>
  </div>
);
