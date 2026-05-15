import React, { useState, useRef, useEffect, useCallback, Component } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up PDF worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

// ─── Types ──────────────────────────────────────────────────────────────────────

interface SourceLocation {
  page: number;
  page_width: number;
  page_height: number;
  rects: Array<{ x0: number; y0: number; x1: number; y1: number }>;
}

interface ActionData {
  id: string;
  title: string;
  source: string;
  description: string;
  tags: string[];
  isVerified?: boolean;
  isHighPriority?: boolean;
  dueDate?: string;
  sourceLocation?: SourceLocation | null;
  sourceText?: string;
  financialDetails?: string | null;
  // Government-perspective enrichment (apps/cases/services/directive_enricher.py)
  actorType?: 'government_department' | 'court_or_registry' | 'accused_or_petitioner' | 'third_party' | 'informational' | null;
  govActionRequired?: boolean | null;
  implementationSteps?: string[];
  displayNote?: string;
  govtSummary?: string;
}

// ─── Helpers ────────────────────────────────────────────────────────────────────

const getDepartmentColors = (source: string) => {
  const s = source.toLowerCase();
  if (s.includes('pollution') || s.includes('kspcb')) return 'bg-green-500/10 border-green-500/30 text-green-400';
  if (s.includes('revenue') || s.includes('tax')) return 'bg-amber-400/10 border-amber-400/30 text-amber-400';
  if (s.includes('labor') || s.includes('hr')) return 'bg-purple-500/10 border-purple-500/30 text-purple-400';
  if (s.includes('legal')) return 'bg-primary-blue/10 border-primary-blue/30 text-primary-blue';
  return 'bg-surface-container-high/50 border-outline-variant/30 text-on-surface-variant';
};

const PDF_RENDER_WIDTH = 580;

// ─── ActionItem ─────────────────────────────────────────────────────────────────

type EditPatch = { description?: string; govtSummary?: string; implementationSteps?: string[]; dueDate?: string };

const ActionItem: React.FC<{
  action: ActionData;
  isActive: boolean;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, patch: EditPatch) => void;
  onSelect: (action: ActionData) => void;
  onShowInPDF: (action: ActionData) => void;
  canVerify?: boolean;
}> = ({
  action,
  isActive,
  onToggle,
  onDelete,
  onEdit,
  onSelect,
  onShowInPDF,
  canVerify = true,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDescription, setEditedDescription] = useState(action.description);
  const [editedSummary, setEditedSummary] = useState(action.govtSummary || '');
  const [editedSteps, setEditedSteps] = useState<string[]>(action.implementationSteps || []);
  const [editedDueDate, setEditedDueDate] = useState(action.dueDate || '');

  // Keep edit form in sync when the source action changes from above
  // (e.g. after a backend save round-trip).
  useEffect(() => {
    setEditedDescription(action.description);
    setEditedSummary(action.govtSummary || '');
    setEditedSteps(action.implementationSteps || []);
    setEditedDueDate(action.dueDate || '');
  }, [action.id, action.description, action.govtSummary, action.implementationSteps, action.dueDate]);

  const handleSave = () => {
    onEdit(action.id, {
      description: editedDescription,
      govtSummary: editedSummary,
      implementationSteps: editedSteps.filter(s => s.trim().length > 0),
      dueDate: editedDueDate,
    });
    setIsEditing(false);
  };

  // Card click only HIGHLIGHTS the card — no longer auto-scrolls the PDF
  // (the explicit "Show in PDF" button does that).
  const handleItemClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return;
    onSelect(action);
  };

  const hasSource = !!action.sourceLocation;

  return (
    <div 
      onClick={handleItemClick}
      className={`glass-card p-5 flex gap-5 items-start transition-all duration-300 group cursor-pointer ${
        isActive
          ? 'border-yellow-400/50 bg-yellow-400/[0.05] ring-1 ring-yellow-400/30'
          : action.isVerified 
            ? 'border-primary-blue/30 bg-primary-blue/[0.03]' 
            : 'hover:border-primary-blue/40 bg-surface-container/20'
      }`}
    >
      <div className="pt-1">
        <button
          onClick={() => canVerify && onToggle(action.id)}
          disabled={!canVerify}
          title={canVerify ? undefined : 'Only HLC / Central Law can verify'}
          className={`flex items-center justify-center w-6 h-6 rounded border-2 transition-all ${
            action.isVerified
              ? 'border-primary-blue bg-primary-blue/20 text-primary-blue'
              : 'border-outline-variant/60 hover:border-primary-blue'
          } ${!canVerify ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          {action.isVerified && <span className="material-symbols-outlined text-sm font-bold">check</span>}
        </button>
      </div>
      
      <div className="flex-1 space-y-4">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`inline-flex px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-[0.1em] border ${getDepartmentColors(action.source)}`}>
                {action.source}
              </span>
              {hasSource && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onShowInPDF(action); }}
                  title="Scroll PDF to this directive's source paragraph"
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-yellow-400/10 border border-yellow-400/20 text-yellow-400 hover:bg-yellow-400/20 hover:border-yellow-400/40 transition-all"
                >
                  <span className="material-symbols-outlined text-[12px]">find_in_page</span>
                  Show in PDF · Pg {action.sourceLocation!.page}
                </button>
              )}
            </div>
            <h4 className="font-bold text-on-surface text-lg tracking-tight group-hover:text-primary-blue transition-colors">{action.title}</h4>
          </div>
          {canVerify && (
            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className={`p-1.5 rounded transition-colors ${isEditing ? 'text-primary-blue bg-primary-blue/10' : 'text-on-surface-variant hover:text-primary-blue hover:bg-primary-blue/10'}`}
              >
                <span className="material-symbols-outlined text-sm">{isEditing ? 'close' : 'edit'}</span>
              </button>
              <button
                onClick={() => onDelete(action.id)}
                className="p-1.5 text-on-surface-variant hover:text-error-red rounded hover:bg-error-red/10 transition-colors"
              >
                <span className="material-symbols-outlined text-sm">delete</span>
              </button>
            </div>
          )}
        </div>
        
        {isEditing ? (
          <div className="space-y-4 bg-primary-blue/[0.04] border border-primary-blue/20 rounded-lg p-4">
            {/* Verbatim text */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/80">
                Verbatim Directive (from PDF)
              </label>
              <textarea
                className="w-full bg-surface-dim/80 border border-primary-blue/30 rounded-lg p-3 text-[13px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue min-h-[80px]"
                value={editedDescription}
                onChange={(e) => setEditedDescription(e.target.value)}
              />
            </div>

            {/* Govt summary */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-widest text-emerald-300/80">
                Government Summary (one-liner)
              </label>
              <textarea
                className="w-full bg-surface-dim/80 border border-emerald-400/30 rounded-lg p-3 text-[13px] text-on-surface focus:outline-none focus:ring-1 focus:ring-emerald-400/50 min-h-[48px]"
                value={editedSummary}
                onChange={(e) => setEditedSummary(e.target.value)}
                placeholder="e.g. Refund excess service tax to petitioner."
              />
            </div>

            {/* Implementation steps */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-emerald-300/80">
                Implementation Steps (LCO action plan)
              </label>
              {editedSteps.map((step, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-on-surface-variant text-xs font-mono mt-2.5 shrink-0">{idx + 1}.</span>
                  <input
                    type="text"
                    value={step}
                    onChange={e => {
                      const next = [...editedSteps];
                      next[idx] = e.target.value;
                      setEditedSteps(next);
                    }}
                    className="flex-1 bg-surface-dim/80 border border-emerald-400/30 rounded-lg px-3 py-2 text-[13px] text-on-surface focus:outline-none focus:ring-1 focus:ring-emerald-400/50"
                  />
                  <button
                    type="button"
                    onClick={() => setEditedSteps(editedSteps.filter((_, i) => i !== idx))}
                    className="p-2 text-on-surface-variant hover:text-error-red rounded hover:bg-error-red/10"
                    title="Remove step"
                  >
                    <span className="material-symbols-outlined text-sm">close</span>
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => setEditedSteps([...editedSteps, ''])}
                className="text-[11px] font-semibold text-emerald-300/80 hover:text-emerald-300 inline-flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-sm">add</span> Add Step
              </button>
            </div>

            {/* Due date */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant/80">
                Due Date / Timeline
              </label>
              <input
                type="text"
                value={editedDueDate}
                onChange={e => setEditedDueDate(e.target.value)}
                placeholder="e.g. within three weeks, 30 Jun 2026"
                className="w-full bg-surface-dim/80 border border-outline-variant/40 rounded-lg px-3 py-2 text-[13px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue/50"
              />
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                onClick={() => {
                  setIsEditing(false);
                  setEditedDescription(action.description);
                  setEditedSummary(action.govtSummary || '');
                  setEditedSteps(action.implementationSteps || []);
                  setEditedDueDate(action.dueDate || '');
                }}
                className="px-4 py-1.5 text-on-surface-variant hover:text-on-surface text-[11px] font-bold rounded-lg uppercase tracking-wider"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-1.5 bg-primary-blue text-on-primary-blue text-[11px] font-bold rounded-lg uppercase tracking-wider"
              >
                Save Changes
              </button>
            </div>
          </div>
        ) : null}

        {/* Government-perspective enrichment block (read-only display) */}
        {!isEditing && action.actorType && (
          <GovtPerspectivePanel action={action} />
        )}

        {action.financialDetails && (
          <div className="flex items-start gap-2 bg-amber-400/5 border border-amber-400/15 rounded-lg p-3">
            <span className="material-symbols-outlined text-amber-400 text-sm mt-0.5">currency_rupee</span>
            <p className="text-xs text-amber-400/90 font-medium leading-relaxed">{action.financialDetails}</p>
          </div>
        )}
        
        <div className="flex flex-wrap gap-2">
          {(action.tags || []).map(tag => (
            <span key={tag} className="inline-flex items-center px-2.5 py-1 rounded-full bg-surface-container-high/50 border border-outline-variant/30 text-on-surface-variant text-[10px] font-bold uppercase tracking-wider">
              {tag}
            </span>
          ))}
          {action.dueDate && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-error-red/5 border border-error-red/20 text-error-red text-[10px] font-bold uppercase tracking-wider">
              <span className="material-symbols-outlined text-[12px]">schedule</span>
              Due: {action.dueDate}
            </span>
          )}
          {action.isHighPriority && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-error-red/10 border border-error-red/30 text-error-red text-[10px] font-bold uppercase tracking-wider animate-pulse">
              <span className="material-symbols-outlined text-[12px]">warning</span>
              High Priority
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Government Perspective Panel ──────────────────────────────────────────────

const ACTOR_LABELS: Record<string, string> = {
  government_department: 'Your Department',
  court_or_registry: 'Court / Registrar',
  accused_or_petitioner: 'Litigating Party',
  third_party: 'Third Party',
  informational: 'Informational',
};
const ACTOR_ICONS: Record<string, string> = {
  government_department: 'account_balance',
  court_or_registry: 'gavel',
  accused_or_petitioner: 'person',
  third_party: 'group',
  informational: 'info',
};

const GovtPerspectivePanel: React.FC<{ action: ActionData }> = ({ action }) => {
  const gov = action.govActionRequired === true;
  const actor = action.actorType || 'informational';

  return (
    <div
      className={`rounded-lg p-3 border ${
        gov
          ? 'bg-emerald-500/[0.06] border-emerald-400/30'
          : 'bg-surface-container-highest/30 border-outline-variant/20'
      }`}
    >
      {/* Header chip + summary */}
      <div className="flex items-start gap-2 mb-2">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-[0.1em] border shrink-0 ${
            gov
              ? 'bg-emerald-500/15 text-emerald-300 border-emerald-400/40'
              : 'bg-surface-container/60 text-on-surface-variant border-outline-variant/40'
          }`}
        >
          <span className="material-symbols-outlined text-[12px]">{ACTOR_ICONS[actor]}</span>
          {gov ? 'Govt Action Required' : `Informational · ${ACTOR_LABELS[actor]}`}
        </span>
        {action.govtSummary && (
          <p className="text-[11px] text-on-surface leading-relaxed flex-1 min-w-0">
            {action.govtSummary}
          </p>
        )}
      </div>

      {/* Implementation steps for government-action items */}
      {gov && (action.implementationSteps?.length ?? 0) > 0 && (
        <div className="mt-2 pl-2 border-l-2 border-emerald-400/30 space-y-1.5">
          <p className="text-[9px] font-bold uppercase tracking-widest text-emerald-300/80">
            Implementation Steps for LCO
          </p>
          <ol className="space-y-1 text-[11px] text-on-surface-variant leading-relaxed list-decimal list-inside">
            {action.implementationSteps!.map((step, i) => (
              <li key={i} className="marker:text-emerald-300/70">{step}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Display note for non-government items */}
      {!gov && action.displayNote && (
        <p className="text-[11px] text-on-surface-variant opacity-80 italic mt-1 pl-2 border-l-2 border-outline-variant/30">
          {action.displayNote}
        </p>
      )}
    </div>
  );
};

// ─── Highlight Overlay Component ────────────────────────────────────────────────

const HighlightOverlay = ({ 
  rects, 
  pageWidth, 
  renderWidth 
}: { 
  rects: Array<{ x0: number; y0: number; x1: number; y1: number }>;
  pageWidth: number;
  renderWidth: number;
}) => {
  const scale = renderWidth / pageWidth;
  
  // Guard: empty rects array
  if (!rects || rects.length === 0) return null;

  // Normalize rects — scanned PDFs may have rotated coordinates (tall-thin instead of wide-short)
  const normalizedRects = rects.map(r => {
    const w = Math.abs(r.x1 - r.x0);
    const h = Math.abs(r.y1 - r.y0);
    // If a rect is taller than wide, it's likely from a rotated scan — swap axes
    if (h > w * 3 && w < 50) {
      return { x0: r.y0, y0: r.x0, x1: r.y1, y1: r.x1 };
    }
    return r;
  }).filter(r => {
    // Filter out invalid/degenerate rects
    const w = r.x1 - r.x0;
    const h = r.y1 - r.y0;
    return w > 0 && h > 0 && w < pageWidth && h < 842;
  });

  if (normalizedRects.length === 0) return null;

  // Compute a single paragraph bounding box from all rects
  // This gives a clean highlight for scanned PDFs where per-word rects are fragmented
  const minX = Math.min(...normalizedRects.map(r => r.x0));
  const maxX = Math.max(...normalizedRects.map(r => r.x1));
  const minY = Math.min(...normalizedRects.map(r => r.y0));
  const maxY = Math.max(...normalizedRects.map(r => r.y1));

  // Use standard text margins for the paragraph box
  const paraLeft = Math.min(minX, 72) * scale;
  const paraRight = Math.max(maxX, pageWidth - 50) * scale;

  return (
    <>
      {/* Full paragraph highlight band */}
      <motion.div
        initial={{ opacity: 0, scaleY: 0 }}
        animate={{ opacity: 1, scaleY: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{
          position: 'absolute',
          left: `${paraLeft}px`,
          top: `${minY * scale - 4}px`,
          width: `${paraRight - paraLeft}px`,
          height: `${(maxY - minY) * scale + 8}px`,
          transformOrigin: 'top center',
        }}
        className="bg-yellow-400/15 border border-yellow-400/40 pointer-events-none z-10 rounded-lg"
      />
      {/* Side bracket indicator */}
      <motion.div
        initial={{ opacity: 0, scaleY: 0 }}
        animate={{ opacity: 1, scaleY: 1 }}
        transition={{ duration: 0.5, delay: 0.15 }}
        style={{
          position: 'absolute',
          left: `${Math.max(0, paraLeft - 8)}px`,
          top: `${minY * scale - 4}px`,
          width: '4px',
          height: `${(maxY - minY) * scale + 8}px`,
          transformOrigin: 'top center',
        }}
        className="bg-yellow-400 rounded-full pointer-events-none z-10 shadow-[0_0_8px_rgba(250,204,21,0.6)]"
      />
    </>
  );
};

// ─── Main Component ─────────────────────────────────────────────────────────────

export const VerifyActions = ({
  actions,
  onToggle,
  onDelete,
  onEdit,
  onVerifyAll,
  onActionClick,
  onAdd,
  highlightedPage: _highlightedPage,
  pdfUrl,
  canVerify = true,
}: {
  actions: ActionData[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, patch: { description?: string; govtSummary?: string; implementationSteps?: string[] }) => void;
  onVerifyAll: () => void;
  onActionClick: (page: number) => void;
  onAdd: (action: Omit<ActionData, 'id'>) => void;
  highlightedPage: number | null;
  pdfUrl?: string | null;
  /** Hide approve/edit/reject/add controls when false (non-HLC roles). */
  canVerify?: boolean;
}) => {
  const [zoom, setZoom] = useState(100);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<SourceLocation | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);
  
  const [isAdding, setIsAdding] = useState(false);
  const [newAction, setNewAction] = useState({ title: '', source: '', description: '', isHighPriority: false });

  const handleAddSubmit = () => {
    if (!newAction.title.trim() || !newAction.description.trim()) return;
    onAdd({
      title: newAction.title,
      source: newAction.source || 'Manual Entry',
      description: newAction.description,
      tags: [],
      isVerified: false,
      isHighPriority: newAction.isHighPriority,
    });
    setNewAction({ title: '', source: '', description: '', isHighPriority: false });
    setIsAdding(false);
  };

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  // Card click: only marks the card active + paints the overlay if we already
  // have a source location. NEVER scrolls the PDF — that's the explicit
  // "Show in PDF" button's job.
  const handleActionSelect = useCallback((action: ActionData) => {
    setActiveActionId(action.id);
    if (action.sourceLocation) {
      setActiveSource(action.sourceLocation);
    } else {
      setActiveSource(null);
    }
  }, []);

  // Explicit user action: scroll PDF to the source paragraph.
  const handleShowInPDF = useCallback((action: ActionData) => {
    setActiveActionId(action.id);

    if (action.sourceLocation) {
      setActiveSource(action.sourceLocation);
      const targetPage = action.sourceLocation.page;

      requestAnimationFrame(() => {
        const el = pageRefs.current[targetPage - 1];
        const container = scrollRef.current;
        if (el && container) {
          const rects = action.sourceLocation!.rects || [];
          const scale = PDF_RENDER_WIDTH / action.sourceLocation!.page_width;
          const highlightY = rects.length > 0 ? rects[0].y0 * scale : 0;
          const targetScroll = el.offsetTop + highlightY - container.clientHeight / 3;

          container.scrollTo({
            top: Math.max(0, targetScroll),
            behavior: 'smooth',
          });
        }
      });

      onActionClick(targetPage);
    } else {
      // No source location — fall back to an estimated page.
      setActiveSource(null);
      const lastPage = numPages || 1;
      const estimatedPage = Math.max(1, lastPage - 2 + parseInt(action.id));
      onActionClick(Math.min(estimatedPage, lastPage));

      requestAnimationFrame(() => {
        const el = pageRefs.current[Math.min(estimatedPage, lastPage) - 1];
        const container = scrollRef.current;
        if (el && container) {
          container.scrollTo({
            top: el.offsetTop - 40,
            behavior: 'smooth',
          });
        }
      });
    }
  }, [numPages, onActionClick]);

  // Clear highlight after 8 seconds
  useEffect(() => {
    if (!activeActionId) return;
    const timer = setTimeout(() => {
      setActiveSource(null);
      setActiveActionId(null);
    }, 8000);
    return () => clearTimeout(timer);
  }, [activeActionId]);

  return (
    <div className="flex flex-col lg:flex-row gap-6 sm:gap-8 py-4 sm:py-8 h-auto lg:h-[calc(100vh-100px)] lg:min-h-[800px] overflow-visible lg:overflow-hidden">
      {/* Left: PDF Viewer */}
      <div className="w-full lg:w-1/2 flex flex-col glass-card border-outline-variant/20 h-[50vh] sm:h-[60vh] lg:h-full relative group shrink-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary-blue/50 via-primary-blue/20 to-transparent"></div>
        
        {/* Toolbar */}
        <div className="h-12 sm:h-14 border-b border-outline-variant/20 bg-surface-container/30 flex items-center justify-between px-3 sm:px-6 shrink-0 z-20">
          <div className="flex items-center gap-4">
            <button className="p-1.5 rounded hover:bg-surface-container-high transition-colors text-on-surface-variant">
              <span className="material-symbols-outlined text-base">menu</span>
            </button>
            <div className="w-px h-4 bg-outline-variant/30"></div>
            <span className="font-bold text-[10px] text-on-surface-variant uppercase tracking-widest min-w-[80px]">
              {activeSource ? (
                <span className="text-yellow-400">
                  <span className="material-symbols-outlined text-[10px] align-middle mr-1">pin_drop</span>
                  Page {activeSource.page} of {numPages || '?'}
                </span>
              ) : (
                `Page 1 of ${numPages || '?'}`
              )}
            </span>
          </div>
          
          <div className="flex items-center gap-2 bg-surface-dim/40 rounded-lg p-1 border border-outline-variant/20">
            <button 
              onClick={() => setZoom(Math.max(50, zoom - 10))}
              className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant transition-colors"
            >
              <span className="material-symbols-outlined text-base">remove</span>
            </button>
            <span className="font-bold text-[10px] w-12 text-center text-on-surface">{zoom}%</span>
            <button 
              onClick={() => setZoom(Math.min(200, zoom + 10))}
              className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant transition-colors"
            >
              <span className="material-symbols-outlined text-base">add</span>
            </button>
          </div>
          
          <div className="flex items-center gap-3">
            <button className="p-1.5 rounded hover:bg-surface-container-high transition-colors text-on-surface-variant">
              <span className="material-symbols-outlined text-base">search</span>
            </button>
            <button className="p-1.5 rounded hover:bg-surface-container-high transition-colors text-on-surface-variant">
              <span className="material-symbols-outlined text-base">download</span>
            </button>
          </div>
        </div>
        
        {/* Document Area */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto bg-surface-container-lowest/50 p-4 sm:p-10 flex flex-col items-center gap-6 sm:gap-10 scrollbar-thin relative"
        >
          {pdfUrl ? (
            <Document
              file={pdfUrl.startsWith('http') ? pdfUrl : pdfUrl.startsWith('/') ? pdfUrl : `/${pdfUrl}`}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={(err) => console.warn('PDF load error:', err)}
              loading={<div className="text-on-surface-variant font-bold p-10 animate-pulse">Loading PDF...</div>}
              error={<div className="text-error-red font-bold p-10">Failed to load PDF. Try reloading the page.</div>}
            >
              {Array.from(new Array(numPages || 0), (_, index) => {
                const pageNum = index + 1;
                const isHighlightedPage = activeSource?.page === pageNum;

                return (
                  <div 
                    key={`page_${pageNum}`}
                    ref={el => pageRefs.current[index] = el}
                    className="mb-10 shadow-2xl rounded-sm relative transition-transform duration-300 bg-white"
                    style={{ transform: `scale(${zoom/100})`, transformOrigin: 'top center' }}
                  >
                    <Page 
                      pageNumber={pageNum} 
                      renderTextLayer={false}
                      renderAnnotationLayer={false}
                      className="max-w-[580px]"
                      width={PDF_RENDER_WIDTH}
                    />

                    {/* Precise Paragraph Highlight Overlay */}
                    {isHighlightedPage && activeSource.rects.length > 0 && (
                      <HighlightOverlay
                        rects={activeSource.rects}
                        pageWidth={activeSource.page_width}
                        renderWidth={PDF_RENDER_WIDTH}
                      />
                    )}

                    {/* Fallback: Page-level flash when no precise rects */}
                    {isHighlightedPage && activeSource.rects.length === 0 && (
                      <AnimatePresence mode="wait">
                        <motion.div 
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0, 0.3, 0.3, 0.1] }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 2, times: [0, 0.1, 0.8, 1] }}
                          className="absolute inset-0 bg-yellow-400 mix-blend-multiply pointer-events-none z-10"
                        />
                      </AnimatePresence>
                    )}

                    {/* Page number badge */}
                    <div className="absolute bottom-2 right-3 bg-black/50 text-white text-[9px] font-bold px-2 py-0.5 rounded-full backdrop-blur-sm z-20">
                      {pageNum}
                    </div>
                  </div>
                );
              })}
            </Document>
          ) : (
            <div className="w-full max-w-[580px] bg-white text-black p-12 shadow-2xl rounded-sm min-h-[820px] relative font-serif shrink-0 flex items-center justify-center">
               <span className="text-gray-400 font-bold">No PDF available for this case.</span>
            </div>
          )}
        </div>
      </div>

      {/* Right Column — Action List */}
      <div className="w-full lg:w-1/2 flex flex-col gap-4 sm:gap-6 h-auto lg:h-full">
        {/* Header & Controls */}
        <div className="flex items-center justify-between flex-wrap gap-4 shrink-0">
          <div className="flex items-center gap-4 flex-wrap">
            <h3 className="text-lg sm:text-xl font-bold text-on-surface tracking-tight whitespace-nowrap">Court Directions — Verify</h3>
            <span className="px-2 py-1 bg-surface-container-high rounded text-[10px] font-bold text-on-surface-variant uppercase tracking-widest whitespace-nowrap">
              {actions.filter(a => a.isVerified).length} / {actions.length} Verified
            </span>
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            {!canVerify && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-container-highest/60 border border-outline-variant/30 text-on-surface-variant text-[10px] font-bold uppercase tracking-wider">
                <span className="material-symbols-outlined text-sm">visibility</span>
                Read-only — HLC verifies
              </span>
            )}
            {canVerify && (
              <>
                <button
                  onClick={() => setIsAdding(!isAdding)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-high transition-all font-bold text-xs uppercase tracking-widest"
                >
                  <span className="material-symbols-outlined text-sm">{isAdding ? 'close' : 'add'}</span> {isAdding ? 'Cancel' : 'Add Action'}
                </button>
                <button
                  onClick={onVerifyAll}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-blue text-on-primary-blue hover:bg-primary-blue/90 transition-all font-bold text-xs uppercase tracking-widest shadow-lg shadow-primary-blue/20"
                >
                  <span className="material-symbols-outlined text-sm">check_circle</span> Verify All ({actions.length})
                </button>
              </>
            )}
          </div>
        </div>

        {/* Source Highlighting Legend */}
        <div className="flex items-center gap-4 px-4 py-2.5 rounded-xl bg-yellow-400/5 border border-yellow-400/15">
          <span className="material-symbols-outlined text-yellow-400 text-sm">info</span>
          <p className="text-[11px] text-on-surface-variant font-medium">
            Click any action to <span className="text-yellow-400 font-bold">highlight its source paragraph</span> in the PDF. Each directive is traced back to its exact location via PyMuPDF.
          </p>
        </div>

        {/* Action List Section */}
        <div className="flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin pb-20">
          {isAdding && (
            <div className="glass-card p-5 border-primary-blue/30 bg-primary-blue/[0.03] space-y-4 mb-4">
              <h4 className="font-bold text-primary-blue text-sm uppercase tracking-wider">New Action</h4>
              <div className="space-y-3">
                <input 
                  type="text" 
                  placeholder="Action Title" 
                  className="w-full bg-surface-dim/80 border border-primary-blue/30 rounded-lg p-3 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue"
                  value={newAction.title}
                  onChange={(e) => setNewAction({ ...newAction, title: e.target.value })}
                />
                <input 
                  type="text" 
                  placeholder="Department / Source (Optional)" 
                  className="w-full bg-surface-dim/80 border border-primary-blue/30 rounded-lg p-3 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue"
                  value={newAction.source}
                  onChange={(e) => setNewAction({ ...newAction, source: e.target.value })}
                />
                <textarea
                  placeholder="Detailed Description"
                  className="w-full bg-surface-dim/80 border border-primary-blue/30 rounded-lg p-3 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue min-h-[80px]"
                  value={newAction.description}
                  onChange={(e) => setNewAction({ ...newAction, description: e.target.value })}
                />
                <div className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    id="highPriority" 
                    checked={newAction.isHighPriority} 
                    onChange={(e) => setNewAction({ ...newAction, isHighPriority: e.target.checked })}
                    className="rounded border-outline-variant/60 text-primary-blue focus:ring-primary-blue bg-transparent w-4 h-4"
                  />
                  <label htmlFor="highPriority" className="text-sm text-on-surface-variant font-medium">Mark as High Priority</label>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button 
                    onClick={() => setIsAdding(false)}
                    className="px-4 py-2 text-on-surface-variant hover:bg-surface-container-high text-xs font-bold rounded-lg uppercase tracking-wider transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleAddSubmit}
                    disabled={!newAction.title.trim() || !newAction.description.trim()}
                    className="px-4 py-2 bg-primary-blue text-on-primary-blue hover:bg-primary-blue/90 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-bold rounded-lg uppercase tracking-wider shadow-lg shadow-primary-blue/20 transition-all"
                  >
                    Save Action
                  </button>
                </div>
              </div>
            </div>
          )}

          {actions.length > 0 ? (
            actions.map(action => (
              <ActionItem
                key={action.id}
                action={action}
                isActive={activeActionId === action.id}
                onToggle={onToggle}
                onDelete={onDelete}
                onEdit={onEdit}
                onSelect={handleActionSelect}
                onShowInPDF={handleShowInPDF}
                canVerify={canVerify}
              />
            ))
          ) : (
            !isAdding && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-10 opacity-50 mt-10">
                <span className="material-symbols-outlined text-6xl mb-4">playlist_add_check</span>
                <p className="font-bold">No actions found</p>
                <p className="text-sm">Extracted actions will appear here for verification.</p>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Error Boundary ──────────────────────────────────────────────────────────
class VerifyActionsErrorBoundary extends Component<
  { children: React.ReactNode }, 
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    // @ts-ignore
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('VerifyActions crashed:', error, info);
  }
  render() {
    // @ts-ignore
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-10 text-center">
          <span className="material-symbols-outlined text-6xl text-error-red mb-4">error</span>
          <h3 className="text-xl font-bold text-on-surface mb-2">Something went wrong</h3>
          {/* @ts-ignore */}
          <p className="text-on-surface-variant mb-4 text-sm">{this.state.error?.message || 'Unknown error'}</p>
          <button 
            // @ts-ignore
            onClick={() => this.setState({ hasError: false })}
            className="px-4 py-2 bg-primary-blue text-white rounded-lg hover:bg-primary-blue/80 transition-colors font-bold text-sm"
          >
            Try Again
          </button>
        </div>
      );
    }
    // @ts-ignore
    return this.props.children;
  }
}

// Wrap export with error boundary
export const VerifyActionsSafe = (props: Parameters<typeof VerifyActions>[0]) => (
  <VerifyActionsErrorBoundary>
    <VerifyActions {...props} />
  </VerifyActionsErrorBoundary>
);
