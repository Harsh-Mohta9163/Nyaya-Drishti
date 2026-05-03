import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Eye } from 'lucide-react';
import { mockCases, mockDeadlines } from '@/lib/mockData';
import StatusBadge from '@/components/cases/StatusBadge';
import PDFUpload from '@/components/cases/PDFUpload';
import { cn, riskColor, formatDate } from '@/lib/utils';
import { mockDelay } from '@/lib/api';
import type { Case, CaseStatus, CaseType } from '@/types';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function CasesListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<CaseStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<CaseType | 'all'>('all');
  const [showUpload, setShowUpload] = useState(false);

  const filtered = useMemo(() => {
    return mockCases.filter(c => {
      if (search && !c.case_number.toLowerCase().includes(search.toLowerCase()) &&
          !c.petitioner.toLowerCase().includes(search.toLowerCase()) &&
          !c.respondent.toLowerCase().includes(search.toLowerCase())) return false;
      if (statusFilter !== 'all' && c.status !== statusFilter) return false;
      if (typeFilter !== 'all' && c.case_type !== typeFilter) return false;
      return true;
    });
  }, [search, statusFilter, typeFilter]);

  const getDaysRemaining = (caseId: number) => {
    const d = mockDeadlines.find(dl => dl.case_id === caseId);
    return d?.days_remaining;
  };

  const getContemptRisk = (caseId: number) => {
    const d = mockDeadlines.find(dl => dl.case_id === caseId);
    return d?.contempt_risk;
  };

  const handleUpload = async (file: File): Promise<Case> => {
    await mockDelay(1500);
    return { ...mockCases[0], id: Date.now(), case_number: `NEW/${Date.now()}`, status: 'uploaded' };
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('cases.title')}</h1>
          <p className="text-sm text-muted-foreground mt-1">{filtered.length} of {mockCases.length} cases</p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)} className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20">
          <Plus className="mr-2 h-4 w-4" />
          {t('cases.uploadTitle')}
        </Button>
      </motion.div>

      {showUpload && (
        <motion.div variants={item}>
          <PDFUpload onUpload={handleUpload} />
        </motion.div>
      )}

      {/* Filters */}
      <motion.div variants={item} className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[250px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('cases.search')}
            className="!pl-10 bg-card border-border shadow-sm"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as CaseStatus | 'all')}>
          <SelectTrigger className="w-[180px] bg-card border-border shadow-sm">
            <SelectValue placeholder={t('cases.filterByStatus')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            {(['uploaded', 'processing', 'extracted', 'review_pending', 'verified', 'action_created'] as CaseStatus[]).map(s => (
              <SelectItem key={s} value={s}>{t(`status.${s}`)}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v as CaseType | 'all')}>
          <SelectTrigger className="w-[180px] bg-card border-border shadow-sm">
            <SelectValue placeholder={t('cases.filterByType')} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {(['WP', 'Appeal', 'SLP', 'CCP', 'LPA'] as CaseType[]).map(ct => (
              <SelectItem key={ct} value={ct}>{ct}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </motion.div>

      {/* Table */}
      <motion.div variants={item} className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow className="hover:bg-transparent">
              <TableHead className="font-medium">{t('cases.caseNumber')}</TableHead>
              <TableHead className="font-medium">{t('cases.court')}</TableHead>
              <TableHead className="font-medium">{t('cases.caseType')}</TableHead>
              <TableHead className="font-medium">{t('cases.judgmentDate')}</TableHead>
              <TableHead className="font-medium">{t('cases.status')}</TableHead>
              <TableHead className="font-medium">{t('cases.contemptRisk')}</TableHead>
              <TableHead className="font-medium">{t('cases.daysToDeadline')}</TableHead>
              <TableHead className="text-right font-medium">{t('cases.actions')}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  {t('cases.noResults')}
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((c, i) => {
                const days = getDaysRemaining(c.id);
                const risk = getContemptRisk(c.id);
                return (
                  <motion.tr
                    key={c.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className="group cursor-pointer border-b transition-colors hover:bg-muted/30 data-[state=selected]:bg-muted"
                    onClick={() => navigate(`/cases/${c.id}`)}
                  >
                    <TableCell className="font-medium text-blue-500">{c.case_number}</TableCell>
                    <TableCell className="text-muted-foreground">{c.court}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-background">{c.case_type}</Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(c.judgment_date)}</TableCell>
                    <TableCell><StatusBadge status={c.status} /></TableCell>
                    <TableCell>
                      {risk && <span className={cn('rounded-full px-2 py-0.5 text-[11px] font-semibold tracking-wide', riskColor[risk])}>{risk}</span>}
                    </TableCell>
                    <TableCell>
                      {days !== undefined && (
                        <span className={cn('text-sm font-semibold', days <= 7 ? 'text-red-500' : days <= 14 ? 'text-amber-500' : 'text-slate-400')}>
                          {days}d
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" className="text-blue-500 hover:text-blue-400 hover:bg-blue-500/10" onClick={(e) => { e.stopPropagation(); navigate(`/cases/${c.id}`); }}>
                        <Eye className="h-4 w-4 mr-1.5" />
                        {t('cases.viewDetail')}
                      </Button>
                    </TableCell>
                  </motion.tr>
                );
              })
            )}
          </TableBody>
        </Table>
      </motion.div>
    </motion.div>
  );
}
