import React, { useState, useRef, useEffect, useCallback } from 'react';
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

const ActionItem = ({ 
  action, 
  isActive,
  onToggle, 
  onDelete, 
  onEdit, 
  onSelect 
}: { 
  action: ActionData;
  isActive: boolean;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, desc: string) => void;
  onSelect: (action: ActionData) => void;
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDescription, setEditedDescription] = useState(action.description);

  const handleSave = () => {
    onEdit(action.id, editedDescription);
    setIsEditing(false);
  };

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
          onClick={() => onToggle(action.id)}
          className={`flex items-center justify-center w-6 h-6 rounded border-2 transition-all ${
            action.isVerified 
              ? 'border-primary-blue bg-primary-blue/20 text-primary-blue' 
              : 'border-outline-variant/60 hover:border-primary-blue'
          }`}
        >
          {action.isVerified && <span className="material-symbols-outlined text-sm font-bold">check</span>}
        </button>
      </div>
      
      <div className="flex-1 space-y-4">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className={`inline-flex px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-[0.1em] border ${getDepartmentColors(action.source)}`}>
                {action.source}
              </span>
              {hasSource && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider bg-yellow-400/10 border border-yellow-400/20 text-yellow-400">
                  <span className="material-symbols-outlined text-[10px]">pin_drop</span>
                  Pg {action.sourceLocation!.page}
                </span>
              )}
            </div>
            <h4 className="font-bold text-on-surface text-lg tracking-tight group-hover:text-primary-blue transition-colors">{action.title}</h4>
          </div>
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
        </div>
        
        {isEditing ? (
          <div className="space-y-3">
            <textarea
              className="w-full bg-surface-dim/80 border border-primary-blue/30 rounded-lg p-3 text-[14px] text-on-surface focus:outline-none focus:ring-1 focus:ring-primary-blue min-h-[80px]"
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button 
                onClick={handleSave}
                className="px-4 py-1.5 bg-primary-blue text-on-primary-blue text-[11px] font-bold rounded-lg uppercase tracking-wider"
              >
                Save Changes
              </button>
            </div>
          </div>
        ) : (
          null
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
  highlightedPage: _highlightedPage,
  pdfUrl
}: { 
  actions: ActionData[]; 
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, desc: string) => void;
  onVerifyAll: () => void;
  onActionClick: (page: number) => void;
  highlightedPage: number | null;
  pdfUrl?: string | null;
}) => {
  const [zoom, setZoom] = useState(100);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<SourceLocation | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<(HTMLDivElement | null)[]>([]);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  // Handle action selection — scroll to source in PDF
  const handleActionSelect = useCallback((action: ActionData) => {
    setActiveActionId(action.id);

    if (action.sourceLocation) {
      // We have precise source location from PyMuPDF
      setActiveSource(action.sourceLocation);
      const targetPage = action.sourceLocation.page;

      // Scroll to the target page
      requestAnimationFrame(() => {
        const el = pageRefs.current[targetPage - 1];
        const container = scrollRef.current;
        if (el && container) {
          // Calculate scroll position to center the highlight in the viewport
          const rects = action.sourceLocation!.rects || [];
          const scale = PDF_RENDER_WIDTH / action.sourceLocation!.page_width;
          const highlightY = rects.length > 0 ? rects[0].y0 * scale : 0;
          const targetScroll = el.offsetTop + highlightY - container.clientHeight / 3;

          container.scrollTo({
            top: Math.max(0, targetScroll),
            behavior: 'smooth'
          });
        }
      });

      // Also notify parent (for backward compat)
      onActionClick(targetPage);
    } else {
      // Fallback: no source location, estimate page
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
            behavior: 'smooth'
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
    <div className="flex flex-col lg:flex-row gap-8 py-8 h-[calc(100vh-180px)] overflow-hidden">
      {/* Left: PDF Viewer */}
      <div className="w-full lg:w-[45%] flex flex-col glass-card border-outline-variant/20 h-full relative group shrink-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary-blue/50 via-primary-blue/20 to-transparent"></div>
        
        {/* Toolbar */}
        <div className="h-14 border-b border-outline-variant/20 bg-surface-container/30 flex items-center justify-between px-6 shrink-0 z-20">
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
          className="flex-1 overflow-y-auto bg-surface-container-lowest/50 p-10 flex flex-col items-center gap-10 scrollbar-thin relative"
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
      <div className="w-full lg:w-[55%] flex flex-col gap-6 h-full">
        {/* Header & Controls */}
        <div className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <h3 className="text-xl font-bold text-on-surface tracking-tight">Court Directions — Verify</h3>
            <span className="px-2 py-1 bg-surface-container-high rounded text-[10px] font-bold text-on-surface-variant uppercase tracking-widest">
              {actions.filter(a => a.isVerified).length} / {actions.length} Verified
            </span>
          </div>
          <div className="flex gap-3">
            <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-high transition-all font-bold text-xs uppercase tracking-widest">
              <span className="material-symbols-outlined text-sm">add</span> Add Action
            </button>
            <button 
              onClick={onVerifyAll}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-blue text-on-primary-blue hover:bg-primary-blue/90 transition-all font-bold text-xs uppercase tracking-widest shadow-lg shadow-primary-blue/20"
            >
              <span className="material-symbols-outlined text-sm">check_circle</span> Verify All ({actions.length})
            </button>
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
        {actions.length > 0 ? (
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin pb-20">
            {actions.map(action => (
              <ActionItem 
                key={action.id}
                action={action}
                isActive={activeActionId === action.id}
                onToggle={onToggle}
                onDelete={onDelete}
                onEdit={onEdit}
                onSelect={handleActionSelect}
              />
            ))}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-10 opacity-50">
            <span className="material-symbols-outlined text-6xl mb-4">playlist_add_check</span>
            <p className="font-bold">No actions found</p>
            <p className="text-sm">Extracted actions will appear here for verification.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// ─── Error Boundary ──────────────────────────────────────────────────────────
class VerifyActionsErrorBoundary extends React.Component<
  { children: React.ReactNode }, 
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('VerifyActions crashed:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-10 text-center">
          <span className="material-symbols-outlined text-6xl text-error-red mb-4">error</span>
          <h3 className="text-xl font-bold text-on-surface mb-2">Something went wrong</h3>
          <p className="text-on-surface-variant mb-4 text-sm">{this.state.error?.message || 'Unknown error'}</p>
          <button 
            onClick={() => this.setState({ hasError: false })}
            className="px-4 py-2 bg-primary-blue text-white rounded-lg hover:bg-primary-blue/80 transition-colors font-bold text-sm"
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Wrap export with error boundary
export const VerifyActionsSafe = (props: Parameters<typeof VerifyActions>[0]) => (
  <VerifyActionsErrorBoundary>
    <VerifyActions {...props} />
  </VerifyActionsErrorBoundary>
);
