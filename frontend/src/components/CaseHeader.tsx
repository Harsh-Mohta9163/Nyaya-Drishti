import React from 'react';

export const CaseHeader = ({ 
  title, 
  refId, 
  activeTab, 
  onTabChange,
  allVerified,
  onBack
}: { 
  title: string; 
  refId: string;
  activeTab: string;
  onTabChange: (tab: string) => void;
  allVerified: boolean;
  onBack: () => void;
}) => (
  <header className="bg-surface-dim/80 backdrop-blur-md relative z-10 border-b border-outline-variant/20 px-4 sm:px-6 lg:px-10 pt-6 sm:pt-8 lg:pt-10 pb-2">
    <button 
      onClick={onBack}
      className="flex items-center gap-2 text-on-surface-variant hover:text-primary-blue transition-colors text-xs font-bold uppercase tracking-widest mb-3 sm:mb-4 group"
    >
      <span className="material-symbols-outlined text-base group-hover:-translate-x-1 transition-transform">arrow_back</span>
      Back to Case List
    </button>
    <div className="flex flex-col gap-3 sm:gap-4 mb-4 sm:mb-6">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-on-surface-variant font-medium text-xs tracking-widest uppercase truncate max-w-[200px] sm:max-w-none">Case Ref: {refId}</span>
        <span className={`px-2 py-0.5 rounded-sm text-[10px] font-bold uppercase tracking-wider transition-colors shrink-0 ${
          allVerified ? 'bg-green-500/20 text-green-400' : 'bg-outline-variant/40 text-on-surface-variant'
        }`}>
          {allVerified ? 'Verified' : 'Unverified'}
        </span>
      </div>
      
      <div className="flex items-start sm:items-center justify-between gap-4">
        <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-on-surface tracking-tight line-clamp-2 sm:line-clamp-1">{title}</h1>
        
        <div className="flex items-center gap-4 shrink-0">
          <button className="p-2.5 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant ml-2">
            <span className="material-symbols-outlined">language</span>
          </button>
        </div>
      </div>
    </div>

    <div className="flex gap-4 sm:gap-8 border-b border-outline-variant/20 -mb-[1px] overflow-x-auto scrollbar-none">
      {[
        { id: 'overview', label: 'Case Overview' },
        { id: 'verify', label: 'Verify Actions' },
        { id: 'precedents', label: 'Precedents' }
      ].map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-1 sm:px-2 py-3 sm:py-4 font-bold text-xs sm:text-sm tracking-tight transition-all relative whitespace-nowrap shrink-0 ${
            activeTab === tab.id 
              ? 'text-primary-blue border-b-2 border-primary-blue' 
              : 'text-on-surface-variant hover:text-on-surface'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  </header>
);
