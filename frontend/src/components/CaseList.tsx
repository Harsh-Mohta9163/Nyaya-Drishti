import React, { useState } from 'react';
import { motion } from 'motion/react';

const CaseRow = ({ id, client, court, type, status, risk, days, onClick }: any) => {
  const riskColor = risk === 'High' ? 'text-error-red' : risk === 'Medium' ? 'text-amber-400' : 'text-primary-blue';
  const riskBg = risk === 'High' ? 'bg-error-red/10 border-error-red/20' : risk === 'Medium' ? 'bg-amber-400/10 border-amber-400/20' : 'bg-primary-blue/10 border-primary-blue/20';
  
  const statusColors = 
    status === 'Verified' ? 'bg-green-500/10 border-green-500/30 text-green-400' :
    status === 'Appeal' ? 'bg-amber-400/10 border-amber-400/30 text-amber-400' :
    status === 'Comply' ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' :
    'bg-tertiary-container/10 border-tertiary-container/30 text-tertiary-container';

  const statusDot = 
    status === 'Verified' ? 'bg-green-400' :
    status === 'Appeal' ? 'bg-amber-400' :
    status === 'Comply' ? 'bg-blue-400' :
    'bg-tertiary-container';

  return (
    <tr 
      onClick={onClick}
      className="border-b border-outline-variant/10 hover:bg-primary-blue/[0.02] cursor-pointer transition-colors group"
    >
      <td className="py-5 px-6">
        <div className="flex flex-col">
          <span className="font-mono font-bold text-primary-blue text-sm">{id}</span>
          <span className="text-[10px] text-on-surface-variant font-bold uppercase tracking-widest mt-1 opacity-50">Added 12 Oct 2023</span>
        </div>
      </td>
      <td className="py-5 px-6">
        <div className="flex flex-col">
          <span className="text-on-surface font-bold text-base tracking-tight group-hover:text-primary-blue transition-colors">{client}</span>
          <span className="text-xs text-on-surface-variant font-medium opacity-70">{court} • {type}</span>
        </div>
      </td>
      <td className="py-5 px-6">
        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border font-bold text-[10px] uppercase tracking-widest ${statusColors}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${statusDot} animate-pulse`}></span>
          {status}
        </span>
      </td>
      <td className="py-5 px-6">
        <span className={`inline-flex items-center px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-widest ${riskBg} ${riskColor}`}>
          {risk} Risk
        </span>
      </td>
      <td className="py-5 px-6 text-center">
        <div className="flex flex-col items-center">
          <span className={`text-xl font-bold tracking-tighter ${days <= 7 ? 'text-error-red' : 'text-on-surface'}`}>
            {days.toString().padStart(2, '0')}
          </span>
          <span className="text-[9px] text-on-surface-variant font-black uppercase tracking-widest opacity-40">
            {days <= 7 ? 'CRITICAL' : 'DAYS LEFT'}
          </span>
        </div>
      </td>
    </tr>
  );
};

export const CaseList = ({ 
  onSelectCase, 
  cases 
}: { 
  onSelectCase: (id: string) => void;
  cases: any[];
}) => {
  const [search, setSearch] = useState('');

  const filteredCases = cases.filter(c => 
    c.client.toLowerCase().includes(search.toLowerCase()) ||
    c.id.toLowerCase().includes(search.toLowerCase()) ||
    c.court.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="py-10 space-y-10 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-8">
        <div className="space-y-1">
          <h2 className="text-5xl font-bold text-on-surface tracking-tighter">Case Portfolio</h2>
          <p className="text-on-surface-variant text-lg font-medium opacity-70">
            Manage and analyze your active legal proceedings with AI-driven intelligence.
          </p>
        </div>

        {/* Upload Zone */}
        <div className="glass-card p-4 flex items-center gap-5 border-dashed border-2 border-primary-blue/30 bg-primary-blue/[0.03] cursor-pointer hover:border-primary-blue/60 hover:bg-primary-blue/[0.06] transition-all group lg:min-w-[400px]">
          <div className="p-4 bg-primary-blue/10 rounded-xl group-hover:scale-110 transition-transform">
            <span className="material-symbols-outlined text-primary-blue text-4xl">cloud_upload</span>
          </div>
          <div className="space-y-1">
            <p className="font-bold text-on-surface tracking-tight">Upload Case Files</p>
            <p className="text-xs text-on-surface-variant font-medium">Drag and drop PDFs or click to browse</p>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="glass-card p-3 flex flex-wrap items-center gap-4">
        <div className="flex-grow min-w-[300px] relative">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
          <input 
            type="text"
            placeholder="Search case numbers, clients, or court names..."
            className="w-full bg-surface-dim/50 border border-outline-variant/20 rounded-xl pl-12 pr-4 py-3 text-sm text-on-surface focus:outline-none focus:border-primary-blue/50 transition-all font-medium"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        
        <div className="flex items-center gap-3">
          <select className="bg-surface-dim/50 border border-outline-variant/20 rounded-xl px-4 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-widest cursor-pointer outline-none hover:border-outline-variant/50">
            <option>All Statuses</option>
            <option>Review Pending</option>
            <option>Verified</option>
          </select>
          <select className="bg-surface-dim/50 border border-outline-variant/20 rounded-xl px-4 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-widest cursor-pointer outline-none hover:border-outline-variant/50">
            <option>Case Type</option>
            <option>Writ Petition</option>
            <option>SLP</option>
            <option>Appeal</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-3 bg-surface-container-high border border-outline-variant/30 rounded-xl text-on-surface-variant font-bold text-xs uppercase tracking-widest hover:text-on-surface hover:border-outline-variant/60 transition-all">
            <span className="material-symbols-outlined text-sm">filter_list</span>
            More Filters
          </button>
        </div>
      </div>

      {/* Table Section */}
      <div className="glass-card overflow-visible">
        <div className="overflow-x-auto overflow-y-visible">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-high/50 border-b border-outline-variant/30 text-on-surface-variant text-[10px] font-bold uppercase tracking-[0.2em]">
                <th className="py-4 px-6">Case Number</th>
                <th className="py-4 px-6">Client & Court</th>
                <th className="py-4 px-6">Status</th>
                <th className="py-4 px-6">Risk Level</th>
                <th className="py-4 px-6 text-center">Days left</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((c) => (
                <CaseRow 
                  key={c.id} 
                  {...c} 
                  onClick={() => onSelectCase(c.id)}
                />
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination placeholder */}
        <div className="px-6 py-4 flex items-center justify-between border-t border-outline-variant/10 bg-surface-container/30">
          <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest opacity-60">Showing {filteredCases.length} cases</span>
          <div className="flex gap-2">
            <button className="w-8 h-8 rounded-lg flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-all">
              <span className="material-symbols-outlined text-base">chevron_left</span>
            </button>
            <button className="w-8 h-8 rounded-lg bg-primary-blue text-on-primary-blue flex items-center justify-center text-xs font-bold">1</button>
            <button className="w-8 h-8 rounded-lg flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high transition-all">
              <span className="material-symbols-outlined text-base">chevron_right</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
