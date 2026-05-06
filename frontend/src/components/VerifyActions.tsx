import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface ActionItemProps {
  action: {
    id: string;
    title: string;
    source: string;
    description: string;
    tags: string[];
    isVerified?: boolean;
    isHighPriority?: boolean;
    dueDate?: string;
  };
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, newDescription: string) => void;
  onActionClick: (page: number) => void;
  key?: string;
}

const getDepartmentColors = (source: string) => {
  const s = source.toLowerCase();
  if (s.includes('pollution') || s.includes('kspcb')) return 'bg-green-500/10 border-green-500/30 text-green-400';
  if (s.includes('revenue') || s.includes('tax')) return 'bg-amber-400/10 border-amber-400/30 text-amber-400';
  if (s.includes('labor') || s.includes('hr')) return 'bg-purple-500/10 border-purple-500/30 text-purple-400';
  if (s.includes('legal')) return 'bg-primary-blue/10 border-primary-blue/30 text-primary-blue';
  return 'bg-surface-container-high/50 border-outline-variant/30 text-on-surface-variant';
};

const ActionItem = ({ action, onToggle, onDelete, onEdit, onActionClick }: ActionItemProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedDescription, setEditedDescription] = useState(action.description);

  const handleSave = () => {
    onEdit(action.id, editedDescription);
    setIsEditing(false);
  };

  const handleItemClick = (e: React.MouseEvent) => {
    // Prevent trigger if clicking buttons
    if ((e.target as HTMLElement).closest('button')) return;
    
    // Extract page number from source (e.g. "Order Page 2" -> 2)
    const pageMatch = action.source.match(/Page\s+(\d+)/i);
    const pageNum = pageMatch ? parseInt(pageMatch[1]) : 1;
    onActionClick(pageNum);
  };

  return (
    <div 
      onClick={handleItemClick}
      className={`glass-card p-5 flex gap-5 items-start transition-all duration-300 group cursor-pointer ${
        action.isVerified ? 'border-primary-blue/30 bg-primary-blue/[0.03]' : 'hover:border-primary-blue/40 bg-surface-container/20'
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
            <span className={`inline-flex px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-[0.1em] border ${getDepartmentColors(action.source)}`}>
              {action.source}
            </span>
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
          <div className="bg-surface-dim/40 rounded-lg p-4 text-[14px] text-on-surface-variant font-medium leading-relaxed border border-outline-variant/10">
            {action.description}
          </div>
        )}
        
        <div className="flex flex-wrap gap-2">
          {action.tags.map(tag => (
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

export const VerifyActions = ({ 
  actions, 
  onToggle, 
  onDelete, 
  onEdit, 
  onVerifyAll,
  onActionClick,
  highlightedPage
}: { 
  actions: {
    id: string;
    title: string;
    source: string;
    description: string;
    tags: string[];
    isVerified?: boolean;
    isHighPriority?: boolean;
    dueDate?: string;
  }[]; 
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, desc: string) => void;
  onVerifyAll: () => void;
  onActionClick: (page: number) => void;
  highlightedPage: number | null;
}) => {
  const [zoom, setZoom] = useState(100);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const pageRefs = React.useRef<(HTMLDivElement | null)[]>([]);

  React.useEffect(() => {
    if (highlightedPage !== null && pageRefs.current[highlightedPage - 1]) {
      const element = pageRefs.current[highlightedPage - 1];
      const container = scrollRef.current;
      
      if (element && container) {
        // Simple offset calculation
        const targetScrollTop = element.offsetTop - 40;
        
        container.scrollTo({
          top: targetScrollTop,
          behavior: 'smooth'
        });
      }
    }
  }, [highlightedPage]);

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
              {highlightedPage ? `Page ${highlightedPage} of 3` : 'Page 1 of 3'}
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
          {[1, 2, 3].map((page) => (
            <div 
              key={page}
              ref={el => pageRefs.current[page-1] = el}
              style={{ transform: `scale(${zoom/100})`, transformOrigin: 'top center' }}
              className="w-full max-w-[580px] bg-white text-black p-12 shadow-2xl rounded-sm min-h-[820px] relative font-serif shrink-0 transition-transform duration-300"
            >
              {/* AI Highlighting Simulation */}
              <AnimatePresence mode="wait">
                {highlightedPage === page && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 1.02 }}
                    animate={{ 
                      opacity: [0, 1, 1, 0.8], 
                      scale: [1.02, 1, 1, 1],
                    }}
                    transition={{ duration: 2, times: [0, 0.1, 0.8, 1] }}
                    className="absolute inset-0 border-[6px] border-primary-blue/40 pointer-events-none z-10 bg-primary-blue/[0.03]"
                  >
                    <motion.div 
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      className="absolute top-4 right-4 bg-primary-blue text-on-primary-blue text-[10px] font-black px-3 py-1.5 rounded shadow-lg uppercase tracking-wider flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-sm">psychology</span>
                      AI Reference Found
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Highlights rendered for specific sections */}
              <div className={`absolute top-[188px] left-10 right-10 h-[62px] border rounded-sm transition-all duration-700 ${highlightedPage === page ? 'bg-primary-blue/40 border-primary-blue ring-8 ring-primary-blue/20' : 'bg-primary-blue/5 border-primary-blue/20'}`}></div>
              <div className={`absolute top-[372px] left-10 right-10 h-[44px] border rounded-sm transition-all duration-700 ${highlightedPage === page ? 'bg-primary-blue/30 border-primary-blue ring-4 ring-primary-blue/10' : 'bg-primary-blue/5 border-primary-blue/10'}`}></div>
              
              <div className="text-center mb-10 border-b border-gray-200 pb-6">
                <h3 className="font-bold text-xl uppercase tracking-tight">In the Supreme Court of India</h3>
                <p className="text-sm italic text-gray-600 mt-1 uppercase tracking-widest text-[10px]">Civil Appellate Jurisdiction</p>
              </div>
              
              <div className="flex justify-between text-[11px] font-bold mb-8 border-b border-gray-100 pb-2">
                <span className="uppercase tracking-wider">Civil Appeal No. 8942 of 2023</span>
                <span className="uppercase tracking-widest">Page {page}</span>
              </div>
              
              <div className="space-y-4 text-xs mb-8">
                <p><span className="font-bold underline uppercase mr-2 tracking-wide">Between:</span> Union of India & Ors. ... Appellants</p>
                <p><span className="font-bold underline uppercase mr-2 tracking-wide">And:</span> Sharma Corp Pvt. Ltd. ... Respondent</p>
              </div>
              
              <div className="space-y-6 text-[13px] leading-relaxed text-justify text-gray-800">
                <h4 className="font-black border-b-2 border-black inline-block uppercase text-sm tracking-tight mb-2">Order Summary</h4>
                <p>1. Leave granted. This appeal arises from the judgment of the High Court dated 14.05.2023, which quashed the demand notice issued by the appellant department.</p>
                <p className="relative">2. Having heard the learned counsel for the parties and perused the records, we find that the High Court erred in its interpretation of Section 42(1) of the Act. The respondent company is hereby directed to deposit 50% of the disputed tax amount within four weeks from today.</p>
                <p>3. The competent authority within the Ministry of Corporate Affairs is directed to review the regulatory compliance of the respondent for the financial years 2020-2022 and submit a preliminary report within 60 days.</p>
                <div className="h-2 w-full bg-gray-100 rounded-full my-4"></div>
                <div className="h-2 w-5/6 bg-gray-100 rounded-full my-4"></div>
                <div className="h-2 w-full bg-gray-100 rounded-full my-4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column (unchanged structure, just updated item calls) */}
      <div className="w-full lg:w-[55%] flex flex-col gap-6 h-full">
        {/* Header & Controls */}
        <div className="flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <h3 className="text-xl font-bold text-on-surface tracking-tight">Action Verification</h3>
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

        {/* Action List Section */}
        {actions.length > 0 ? (
          <div className="flex-1 overflow-y-auto pr-2 space-y-4 scrollbar-thin pb-20">
            {actions.map(action => (
              <ActionItem 
                key={action.id}
                action={action}
                onToggle={onToggle}
                onDelete={onDelete}
                onEdit={onEdit}
                onActionClick={onActionClick}
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
