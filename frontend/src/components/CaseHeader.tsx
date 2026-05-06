import React from 'react';

export const CaseHeader = ({ 
  title, 
  refId, 
  activeTab, 
  onTabChange,
  allVerified,
  onBack,
  decision,
  onDecision
}: { 
  title: string; 
  refId: string;
  activeTab: string;
  onTabChange: (tab: string) => void;
  allVerified: boolean;
  onBack: () => void;
  decision: 'none' | 'appeal' | 'comply';
  onDecision: (decision: 'none' | 'appeal' | 'comply') => void;
}) => (
  <header className="bg-surface-dim/80 backdrop-blur-md sticky top-0 z-10 border-b border-outline-variant/20 px-10 pt-10 pb-2">
    <button 
      onClick={onBack}
      className="flex items-center gap-2 text-on-surface-variant hover:text-primary-blue transition-colors text-xs font-bold uppercase tracking-widest mb-4 group"
    >
      <span className="material-symbols-outlined text-base group-hover:-translate-x-1 transition-transform">arrow_back</span>
      Back to Case List
    </button>
    <div className="flex flex-col gap-4 mb-6">
      <div className="flex items-center gap-3">
        <span className="text-on-surface-variant font-medium text-xs tracking-widest uppercase">Case Ref: {refId}</span>
        <span className={`px-2 py-0.5 rounded-sm text-[10px] font-bold uppercase tracking-wider transition-colors ${
          decision !== 'none' ? (decision === 'appeal' ? 'bg-amber-400/20 text-amber-400' : 'bg-blue-500/20 text-blue-400') :
          allVerified ? 'bg-green-500/20 text-green-400' : 'bg-outline-variant/40 text-on-surface-variant'
        }`}>
          {decision !== 'none' ? (decision === 'appeal' ? 'Appeal' : 'Comply') : (allVerified ? 'Verified' : 'Unverified')}
        </span>
      </div>
      
      <div className="flex items-center justify-between gap-8">
        <h1 className="text-3xl font-bold text-on-surface tracking-tight">{title}</h1>
        
        <div className="flex items-center gap-4">
          {decision === 'none' ? (
            <>
              <button 
                disabled={!allVerified}
                onClick={() => onDecision('appeal')}
                className={`px-6 py-2.5 font-semibold rounded-lg transition-all ${
                  allVerified 
                    ? 'bg-surface-container border border-outline-variant text-on-surface hover:bg-surface-container-high cursor-pointer shadow-lg' 
                    : 'bg-surface-container border border-outline-variant/10 text-on-surface/20 cursor-not-allowed opacity-50'
                }`}
              >
                Appeal Review
              </button>
              <button 
                disabled={!allVerified}
                onClick={() => onDecision('comply')}
                className={`px-6 py-2.5 font-bold rounded-lg transition-all ${
                  allVerified
                    ? 'bg-primary-blue text-on-primary-blue shadow-[0_0_20px_rgba(173,198,255,0.4)] hover:scale-[1.02] cursor-pointer'
                    : 'bg-primary-blue/20 text-primary-blue/20 cursor-not-allowed'
                }`}
              >
                Comply Now
              </button>
            </>
          ) : (
            <div className={`px-6 py-2.5 rounded-xl border flex items-center gap-3 font-bold text-sm tracking-tight ${
              decision === 'appeal' 
                ? 'bg-amber-400/10 border-amber-400/30 text-amber-400' 
                : 'bg-green-500/10 border-green-500/30 text-green-400'
            }`}>
              <span className="material-symbols-outlined">
                {decision === 'appeal' ? 'gavel' : 'verified_user'}
              </span>
              This case was chosen to be {decision === 'appeal' ? 'appealed' : 'complied with'}
            </div>
          )}
          <button className="p-2.5 rounded-full hover:bg-surface-container transition-colors text-on-surface-variant ml-2">
            <span className="material-symbols-outlined">language</span>
          </button>
        </div>
      </div>
    </div>

    <div className="flex gap-8 border-b border-outline-variant/20 -mb-[1px]">
      {[
        { id: 'overview', label: 'Case Overview' },
        { id: 'verify', label: 'Verify Actions' },
        { id: 'precedents', label: 'Precedents' }
      ].map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`px-2 py-4 font-bold text-sm tracking-tight transition-all relative ${
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
