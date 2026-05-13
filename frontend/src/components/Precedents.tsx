import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
const PrecedentCard = ({ 
  id, 
  title, 
  description, 
  matchScore, 
  outcome, 
  court, 
  year, 
  borderClass, 
  scoreColor,
  evidenceType = 'RAG',
  evidencePoints = []
}: any) => {
  return (
    <motion.article 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-surface-container/40 backdrop-blur-md rounded-2xl p-6 border-l-4 ${borderClass} border-outline-variant/20 hover:bg-surface-container-high/60 transition-all group relative overflow-hidden`}
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary-blue/5 rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-primary-blue/10 transition-colors"></div>
      
      <div className="flex flex-col md:flex-row gap-8 relative z-10">
        {/* Left: Score & Meta */}
        <div className="w-full md:w-48 shrink-0 flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-end">
              <span className={`text-4xl font-black ${scoreColor}`}>{matchScore}%</span>
              <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest mb-1">Match</span>
            </div>
            <div className="h-2 w-full bg-surface-dim rounded-full overflow-hidden border border-outline-variant/10">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${matchScore}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
                className={`h-full ${scoreColor.replace('text-', 'bg-')} shadow-[0_0_15px_rgba(173,198,255,0.4)]`}
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className={`px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-wider border ${
              outcome === 'Upheld' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 
              outcome === 'Dismissed' ? 'bg-error-red/10 text-error-red border-error-red/20' : 
              'bg-amber-400/10 text-amber-400 border-amber-400/20'
            }`}>
              {outcome}
            </span>
            <span className="px-2 py-1 rounded-lg bg-surface-dim border border-outline-variant/30 text-on-surface-variant text-[9px] font-black uppercase tracking-wider">
              {court}
            </span>
            <span className="px-2 py-1 rounded-lg bg-surface-dim border border-outline-variant/30 text-on-surface-variant text-[9px] font-black uppercase tracking-wider">
              {year}
            </span>
          </div>
        </div>

        {/* Right: Case Details */}
        <div className="flex-1 flex flex-col gap-5">
          <div>
            <h3 className="font-bold text-on-surface text-lg group-hover:text-primary-blue transition-colors cursor-pointer">{id}: {title}</h3>
            <p className="text-sm text-on-surface-variant leading-relaxed mt-2 line-clamp-2">{description}</p>
          </div>

          <div className="bg-surface-dim/50 rounded-xl p-5 border border-outline-variant/10">
            <h4 className={`text-[10px] font-black uppercase tracking-[0.2em] mb-4 flex items-center gap-2 ${scoreColor}`}>
              <span className="material-symbols-outlined text-sm">
                {evidenceType === 'RAG' ? 'psychology' : 'policy'}
              </span>
              AI {evidenceType} Evidence
            </h4>
            
            {evidencePoints.length > 0 ? (
              <ul className="space-y-3">
                {evidencePoints.map((point: string, idx: number) => (
                  <li key={idx} className="text-xs text-on-surface-variant flex items-start gap-3">
                    <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${scoreColor.replace('text-', 'bg-')}`}></span>
                    <span dangerouslySetInnerHTML={{ __html: point }} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-on-surface-variant italic leading-relaxed">
                Analysis suggests a divergence in judicial interpretation regarding physical hardware requirements vs software logic.
              </p>
            )}
          </div>

        </div>
      </div>
    </motion.article>
  );
};

export const Precedents = ({ 
  recommendation,
  isGenerating,
  onGenerateAnalysis
}: { 
  recommendation?: any | null,
  isGenerating?: boolean,
  onGenerateAnalysis?: () => void
}) => {
  const precedents = recommendation?.agent_outputs?.precedents || [];

  return (
    <div className="flex flex-col lg:flex-row gap-10 py-8">
      {/* Main content */}
      <div className="flex-1 flex flex-col gap-8">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-on-surface tracking-tight flex items-center gap-3">
            <div className="p-2 bg-primary-blue/10 rounded-lg">
              <span className="material-symbols-outlined text-primary-blue">library_books</span>
            </div>
            Similar Cases & RAG Evidence
          </h2>
          <div className="flex items-center gap-3">
            {isGenerating && <span className="text-primary-blue text-xs animate-pulse">Running AI Inference (Llama 70B)...</span>}
            <span className="text-[10px] font-black uppercase tracking-widest text-on-surface-variant">Sort by:</span>
            <select className="bg-surface-container/50 border border-outline-variant/30 rounded-lg px-3 py-1.5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest outline-none focus:border-primary-blue/50">
              <option>Similarity Score</option>
              <option>Recent</option>
              <option>Authority level</option>
            </select>
          </div>
        </div>

        <div className="space-y-6">
          {!recommendation ? (
            <div className="flex flex-col items-center justify-center p-12 border-dashed border-2 border-outline-variant/30 rounded-2xl text-center">
              {isGenerating ? (
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 rounded-full border-4 border-primary-blue border-t-transparent animate-spin mb-6"></div>
                  <h3 className="text-xl font-bold text-on-surface tracking-tight mb-2">Analyzing 20-Year Case History...</h3>
                  <p className="text-sm text-on-surface-variant">Retrieving similar precedents and generating legal risk evidence.</p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <span className="material-symbols-outlined text-5xl text-primary-blue/50 mb-4">search</span>
                  <h3 className="text-xl font-bold text-on-surface tracking-tight mb-2">Precedent Analysis Pending</h3>
                  <p className="text-sm text-on-surface-variant max-w-md mb-6">Generate AI Analysis to load matching precedents and similarity scores.</p>
                  <button 
                    onClick={onGenerateAnalysis}
                    className="px-6 py-2.5 bg-primary-blue text-on-primary-blue font-bold rounded-lg flex items-center gap-2"
                  >
                    Generate AI Analysis
                  </button>
                </div>
              )}
            </div>
          ) : precedents.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-center opacity-50 border-dashed border-2 border-outline-variant/30 rounded-2xl">
               <span className="material-symbols-outlined text-4xl mb-2">not_listed_location</span>
               <p className="font-bold">No strong precedents found.</p>
            </div>
          ) : (
            <>
              {recommendation && recommendation.verdict && (() => {
                const ao = recommendation.agent_outputs || {};
                const precedentStrength = ao.precedent_strength || 'WEAK';
                const balanceAssessment = ao.balance_assessment || 'BALANCED';
                const contemptUrgency = ao.contempt_urgency || 'LOW';
                return (
                  <div className="space-y-4 mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Agent 1: Precedent Research */}
                      <div className="p-4 bg-surface-container/60 border border-outline-variant/20 rounded-xl flex flex-col gap-2">
                        <p className="text-[9px] font-black uppercase tracking-widest text-on-surface-variant flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm">psychology</span> Agent 1 · Precedent Research
                        </p>
                        <span className={`self-start px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                          precedentStrength === 'STRONG' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                          precedentStrength === 'MODERATE' ? 'bg-amber-400/10 text-amber-400 border-amber-400/20' :
                          'bg-error-red/10 text-error-red border-error-red/20'
                        }`}>{precedentStrength}</span>
                        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-3">
                          {ao.overall_trend || 'No trend data available.'}
                        </p>
                      </div>
                      {/* Agent 2: Argument Balance */}
                      <div className="p-4 bg-surface-container/60 border border-outline-variant/20 rounded-xl flex flex-col gap-2">
                        <p className="text-[9px] font-black uppercase tracking-widest text-on-surface-variant flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm">balance</span> Agent 2 · Argument Balance
                        </p>
                        <span className={`self-start px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                          balanceAssessment === 'APPEAL_FAVORED' ? 'bg-amber-400/10 text-amber-400 border-amber-400/20' :
                          balanceAssessment === 'COMPLIANCE_FAVORED' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                          'bg-primary-blue/10 text-primary-blue border-primary-blue/20'
                        }`}>{balanceAssessment.replace(/_/g, ' ')}</span>
                        {ao.strongest_appeal_ground && (
                          <p className="text-xs text-on-surface-variant line-clamp-2 leading-relaxed">
                            <span className="text-amber-400 font-bold">Appeal: </span>{ao.strongest_appeal_ground}
                          </p>
                        )}
                        {ao.strongest_compliance_reason && (
                          <p className="text-xs text-on-surface-variant line-clamp-2 leading-relaxed">
                            <span className="text-green-400 font-bold">Comply: </span>{ao.strongest_compliance_reason}
                          </p>
                        )}
                      </div>
                      {/* Agent 3: Risk Audit */}
                      <div className="p-4 bg-surface-container/60 border border-outline-variant/20 rounded-xl flex flex-col gap-2">
                        <p className="text-[9px] font-black uppercase tracking-widest text-on-surface-variant flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm">warning</span> Agent 3 · Risk Audit
                        </p>
                        <span className={`self-start px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                          contemptUrgency === 'HIGH' ? 'bg-error-red/10 text-error-red border-error-red/20' :
                          contemptUrgency === 'MEDIUM' ? 'bg-amber-400/10 text-amber-400 border-amber-400/20' :
                          'bg-green-500/10 text-green-400 border-green-500/20'
                        }`}>Contempt: {contemptUrgency}</span>
                        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-3">
                          {ao.limitation_analysis || ao.contempt_risk_assessment || 'No risk data available.'}
                        </p>
                      </div>
                    </div>
                    {/* Decision strip */}
                    <div className="flex flex-wrap gap-3">
                      <span className="px-3 py-1 bg-surface-dim rounded-lg text-xs font-bold border border-outline-variant/30 text-on-surface">
                        Decision: <span className="text-primary-blue">{recommendation.verdict.decision}</span>
                      </span>
                      <span className="px-3 py-1 bg-surface-dim rounded-lg text-xs font-bold border border-outline-variant/30 text-on-surface">
                        Cases analysed: <span className="text-amber-400">{recommendation.statistical_basis?.similar_cases_analyzed || 0}</span>
                      </span>
                      {(ao.pro_appeal_count > 0 || ao.pro_compliance_count > 0) && (
                        <span className="px-3 py-1 bg-surface-dim rounded-lg text-xs font-bold border border-outline-variant/30 text-on-surface">
                          <span className="text-amber-400">{ao.pro_appeal_count}</span> appeal grounds ·{' '}
                          <span className="text-green-400">{ao.pro_compliance_count}</span> compliance reasons
                        </span>
                      )}
                    </div>
                  </div>
                );
              })()}
              {/* Build Agent 1 analysis lookup: case_id → {key_holding, relevance, applicability} */}
              {(() => {
                const agent1Map: Record<string, any> = {};
                (recommendation?.agent_outputs?.precedents || []).forEach((ap: any) => {
                  if (ap.case_id) agent1Map[ap.case_id] = ap;
                });

                const displayList = recommendation?.agent_outputs?.rag_precedents?.length
                  ? recommendation.agent_outputs.rag_precedents
                  : precedents;

                return displayList.map((p: any, i: number) => {
                  const isAllowed = p.outcome?.toLowerCase().includes('allow') || p.outcome?.toLowerCase().includes('upheld');
                  const score = p.similarity_score
                    ? Math.round(p.similarity_score * 100)
                    : p.relevance === 'High' ? 90 : p.relevance === 'Moderate' ? 75 : 55;

                  // Only accept years 1900-2099 — avoids "0100" from bad metadata
                  const yearFromMeta = /^(19|20)\d{2}$/.test(p.year || '') ? p.year : null;
                  const yearFromId = p.case_id?.match(/\b(19|20)\d{2}\b/)?.[0] ?? null;
                  const year: string = yearFromMeta || yearFromId || '';

                  const courtName = p.court && p.court !== 'Unknown' ? p.court : 'Supreme Court';
                  const formattedOutcome =
                    p.outcome === 'APPEAL_ALLOWED' || p.outcome === 'Appeal(s) allowed' ? 'Allowed' :
                    p.outcome === 'APPEAL_DISMISSED' || p.outcome === 'Dismissed' ? 'Dismissed' :
                    p.outcome === 'Disposed off' ? 'Disposed' :
                    p.outcome === 'Case Partly allowed' ? 'Partly Allowed' :
                    p.outcome || 'Unknown';

                  // Agent 1 LLM analysis for this case (available in 4-agent mode)
                  const a1 = agent1Map[p.case_id] || null;
                  const aiRelevance: string | null = a1?.relevance || null;
                  const aiKeyHolding: string | null = a1?.key_holding || null;
                  const aiApplicability: string | null = a1?.applicability || null;

                  // Description: prefer AI relevance explanation (why it's similar), else short raw excerpt
                  const rawExcerpt = p.key_holding ? p.key_holding.substring(0, 150) + (p.key_holding.length > 150 ? '...' : '') : '';
                  const description = aiRelevance || rawExcerpt;

                  const partyLine = (p.petitioner || p.respondent)
                    ? `${p.petitioner || ''}${p.petitioner && p.respondent ? ' v. ' : ''}${p.respondent || ''}`
                    : null;

                  // Evidence points: show AI analysis when available, else raw chunk (never duplicate description)
                  const evidencePoints: string[] = [
                    aiKeyHolding
                      ? `<span class="font-semibold text-on-surface/90">Key Holding:</span> ${aiKeyHolding.substring(0, 260)}${aiKeyHolding.length > 260 ? '...' : ''}`
                      : (p.key_holding ? p.key_holding.substring(0, 260) + (p.key_holding.length > 260 ? '...' : '') : null),
                    aiApplicability
                      ? `<span class="font-semibold text-on-surface/90">AI Analysis:</span> ${aiApplicability}`
                      : null,
                    partyLine ? `<span class="font-semibold text-on-surface/80">${partyLine}</span>` : null,
                    `<span class="text-primary-blue/70 font-bold">🔍 Search:</span> <span class="italic">${p.case_title || p.case_id}${year ? ' (' + year + ')' : ''} — ${courtName}</span>`,
                  ].filter((x): x is string => Boolean(x));

                  return (
                    <PrecedentCard
                      key={i}
                      id={p.case_id || `PRE-${1000 + i}`}
                      title={p.case_title || p.case}
                      description={description}
                      matchScore={Math.max(score - i * 2, 50)}
                      outcome={formattedOutcome}
                      court={courtName}
                      year={year}
                      borderClass={isAllowed ? "border-l-primary-blue" : "border-l-amber-400"}
                      scoreColor={isAllowed ? "text-primary-blue" : "text-amber-400"}
                      evidencePoints={evidencePoints}
                    />
                  );
                });
              })()}
            </>
          )}
        </div>
      </div>

    </div>
  );
};
