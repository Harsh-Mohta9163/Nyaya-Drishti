import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string): string {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

export function formatRelativeTime(dateString: string): string {
  if (!dateString) return '';
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const daysDifference = Math.round((new Date(dateString).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
  return rtf.format(daysDifference, 'day');
}

export function daysUntil(dateString: string): number {
  if (!dateString) return 0;
  return Math.ceil((new Date(dateString).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
}

export const riskColor: Record<string, string> = {
  High: 'bg-red-500/10 text-red-500 border border-red-500/20',
  Medium: 'bg-amber-500/10 text-amber-500 border border-amber-500/20',
  Low: 'bg-green-500/10 text-green-500 border border-green-500/20',
  Critical: 'bg-red-600/20 text-red-400 border border-red-600/30 font-bold'
};

export const statusColor: Record<string, string> = {
  uploaded: 'bg-slate-500/10 text-slate-400',
  processing: 'bg-blue-500/10 text-blue-400',
  extracted: 'bg-purple-500/10 text-purple-400',
  review_pending: 'bg-amber-500/10 text-amber-400',
  verified: 'bg-green-500/10 text-green-400',
  action_created: 'bg-indigo-500/10 text-indigo-400'
};
