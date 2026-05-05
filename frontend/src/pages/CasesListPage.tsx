import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Eye } from 'lucide-react';
import StatusBadge from '@/components/cases/StatusBadge';
import PDFUpload from '@/components/cases/PDFUpload';
import { cn, riskColor, formatDate } from '@/lib/utils';
import { useCasesList, useUploadCase } from '@/hooks/useCases';
import { useDeadlines } from '@/hooks/useDashboard';
import type { CaseStatus, CaseType } from '@/types';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function CasesListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<CaseStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<CaseType | 'all'>('all');
  const [showUpload, setShowUpload] = useState(false);

  // We can pass filters to the backend, but since the mock version did client-side filtering, 
  // we'll fetch all and filter client-side for now, or pass params if backend supports it.
  // The updated backend supports status, case_type, and search.
  const { data: casesResponse, isLoading: casesLoading } = useCasesList({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    case_type: typeFilter !== 'all' ? typeFilter : undefined,
    search: search || undefined,
  });
  
  const cases = casesResponse?.results || [];

  const { data: deadlines = [] } = useDeadlines(30);
  const uploadMutation = useUploadCase();

  const getDaysRemaining = (caseId: number) => {
    const d = deadlines.find(dl => dl.case_id === caseId);
    return d?.days_remaining;
  };

  const getContemptRisk = (caseId: number) => {
    const d = deadlines.find(dl => dl.case_id === caseId);
    return d?.contempt_risk;
  };

  const handleUpload = async (file: File) => {
    const newCase = await uploadMutation.mutateAsync({ file });
    setShowUpload(false);
    navigate(`/cases/${newCase.id}`);
    return newCase;
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('cases.title')}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {casesLoading ? 'Loading cases...' : `${cases.length} ${search || statusFilter !== 'all' || typeFilter !== 'all' ? 'filtered ' : ''}cases`}
          </p>
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
      <motion.div variants={item} className="rounded-xl border border-border bg-card shadow-sm overflow-hidden min-h-[400px] relative">
        {casesLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-card/50 backdrop-blur-sm">
            <LoadingSpinner />
          </div>
        )}
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
            {!casesLoading && cases.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  {t('cases.noResults')}
                </TableCell>
              </TableRow>
            ) : (
              cases.map((c, i) => {
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
