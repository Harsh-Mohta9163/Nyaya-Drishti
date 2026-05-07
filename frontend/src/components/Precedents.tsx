import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { apiGetRecommendation } from '../api';

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

          <div className="flex items-center gap-4 pt-2">
            <button className="px-4 py-2 bg-primary-blue text-on-primary-blue text-[10px] font-black uppercase tracking-widest rounded-lg shadow-lg shadow-primary-blue/20 hover:scale-105 transition-transform">
              View Full Case
            </button>
            <button className="flex items-center gap-2 text-on-surface-variant hover:text-on-surface transition-colors text-[10px] font-black uppercase tracking-widest">
              <span className="material-symbols-outlined text-lg">description</span> PDF
            </button>
          </div>
        </div>
      </div>
    </motion.article>
  );
};

export const Precedents = ({ caseId = "mock-id" }: { caseId?: string }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<any>(null);

  useEffect(() => {
    const fetchRecommendation = async () => {
      setLoading(true);
      try {
        const data = await apiGetRecommendation({
          case_id: caseId,
          area_of_law: 'constitutional',
          case_text: 'The petitioner filed a writ petition challenging the arbitrary dismissal from service without due process or a proper inquiry under Article 311 of the Constitution.'
        });
        setRecommendation(data);
      } catch (err: any) {
        console.error(err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendation();
  }, [caseId]);

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
            {loading && <span className="text-primary-blue text-xs animate-pulse">Running AI Inference (Llama 70B)...</span>}
            <span className="text-[10px] font-black uppercase tracking-widest text-on-surface-variant">Sort by:</span>
            <select className="bg-surface-container/50 border border-outline-variant/30 rounded-lg px-3 py-1.5 text-[10px] font-bold text-on-surface-variant uppercase tracking-widest outline-none focus:border-primary-blue/50">
              <option>Similarity Score</option>
              <option>Recent</option>
              <option>Authority level</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-error-red/10 border border-error-red/30 rounded-xl text-error-red text-sm">
            Error loading RAG recommendations: {error}
          </div>
        )}

        <div className="space-y-6">
          {recommendation && recommendation.verdict && (
            <div className="p-6 mb-6 bg-primary-blue/5 border border-primary-blue/20 rounded-2xl">
              <h3 className="text-primary-blue font-bold mb-2">Live AI Recommendation</h3>
              <p className="text-on-surface-variant text-sm mb-4">{recommendation.primary_reasoning}</p>
              <div className="flex gap-4">
                <span className="px-3 py-1 bg-surface-dim rounded-lg text-xs font-bold border border-outline-variant/30 text-on-surface">
                  Decision: <span className="text-primary-blue">{recommendation.verdict.decision}</span>
                </span>
                <span className="px-3 py-1 bg-surface-dim rounded-lg text-xs font-bold border border-outline-variant/30 text-on-surface">
                  Analyzed Precedents: <span className="text-amber-400">{recommendation.statistical_basis?.similar_cases_analyzed || 0}</span>
                </span>
              </div>
            </div>
          )}
          <PrecedentCard 
            id="#SC-2022-81"
            title="ABC Corp vs Union of India"
            description="Landmark ruling establishing boundaries for algorithmic patentability under Section 3(k) of the Patents Act, setting a high bar for 'technical effect'."
            matchScore={94}
            outcome="Upheld"
            court="Supreme Court"
            year="2022"
            borderClass="border-l-primary-blue"
            scoreColor="text-primary-blue"
            evidencePoints={[
              "Strong alignment on <b class='text-on-surface'>Claim 14</b> regarding neural network weight updates.",
              "Court specifically rejected the defense's reliance on <b class='text-on-surface'>'abstract mathematical methods'</b> (Para 42).",
              "Cited identical precedent (State vs Turing, 2018) in final judgment."
            ]}
          />

          <PrecedentCard 
            id="#HC-DEL-2021-404"
            title="Nexus Systems vs State"
            description="Case dismissed due to insufficient detailing of the algorithmic 'technical advancement' over existing prior art in software patents."
            matchScore={81}
            outcome="Dismissed"
            evidenceType="RISK FLAG"
            court="High Court (Del)"
            year="2021"
            borderClass="border-l-error-red"
            scoreColor="text-error-red"
            evidencePoints={[
              "The court ruled that mere implementation of known ML algorithms (CNNs) does not constitute patentable subject matter without hardware-software synergy.",
              "<b>Critical Gap:</b> Our current filing lacks this specific synergy documentation, posing a high risk of dismissal."
            ]}
          />

          <PrecedentCard 
            id="#TRB-2020-112"
            title="VisionTech IP Dispute"
            description="Dispute regarding copyright infringement of training datasets used in early computer vision models."
            matchScore={76}
            outcome="Settled"
            court="Tribunal"
            year="2020"
            borderClass="border-l-amber-400"
            scoreColor="text-amber-400"
            evidencePoints={[
              "Case reinforces fair use doctrine specifically for datasets compiled from public-facing URLs.",
              "Settlement included an ongoing royalty model that could be used as a bargaining benchmark."
            ]}
          />
        </div>
      </div>

      {/* Right Sidebar */}
      <aside className="w-full lg:w-80 flex flex-col gap-8 shrink-0">
        <div className="glass-card p-6 border-outline-variant/20">
          <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-on-surface-variant mb-6 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">hub</span>
            Precedent Network
          </h3>
          <div className="aspect-square bg-surface-dim/80 rounded-2xl border border-outline-variant/10 relative overflow-hidden flex items-center justify-center p-4">
            {/* Visual representation of network */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary-blue/10 via-transparent to-transparent"></div>
            <div className="relative w-full h-full border border-dashed border-outline-variant/30 rounded-full animate-spin-slow"></div>
            <div className="absolute w-4 h-4 rounded-full bg-primary-blue shadow-[0_0_20px_rgba(173,198,255,1)]"></div>
            <div className="absolute top-1/4 left-1/4 w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.5)]"></div>
            <div className="absolute bottom-1/4 right-1/4 w-3 h-3 rounded-full bg-green-400 shadow-[0_0_15px_rgba(74,222,128,0.5)]"></div>
            
            <button className="absolute bottom-4 inset-x-4 bg-surface-container-high/90 backdrop-blur-md border border-outline-variant/30 rounded-lg py-2 text-[8px] font-black uppercase tracking-widest hover:bg-primary-blue hover:text-on-primary-blue transition-all">
              Interactive Graph <span className="material-symbols-outlined text-[10px] align-middle ml-1">open_in_full</span>
            </button>
          </div>
        </div>

        <div className="glass-card p-6 border-outline-variant/20">
          <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-on-surface-variant mb-6">Active AI Filters</h3>
          <div className="flex flex-wrap gap-2">
            {['Section 3(k)', 'Supreme Court', 'Neural Networks'].map(filter => (
              <span key={filter} className="pl-3 pr-2 py-1.5 rounded-lg bg-surface-container flex items-center gap-2 text-[10px] font-bold text-on-surface border border-outline-variant/30 group hover:border-primary-blue transition-colors cursor-pointer">
                {filter}
                <span className="material-symbols-outlined text-[12px] text-on-surface-variant group-hover:text-error-red">close</span>
              </span>
            ))}
            <button className="text-[10px] font-black text-primary-blue uppercase tracking-widest hover:underline mt-2 ml-1">
              + Add Filter
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
};
