import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, FileText, ClipboardList, History, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import GlassCard from '@/components/common/GlassCard';
import StatusBadge from '@/components/cases/StatusBadge';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import ProcessingStatus from '@/components/cases/ProcessingStatus';
import PDFViewer from '@/components/pdf/PDFViewer';
import SplitView from '@/components/pdf/SplitView';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { formatDate, cn } from '@/lib/utils';
import { useCaseDetail, useTriggerExtraction } from '@/hooks/useCases';
import { useExtractedData, useExtractionStatus } from '@/hooks/useExtraction';
import { useReviewHistory } from '@/hooks/useReviews';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function CaseDetailPage() {
  const { id } = useParams();
  const caseId = Number(id);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'extracted' | 'action' | 'history'>('extracted');
  const [expandedDirection, setExpandedDirection] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [highlightText, setHighlightText] = useState<string>('');

  const { data: initialCaseData, isLoading: caseLoading } = useCaseDetail(caseId);
  const isProcessing = initialCaseData?.status === 'processing';
  
  // Use extraction status polling if it's currently processing
  const { data: polledCaseData } = useExtractionStatus(caseId, isProcessing);
  const caseData = polledCaseData || initialCaseData;

  const { data: extracted, isLoading: extractionLoading } = useExtractedData(caseId);
  const { data: reviewLogs = [], isLoading: historyLoading } = useReviewHistory(caseId);
  
  const extractMutation = useTriggerExtraction();

  // Handle triggering extraction if it's just uploaded
  useEffect(() => {
    if (caseData?.status === 'uploaded' && !extractMutation.isPending) {
      extractMutation.mutate(caseId);
    }
  }, [caseData?.status, caseId]);

  if (caseLoading) {
    return <div className="flex items-center justify-center h-64"><LoadingSpinner /></div>;
  }

  if (!caseData) {
    return <div className="p-8 text-center text-slate-400">Case not found.</div>;
  }

  if (caseData.status === 'uploaded' || caseData.status === 'processing' || extractMutation.isPending) {
    return (
      <div className="space-y-6">
        <button onClick={() => navigate('/cases')} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
          <ArrowLeft size={16} /> {t('common.back')}
        </button>
        <ProcessingStatus status="processing" />
      </div>
    );
  }

  const tabs = [
    { key: 'extracted' as const, label: t('caseDetail.extractedData'), icon: <FileText size={14} /> },
    { key: 'action' as const, label: t('caseDetail.actionPlan'), icon: <ClipboardList size={14} /> },
    { key: 'history' as const, label: t('caseDetail.reviewHistory'), icon: <History size={14} /> },
  ];

  const pdfUrl = `${import.meta.env.VITE_API_URL}/api/cases/${caseId}/pdf/`;

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item}>
        <button onClick={() => navigate('/cases')} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors mb-4">
          <ArrowLeft size={16} /> {t('common.back')}
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{caseData.case_number}</h1>
            <p className="text-sm text-slate-400 mt-1">{caseData.court} • {caseData.bench || 'Unknown Bench'}</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={caseData.status} />
            {caseData.ocr_confidence && <ConfidenceBadge value={caseData.ocr_confidence} label="OCR" />}
          </div>
        </div>
      </motion.div>

      {/* Quick Info */}
      <motion.div variants={item} className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          { label: t('cases.petitioner'), value: caseData.petitioner },
          { label: t('cases.respondent'), value: caseData.respondent },
          { label: t('cases.caseType'), value: caseData.case_type },
          { label: t('cases.judgmentDate'), value: formatDate(caseData.judgment_date) },
        ].map(info => (
          <div key={info.label} className="glass-card p-4">
            <p className="text-xs text-slate-500 mb-1">{info.label}</p>
            <p className="text-sm font-medium text-slate-200 truncate" title={info.value}>{info.value}</p>
          </div>
        ))}
      </motion.div>

      {/* Layout Wrap */}
      <motion.div variants={item}>
        <SplitView
          left={<PDFViewer file={pdfUrl} currentPage={currentPage} onPageChange={(p) => { setCurrentPage(p); setHighlightText(''); }} highlightText={highlightText} />}
          right={
            <div className="space-y-6">
              {/* Tabs */}
              <div className="flex gap-1 border-b border-border/50 mb-6">
                {tabs.map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={cn(
                      'flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
                      activeTab === tab.key
                        ? 'border-blue-500 text-blue-500'
                        : 'border-transparent text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {tab.icon} {tab.label}
                  </button>
                ))}
              </div>

        {/* Extracted Data Tab */}
        {activeTab === 'extracted' && (
          <div className="space-y-6">
            {extractionLoading ? (
              <div className="py-12 flex justify-center"><LoadingSpinner /></div>
            ) : !extracted ? (
              <div className="py-8 text-center text-slate-400">No extraction data available yet.</div>
            ) : (
              <>
                {/* Header Data */}
                <GlassCard>
                  <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('caseDetail.headerData')}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(extracted.header_data || {}).map(([key, value]) => (
                      <div key={key}>
                        <p className="text-xs text-slate-500 capitalize">{key.replace(/_/g, ' ')}</p>
                        <p className="text-sm text-slate-200 mt-0.5">{String(value)}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex justify-end">
                    <ConfidenceBadge value={extracted.extraction_confidence} label={t('caseDetail.confidence')} />
                  </div>
                </GlassCard>

                {/* Operative Order */}
                <GlassCard>
                  <h3 className="text-sm font-semibold text-slate-200 mb-3">{t('caseDetail.operativeOrder')}</h3>
                  <div className="rounded-lg bg-slate-800/50 p-4 text-sm text-slate-300 whitespace-pre-line leading-relaxed">
                    {extracted.operative_order}
                  </div>
                </GlassCard>

                {/* Court Directions */}
                {extracted.court_directions && extracted.court_directions.length > 0 && (
                  <GlassCard>
                    <h3 className="text-sm font-semibold text-slate-200 mb-4">{t('caseDetail.courtDirections')}</h3>
                    <div className="space-y-3">
                      {extracted.court_directions.map((dir: any, idx: number) => {
                        const dirId = dir.id || `dir-${idx}`;
                        const verbatimText = dir.verbatim_text || dir.text || '';
                        const directionType = dir.direction_type || dir.action_required || 'Directive';
                        const confidence = dir.confidence || extracted.extraction_confidence || 0.5;
                        
                        return (
                          <div key={dirId} className="rounded-lg border border-border/50 bg-muted/20 overflow-hidden">
                            <button
                              onClick={() => {
                                setExpandedDirection(expandedDirection === dirId ? null : dirId);
                                if (dir.source_reference?.page) {
                                  setCurrentPage(dir.source_reference.page);
                                }
                                if (dir.source_reference?.text_snippet) {
                                  setHighlightText(dir.source_reference.text_snippet);
                                } else if (verbatimText) {
                                  setHighlightText(verbatimText);
                                } else {
                                  setHighlightText('');
                                }
                              }}
                              className="flex w-full items-center justify-between p-4 text-left hover:bg-muted/30 transition-colors"
                            >
                              <div className="flex items-center gap-3">
                                {expandedDirection === dirId ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-500" />}
                                <div>
                                  <span className="rounded-md bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-400">{directionType}</span>
                                  <p className="mt-1 text-sm text-slate-300 line-clamp-1">{verbatimText}</p>
                                </div>
                              </div>
                              <ConfidenceBadge value={confidence} />
                            </button>
                            {expandedDirection === dirId && (
                              <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} className="border-t border-slate-700/50 p-4">
                                <p className="text-sm text-slate-300 mb-3">{verbatimText}</p>
                                <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                                  <span>Responsible: <span className="text-slate-300">{dir.responsible_entity || 'Not specified'}</span></span>
                                  {dir.source_reference && (
                                    <>
                                      <span>{t('caseDetail.page')}: <span className="text-slate-300">{dir.source_reference.page}</span></span>
                                      <span>{t('caseDetail.paragraph')}: <span className="text-slate-300">{dir.source_reference.paragraph}</span></span>
                                    </>
                                  )}
                                </div>
                                {dir.source_reference?.text_snippet && (
                                  <div className="mt-3 rounded-md bg-amber-500/5 border border-amber-500/20 p-3 text-xs text-amber-300/80 italic">
                                    "{dir.source_reference.text_snippet}"
                                  </div>
                                )}
                              </motion.div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </GlassCard>
                )}

                {/* Entities */}
                {extracted.entities && extracted.entities.length > 0 && (
                  <GlassCard>
                    <h3 className="text-sm font-semibold text-slate-200 mb-3">{t('caseDetail.entities')}</h3>
                    <div className="flex flex-wrap gap-2">
                      {extracted.entities.map((entity: any, idx: number) => {
                        const entityName = typeof entity === 'string' ? entity : entity.name || 'Unknown';
                        const entityRole = typeof entity === 'object' && entity.role ? ` (${entity.role})` : '';
                        return (
                          <span key={`${entityName}-${idx}`} className="rounded-full bg-purple-500/10 border border-purple-500/20 px-3 py-1 text-xs font-medium text-purple-300">
                            {entityName}{entityRole}
                          </span>
                        );
                      })}
                    </div>
                  </GlassCard>
                )}
              </>
            )}
          </div>
        )}

        {/* Action Plan Tab */}
        {activeTab === 'action' && (
          <div className="text-center py-8">
            <button
              onClick={() => navigate(`/cases/${id}/action-plan`)}
              className="flex items-center gap-2 mx-auto rounded-lg bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-3 text-sm font-medium text-white shadow-lg shadow-blue-500/25 hover:from-blue-500 hover:to-blue-400 transition-all"
            >
              <ExternalLink size={16} />
              {t('actionPlan.title')}
            </button>
          </div>
        )}

        {/* Review History Tab */}
        {activeTab === 'history' && (
          <div className="space-y-3">
            {historyLoading ? (
              <div className="py-8 flex justify-center"><LoadingSpinner /></div>
            ) : reviewLogs.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No review history yet.</p>
            ) : (
              reviewLogs.map((log, i) => (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="glass-card p-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          'rounded-full px-2 py-0.5 text-xs font-medium',
                          log.action === 'approve' ? 'bg-green-500/10 text-green-500' :
                          log.action === 'edit' ? 'bg-blue-500/10 text-blue-500' :
                          'bg-red-500/10 text-red-500'
                        )}>
                          {log.action}
                        </span>
                        <span className="text-xs text-muted-foreground capitalize">{log.review_level} level</span>
                      </div>
                      <p className="mt-1 text-sm text-foreground">{log.reviewer?.username || 'Unknown User'}</p>
                      {log.notes && <p className="mt-1 text-xs text-muted-foreground italic">"{log.notes}"</p>}
                    </div>
                    <span className="text-xs text-muted-foreground">{formatDate(log.created_at)}</span>
                  </div>
                </motion.div>
              ))
            )}
            <div className="text-center pt-4">
              <button
                onClick={() => navigate(`/cases/${id}/review`)}
                className="text-sm text-blue-500 hover:text-blue-400 transition-colors"
              >
                Go to Review Workflow →
              </button>
            </div>
          </div>
        )}
            </div>
          }
        />
      </motion.div>
    </motion.div>
  );
}
