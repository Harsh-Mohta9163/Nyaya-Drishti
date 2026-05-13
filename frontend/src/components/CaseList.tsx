import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { fetchCases, extractCase, CaseData } from '../api/client';
import { shortPartyTitle, formatCaseNumber } from '../utils/truncate';
const PHASES = [
  { label: 'Extracting Metadata...', icon: 'progress_activity' },
  { label: 'Finding Precedents...', icon: 'progress_activity' },
  { label: 'Analyzing Legal Risk...', icon: 'progress_activity' },
  { label: 'Generating Action Plan...', icon: 'progress_activity' },
];

function processingStatus(j: CaseData): string | null {
  if (!j.judgments?.length) return null;
  const s = j.judgments[0].processing_status;
  if (s === 'complete' || s === 'failed') return null;
  return s;
}

function mapStatus(c: CaseData): string {
  const ps = c.judgments?.[0]?.processing_status;
  if (ps === 'complete') return 'Extracted';
  if (ps === 'failed') return 'Failed';
  return c.status === 'disposed' ? 'Disposed' : 'Pending';
}

function riskFromCase(c: CaseData): 'High' | 'Medium' | 'Low' {
  const risk = c.judgments?.[0]?.contempt_risk;
  if (risk === 'High') return 'High';
  if (risk === 'Medium') return 'Medium';
  return 'Low';
}

// ─── Processing Row (inline in table, matching code.html) ───────────────────

const ProcessingRow = ({ fileName, phase }: { fileName: string; phase: number }) => (
  <tr className="hover:bg-primary-blue/5 transition-colors group border-l-4 border-primary-blue bg-primary-blue/[0.03]">
    <td className="py-4 sm:py-5 px-4 sm:px-6">
      <div className="flex flex-col">
        <span className="font-mono font-bold text-primary-blue text-sm">Pending...</span>
        <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest mt-1 italic animate-pulse">
          Processing
        </span>
      </div>
    </td>
    <td className="py-4 sm:py-5 px-4 sm:px-6 hidden sm:table-cell">
      <div className="flex flex-col">
        <span className="text-on-surface font-bold text-base tracking-tight truncate max-w-[200px]">{fileName}</span>
        <span className="text-xs text-on-surface-variant font-medium opacity-70">Analyzing uploaded document...</span>
      </div>
    </td>
    <td className="py-4 sm:py-5 px-4 sm:px-6 hidden md:table-cell" colSpan={2}>
      <div className="flex flex-col gap-2 max-w-xs">
        <div className="relative h-5 overflow-hidden">
          {PHASES.map((p, i) => (
            <div
              key={i}
              className="absolute inset-0 text-primary-blue font-bold text-xs flex items-center gap-2 transition-opacity duration-500"
              style={{ opacity: phase === i ? 1 : 0 }}
            >
              <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
              {p.label}
            </div>
          ))}
        </div>
        <div className="w-full bg-primary-blue/10 h-1.5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary-blue shadow-[0_0_8px_rgba(173,198,255,0.4)]"
            animate={{ width: `${((phase + 1) / PHASES.length) * 100}%` }}
            transition={{ duration: 1.5, ease: 'easeInOut' }}
          />
        </div>
      </div>
    </td>
    <td className="py-4 sm:py-5 px-4 sm:px-6 text-center hidden lg:table-cell">
      <div className="flex flex-col items-center">
        <span className="text-xl font-bold tracking-tighter text-on-surface-variant animate-pulse">--</span>
        <span className="text-[9px] text-on-surface-variant font-black uppercase tracking-widest opacity-40">Calculating</span>
      </div>
    </td>
  </tr>
);

// ─── Mobile Case Card (for small screens) ────────────────────────────────────

const MobileCaseCard: React.FC<{ c: CaseData; onClick: () => void }> = ({ c, onClick }) => {
  const stat = mapStatus(c);
  const risk = riskFromCase(c);
  const riskColor = risk === 'High' ? 'text-error-red' : risk === 'Medium' ? 'text-amber-400' : 'text-primary-blue';
  const riskBg = risk === 'High' ? 'bg-error-red/10 border-error-red/20' : risk === 'Medium' ? 'bg-amber-400/10 border-amber-400/20' : 'bg-primary-blue/10 border-primary-blue/20';
  const statusColors =
    stat === 'Extracted' ? 'bg-green-500/10 border-green-500/30 text-green-400' :
    stat === 'Disposed' ? 'bg-amber-400/10 border-amber-400/30 text-amber-400' :
    stat === 'Failed' ? 'bg-error-red/10 border-error-red/30 text-error-red' :
    'bg-tertiary-container/10 border-tertiary-container/30 text-tertiary-container';
  const hasAnalysis = !!c.judgments?.[0]?.action_plan?.full_rag_recommendation;
  const displayStat = hasAnalysis ? stat : (stat === 'Extracted' ? 'Pending Analysis' : stat);
  const updatedStatusColors = displayStat === 'Pending Analysis' ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : statusColors;
  const clientName = shortPartyTitle(c.petitioner_name, c.respondent_name);
  const formattedCaseNumber = formatCaseNumber(c.case_number || '');

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      className="glass-card p-4 cursor-pointer hover:border-primary-blue/40 transition-all group"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0 flex-1">
          <span className="font-mono font-bold text-primary-blue text-xs truncate block">{formattedCaseNumber.primary}</span>
          <h4 className="font-bold text-on-surface text-base tracking-tight group-hover:text-primary-blue transition-colors truncate mt-1">{clientName}</h4>
          <p className="text-xs text-on-surface-variant font-medium opacity-70 truncate">{c.court_name} • {c.case_type}</p>
        </div>
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-widest shrink-0 ${riskBg} ${riskColor}`}>
          {risk}
        </span>
      </div>
      <div className="flex items-center gap-2 mt-3">
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border font-bold text-[10px] uppercase tracking-widest ${updatedStatusColors}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${displayStat === 'Pending Analysis' ? 'bg-blue-400 animate-pulse' : stat === 'Extracted' ? 'bg-green-400' : 'bg-amber-400'}`}></span>
          {displayStat}
        </span>
      </div>
    </motion.div>
  );
};

// ─── Normal Case Row ─────────────────────────────────────────────────────────

const CaseRow: React.FC<{ c: CaseData; onClick: () => void }> = ({ c, onClick }) => {
  const stat = mapStatus(c);
  const risk = riskFromCase(c);

  const riskColor = risk === 'High' ? 'text-error-red' : risk === 'Medium' ? 'text-amber-400' : 'text-primary-blue';
  const riskBg = risk === 'High' ? 'bg-error-red/10 border-error-red/20' : risk === 'Medium' ? 'bg-amber-400/10 border-amber-400/20' : 'bg-primary-blue/10 border-primary-blue/20';

  const statusColors =
    stat === 'Extracted' ? 'bg-green-500/10 border-green-500/30 text-green-400' :
    stat === 'Disposed' ? 'bg-amber-400/10 border-amber-400/30 text-amber-400' :
    stat === 'Failed' ? 'bg-error-red/10 border-error-red/30 text-error-red' :
    'bg-tertiary-container/10 border-tertiary-container/30 text-tertiary-container';

  const statusDot =
    stat === 'Extracted' ? 'bg-green-400' :
    stat === 'Disposed' ? 'bg-amber-400' :
    stat === 'Failed' ? 'bg-error-red' :
    'bg-tertiary-container';

  const filingDate = new Date(c.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
  const clientName = shortPartyTitle(c.petitioner_name, c.respondent_name);
  const formattedCaseNumber = formatCaseNumber(c.case_number || '');
  
  // Check if RAG analysis has been run
  const hasAnalysis = !!c.judgments?.[0]?.action_plan?.full_rag_recommendation;
  const deadlineDays = hasAnalysis ? c.judgments?.[0]?.action_plan?.full_rag_recommendation?.verdict?.days_remaining : null;
  const isOverdue = deadlineDays !== null && deadlineDays !== undefined && deadlineDays < 0;
  const deadlineText = isOverdue ? 'OVERDUE' : (deadlineDays !== null && deadlineDays !== undefined ? deadlineDays : '—');
  
  const displayStat = hasAnalysis ? stat : (stat === 'Extracted' ? 'Pending Analysis' : stat);
  const updatedStatusColors = 
    displayStat === 'Pending Analysis' ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' :
    statusColors;
  const updatedStatusDot = displayStat === 'Pending Analysis' ? 'bg-blue-400' : statusDot;

  return (
    <motion.tr
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      className="border-b border-outline-variant/10 hover:bg-primary-blue/[0.02] cursor-pointer transition-colors group"
    >
      <td className="py-4 sm:py-5 px-4 sm:px-6">
        <div className="flex flex-col max-w-[180px]">
          <span className="font-mono font-bold text-primary-blue text-sm truncate">{formattedCaseNumber.primary}</span>
          {formattedCaseNumber.additionalCount > 0 && (
            <span className="text-[10px] text-primary-blue/70 font-bold uppercase tracking-widest mt-0.5">+{formattedCaseNumber.additionalCount} more</span>
          )}
          <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest mt-1 opacity-50">Filing: {filingDate}</span>
        </div>
      </td>
      <td className="py-4 sm:py-5 px-4 sm:px-6 hidden sm:table-cell">
        <div className="flex flex-col max-w-[280px]">
          <span className="text-on-surface font-bold text-base tracking-tight group-hover:text-primary-blue transition-colors truncate">
            {clientName}
          </span>
          <span className="text-xs text-on-surface-variant font-medium opacity-70 truncate">{c.court_name} • {c.case_type}</span>
        </div>
      </td>
      <td className="py-4 sm:py-5 px-4 sm:px-6 hidden md:table-cell">
        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border font-bold text-[10px] uppercase tracking-widest ${updatedStatusColors}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${updatedStatusDot} ${displayStat === 'Pending Analysis' ? 'animate-pulse' : ''}`}></span>
          {displayStat}
        </span>
      </td>
      <td className="py-4 sm:py-5 px-4 sm:px-6 hidden md:table-cell">
        <span className={`inline-flex items-center px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-widest ${riskBg} ${riskColor}`}>
          {risk} Risk
        </span>
      </td>
      <td className="py-4 sm:py-5 px-4 sm:px-6 text-center hidden lg:table-cell">
        <div className="flex flex-col items-center">
          <span className={`font-bold tracking-tighter ${isOverdue ? 'text-error-red text-xs uppercase' : deadlineDays !== null && deadlineDays < 14 ? 'text-error-red text-xl' : 'text-on-surface text-xl'}`}>
            {deadlineText}
          </span>
          {!isOverdue && <span className="text-[9px] text-on-surface-variant font-black uppercase tracking-widest opacity-40">Days</span>}
        </div>
      </td>
    </motion.tr>
  );
};

// ─── Main CaseList Component ────────────────────────────────────────────────

export const CaseList = ({
  onSelectCase,
}: {
  onSelectCase: (id: string) => void;
  cases?: any[];
  onAddCase?: (c: any) => void;
}) => {
  const [cases, setCases] = useState<CaseData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingFileName, setProcessingFileName] = useState('');
  const [processingPhase, setProcessingPhase] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const phaseIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ── Fetch cases from DB ────────────────────────────────────────────────
  const loadCases = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchCases();
      setCases(data);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load cases');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadCases(); }, [loadCases]);

  // ── Phase cycling animation ────────────────────────────────────────────
  const startPhaseAnimation = () => {
    setProcessingPhase(0);
    let phase = 0;
    phaseIntervalRef.current = setInterval(() => {
      phase = (phase + 1) % PHASES.length;
      setProcessingPhase(phase);
    }, 2000);
  };

  const stopPhaseAnimation = () => {
    if (phaseIntervalRef.current) {
      clearInterval(phaseIntervalRef.current);
      phaseIntervalRef.current = null;
    }
  };

  // ── File upload handler ────────────────────────────────────────────────
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (fileInputRef.current) fileInputRef.current.value = '';

    setIsProcessing(true);
    setProcessingFileName(file.name);
    startPhaseAnimation();

    try {
      await extractCase(file);
      stopPhaseAnimation();
      setIsProcessing(false);
      await loadCases(); // Refresh list with the new case from DB
    } catch (err: any) {
      stopPhaseAnimation();
      setIsProcessing(false);
      setError(err.message ?? 'Extraction failed');
    }
  };

  // Cleanup on unmount
  useEffect(() => () => stopPhaseAnimation(), []);

  // ── Local search filter ────────────────────────────────────────────────
  const filtered = cases.filter(c => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (c.case_number || '').toLowerCase().includes(q) ||
      (c.petitioner_name || '').toLowerCase().includes(q) ||
      (c.respondent_name || '').toLowerCase().includes(q) ||
      (c.court_name || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="py-6 sm:py-10 space-y-6 sm:space-y-10 max-w-[1440px] mx-auto">
      <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleFileChange} className="hidden" />

      {/* Header */}
      <div className="flex flex-col gap-6 sm:gap-8">
        <div className="space-y-1">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-on-surface tracking-tighter">Case Portfolio</h2>
          <p className="text-on-surface-variant text-sm sm:text-base lg:text-lg font-medium opacity-70">
            Manage and analyze your active legal proceedings with AI-driven intelligence.
          </p>
        </div>

        {/* Upload Zone */}
        <div
          onClick={() => !isProcessing && fileInputRef.current?.click()}
          className={`glass-card p-4 flex items-center gap-4 sm:gap-5 border-dashed border-2 border-primary-blue/30 bg-primary-blue/[0.03] cursor-pointer hover:border-primary-blue/60 hover:bg-primary-blue/[0.06] transition-all group w-full lg:max-w-[500px] ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <div className="p-3 sm:p-4 bg-primary-blue/10 rounded-xl group-hover:scale-110 transition-transform shrink-0">
            <span className="material-symbols-outlined text-primary-blue text-2xl sm:text-4xl">cloud_upload</span>
          </div>
          <div className="space-y-1 flex-1 min-w-0">
            <p className="font-bold text-on-surface tracking-tight text-sm sm:text-base">Upload Case Files</p>
            <p className="text-xs text-on-surface-variant font-medium">PDF up to 50 MB — extraction is automatic</p>
          </div>
          <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary-blue transition-colors shrink-0 hidden sm:block">add_circle</span>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-3 flex flex-wrap items-center gap-4">
        <div className="flex-grow min-w-0 relative">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
          <input
            type="text"
            placeholder="Search case numbers, clients, or court names..."
            className="w-full bg-surface-dim/50 border border-outline-variant/20 rounded-xl pl-12 pr-4 py-3 text-sm text-on-surface focus:outline-none focus:border-primary-blue/50 transition-all font-medium"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Error Banner */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3 px-4 sm:px-5 py-3 bg-error-red/10 border border-error-red/30 rounded-xl text-error-red text-sm font-medium"
          >
            <span className="material-symbols-outlined text-base">warning</span>
            <span className="flex-1 min-w-0 truncate">{error}</span>
            <button onClick={() => setError(null)} className="ml-auto material-symbols-outlined text-base opacity-60 hover:opacity-100 shrink-0">close</button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile Card View */}
      <div className="sm:hidden space-y-3">
        {isProcessing && (
          <div className="glass-card p-4 border-l-4 border-primary-blue bg-primary-blue/[0.03]">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-sm animate-spin text-primary-blue">progress_activity</span>
              <div>
                <p className="font-bold text-primary-blue text-sm">Processing...</p>
                <p className="text-xs text-on-surface-variant truncate">{processingFileName}</p>
              </div>
            </div>
            <div className="mt-3 w-full bg-primary-blue/10 h-1.5 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary-blue"
                animate={{ width: `${((processingPhase + 1) / PHASES.length) * 100}%` }}
                transition={{ duration: 1.5, ease: 'easeInOut' }}
              />
            </div>
          </div>
        )}

        {loading && !isProcessing && (
          <div className="py-20 text-center text-on-surface-variant">
            <span className="material-symbols-outlined text-4xl animate-spin block mx-auto mb-3 opacity-40">progress_activity</span>
            <p className="text-sm opacity-60">Loading cases…</p>
          </div>
        )}

        {!loading && filtered.length === 0 && !isProcessing && (
          <div className="py-20 text-center text-on-surface-variant">
            <span className="material-symbols-outlined text-4xl block mx-auto mb-3 opacity-30">folder_open</span>
            <p className="text-sm opacity-60">No cases found. Upload a PDF to get started.</p>
          </div>
        )}

        {filtered.map(c => (
          <MobileCaseCard key={c.id} c={c} onClick={() => onSelectCase(c.id)} />
        ))}
        
        <div className="px-2 py-3 text-center">
          <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-60">
            Showing {filtered.length} case{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="glass-card overflow-visible hidden sm:block">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-high/50 border-b border-outline-variant/30 text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.2em]">
                <th className="py-4 px-4 sm:px-6">Case Number</th>
                <th className="py-4 px-4 sm:px-6 hidden sm:table-cell">Client &amp; Court</th>
                <th className="py-4 px-4 sm:px-6 hidden md:table-cell">Status</th>
                <th className="py-4 px-4 sm:px-6 hidden md:table-cell">Risk Level</th>
                <th className="py-4 px-4 sm:px-6 text-center hidden lg:table-cell">Days to Deadline</th>
              </tr>
            </thead>
            <tbody>
              {/* In-table processing row */}
              {isProcessing && (
                <ProcessingRow fileName={processingFileName} phase={processingPhase} />
              )}

              {loading && !isProcessing && (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-on-surface-variant">
                    <span className="material-symbols-outlined text-4xl animate-spin block mx-auto mb-3 opacity-40">progress_activity</span>
                    <p className="text-sm opacity-60">Loading cases…</p>
                  </td>
                </tr>
              )}

              {!loading && filtered.length === 0 && !isProcessing && (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-on-surface-variant">
                    <span className="material-symbols-outlined text-4xl block mx-auto mb-3 opacity-30">folder_open</span>
                    <p className="text-sm opacity-60">No cases found. Upload a PDF to get started.</p>
                  </td>
                </tr>
              )}

              {filtered.map(c => (
                <CaseRow key={c.id} c={c} onClick={() => onSelectCase(c.id)} />
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-4 sm:px-6 py-4 flex items-center justify-between border-t border-outline-variant/10 bg-surface-container/30">
          <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-60">
            Showing {filtered.length} case{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>
    </div>
  );
};
