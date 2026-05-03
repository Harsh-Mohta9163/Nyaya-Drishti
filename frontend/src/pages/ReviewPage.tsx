import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  ArrowLeft, Lock, Check, Pencil, X, CheckCircle,
  FileSearch, GitBranch, Stamp, AlertTriangle
} from 'lucide-react';
import { mockExtractedData, mockActionPlan, mockCases } from '@/lib/mockData';
import GlassCard from '@/components/common/GlassCard';
import ConfidenceBadge from '@/components/common/ConfidenceBadge';
import ConflictAlert from '@/components/review/ConflictAlert';
import { cn, riskColor } from '@/lib/utils';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

type ReviewTab = 'field' | 'directive' | 'case';

export default function ReviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<ReviewTab>('field');
  const [fieldApproved, setFieldApproved] = useState(false);
  const [directiveApproved, setDirectiveApproved] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [rejectDialog, setRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [approvedFields, setApprovedFields] = useState<Set<string>>(new Set());
  const [approvedDirectives, setApprovedDirectives] = useState<Set<string>>(new Set());

  const caseData = mockCases.find(c => c.id === Number(id)) || mockCases[0];
  const extracted = mockExtractedData;
  const plan = mockActionPlan;

  const tabs = [
    { key: 'field' as const, label: t('review.fieldLevel'), icon: <FileSearch size={14} />, locked: false },
    { key: 'directive' as const, label: t('review.directiveLevel'), icon: <GitBranch size={14} />, locked: !fieldApproved },
    { key: 'case' as const, label: t('review.caseLevel'), icon: <Stamp size={14} />, locked: !directiveApproved },
  ];

  const handleFieldApprove = (fieldKey: string) => {
    setApprovedFields(prev => new Set(prev).add(fieldKey));
  };

  const handleFieldEdit = (fieldKey: string, value: string) => {
    setEditValues(prev => ({ ...prev, [fieldKey]: value }));
    setEditingField(null);
    // Check for conflicts
    if (fieldKey === 'judgment_date' && new Date(value) > new Date(plan.legal_deadline)) {
      setConflicts(['Judgment date is after the legal deadline — this may be incorrect.']);
    }
  };

  const handleApproveAllFields = () => {
    setFieldApproved(true);
    setActiveTab('directive');
  };

  const handleDirectiveApprove = (dirId: string) => {
    setApprovedDirectives(prev => new Set(prev).add(dirId));
  };

  const handleApproveAllDirectives = () => {
    setDirectiveApproved(true);
    setActiveTab('case');
  };

  const canSignOff = user?.role === 'dept_head' || user?.role === 'legal_advisor';

  const handleSignOff = () => {
    alert('Case signed off successfully! Status updated to "verified".');
    navigate(`/cases/${id}`);
  };

  const headerFields = Object.entries(extracted.header_data);

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Header */}
      <motion.div variants={item}>
        <button onClick={() => navigate(`/cases/${id}`)} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
          <ArrowLeft size={16} /> Back to Case
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{t('review.title')}</h1>
            <p className="text-sm text-muted-foreground mt-1">{caseData.case_number}</p>
          </div>
          <span className={cn('rounded-full border px-3 py-1 text-xs font-medium', riskColor[plan.contempt_risk])}>
            {plan.contempt_risk} Risk
          </span>
        </div>
      </motion.div>

      {/* Tabs */}
      <motion.div variants={item}>
        <div className="flex gap-1 border-b border-slate-700/50 mb-6">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => !tab.locked && setActiveTab(tab.key)}
              disabled={tab.locked}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors relative',
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-500'
                  : tab.locked
                    ? 'border-transparent text-muted-foreground/50 cursor-not-allowed'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              {tab.locked ? <Lock size={12} /> : tab.icon}
              {tab.label}
              {tab.key === 'field' && fieldApproved && <CheckCircle size={12} className="text-green-400 ml-1" />}
              {tab.key === 'directive' && directiveApproved && <CheckCircle size={12} className="text-green-400 ml-1" />}
            </button>
          ))}
        </div>

        {/* Conflict Alert */}
        {conflicts.length > 0 && (
          <div className="mb-4">
            <ConflictAlert
              conflicts={conflicts}
              onDismiss={() => setConflicts([])}
              onRevert={() => { setEditValues({}); setConflicts([]); }}
            />
          </div>
        )}

        {/* Field Review */}
        {activeTab === 'field' && (
          <div className="space-y-8">
            <p className="text-sm text-muted-foreground">Review each extracted field. Approve, edit, or reject.</p>
            {headerFields.map(([key, value]) => {
              const isApproved = approvedFields.has(key);
              const editedValue = editValues[key];
              const displayValue = editedValue || value;

              return (
                <GlassCard key={key} className={cn(isApproved && 'border-green-500/30')}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-xs text-muted-foreground capitalize mb-1">{key.replace(/_/g, ' ')}</p>
                      {editingField === key ? (
                        <div className="flex gap-2">
                          <Input
                            type="text"
                            defaultValue={displayValue}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleFieldEdit(key, (e.target as HTMLInputElement).value);
                              if (e.key === 'Escape') setEditingField(null);
                            }}
                            className="flex-1 h-8 text-sm"
                            autoFocus
                          />
                          <Button variant="ghost" size="icon" onClick={() => setEditingField(null)} className="h-8 w-8 text-muted-foreground hover:text-foreground">
                            <X size={14} />
                          </Button>
                        </div>
                      ) : (
                        <p className="text-sm text-foreground">{displayValue}</p>
                      )}
                      {editedValue && <p className="text-[10px] text-blue-500 mt-1">✎ Edited</p>}
                    </div>
                    <div className="flex items-center gap-1.5 ml-4">
                      <ConfidenceBadge value={extracted.extraction_confidence} />
                      {!isApproved && (
                        <>
                          <button
                            onClick={() => handleFieldApprove(key)}
                            className="rounded-md bg-green-500/10 p-1.5 text-green-400 hover:bg-green-500/20 transition-colors"
                            title="Approve"
                          >
                            <Check size={14} />
                          </button>
                          <button
                            onClick={() => setEditingField(key)}
                            className="rounded-md bg-blue-500/10 p-1.5 text-blue-400 hover:bg-blue-500/20 transition-colors"
                            title="Edit"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => setRejectDialog(true)}
                            className="rounded-md bg-red-500/10 p-1.5 text-red-400 hover:bg-red-500/20 transition-colors"
                            title="Reject"
                          >
                            <X size={14} />
                          </button>
                        </>
                      )}
                      {isApproved && <CheckCircle size={16} className="text-green-400" />}
                    </div>
                  </div>
                </GlassCard>
              );
            })}

            <Button
              onClick={handleApproveAllFields}
              className="w-full bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg hover:from-green-500 hover:to-green-400 transition-all h-11"
            >
              Approve All Fields & Continue →
            </Button>
          </div>
        )}

        {/* Directive Review */}
        {activeTab === 'directive' && (
          <div className="space-y-8">
            <p className="text-sm text-muted-foreground">Review each court direction alongside its generated compliance action.</p>
            {extracted.court_directions.map((dir, i) => {
              const isApproved = approvedDirectives.has(dir.id);
              const action = plan.compliance_actions[i];
              return (
                <GlassCard key={dir.id} className={cn(isApproved && 'border-green-500/30')}>
                  <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                    <div>
                      <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                        <FileSearch size={12} /> Court Direction
                      </p>
                      <p className="text-sm text-foreground">{dir.verbatim_text}</p>
                      <div className="mt-2 flex items-center gap-2">
                        <span className="rounded-md bg-blue-500/10 px-2 py-0.5 text-xs text-blue-500">{dir.direction_type}</span>
                        <ConfidenceBadge value={dir.confidence} />
                      </div>
                    </div>
                    <div className="border-t border-border/50 pt-4 lg:border-t-0 lg:border-l lg:pl-4 lg:pt-0">
                      <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                        <GitBranch size={12} /> Generated Action
                      </p>
                      {action ? (
                        <>
                          <p className="text-sm text-foreground">{action.action}</p>
                          <span className="mt-2 inline-block rounded-md bg-purple-500/10 px-2 py-0.5 text-xs text-purple-500">
                            {action.responsible_department}
                          </span>
                        </>
                      ) : (
                        <p className="text-xs text-muted-foreground italic">No matching action</p>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-end gap-1.5 mt-3 pt-3 border-t border-slate-700/30">
                    {!isApproved ? (
                      <>
                        <button onClick={() => handleDirectiveApprove(dir.id)} className="rounded-md bg-green-500/10 px-3 py-1.5 text-xs text-green-400 hover:bg-green-500/20 transition-colors flex items-center gap-1">
                          <Check size={12} /> Approve
                        </button>
                        <button onClick={() => setRejectDialog(true)} className="rounded-md bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20 transition-colors flex items-center gap-1">
                          <X size={12} /> Reject
                        </button>
                      </>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-green-400"><CheckCircle size={12} /> Approved</span>
                    )}
                  </div>
                </GlassCard>
              );
            })}

            <Button
              onClick={handleApproveAllDirectives}
              className="w-full bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg hover:from-green-500 hover:to-green-400 transition-all h-11"
            >
              Approve All Directives & Continue →
            </Button>
          </div>
        )}

        {/* Case Review */}
        {activeTab === 'case' && (
          <div className="space-y-8">
            <GlassCard>
              <h3 className="text-base font-semibold text-foreground mb-6 flex items-center gap-3">
                <Stamp size={20} className="text-blue-500" />
                Case Summary — Final Sign-Off
              </h3>

              <div className="space-y-6">
                <div className="rounded-lg bg-muted/30 p-6 border border-border/30">
                  <p className="text-xs text-muted-foreground mb-2">Case Details</p>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="text-muted-foreground">Case:</span> <span className="text-foreground font-medium">{caseData.case_number}</span></div>
                    <div><span className="text-muted-foreground">Court:</span> <span className="text-foreground font-medium">{caseData.court}</span></div>
                    <div><span className="text-muted-foreground">Recommendation:</span> <span className={cn('font-medium', plan.recommendation === 'Comply' ? 'text-green-500' : 'text-amber-500')}>{plan.recommendation}</span></div>
                    <div><span className="text-muted-foreground">Risk:</span> <span className={cn('font-medium', riskColor[plan.contempt_risk].split(' ')[0])}>{plan.contempt_risk}</span></div>
                  </div>
                </div>

                <div className="rounded-lg bg-muted/30 p-6 border border-border/30">
                  <p className="text-sm text-muted-foreground mb-4">Review Status</p>
                  <div className="flex gap-6">
                    <span className="flex items-center gap-2 text-sm text-green-500 font-medium"><CheckCircle size={14} /> Field Review Complete</span>
                    <span className="flex items-center gap-2 text-sm text-green-500 font-medium"><CheckCircle size={14} /> Directive Review Complete</span>
                  </div>
                </div>

                <div className="rounded-lg bg-muted/30 p-6 border border-border/30">
                  <p className="text-sm text-muted-foreground mb-4">Compliance Actions ({plan.compliance_actions.length} steps)</p>
                  <div className="space-y-3">
                    {plan.compliance_actions.map(a => (
                      <p key={a.id} className="text-sm text-foreground py-1">
                        <span className="font-medium">{a.step_number}.</span> {a.action} — <span className="text-muted-foreground">{a.responsible_department}</span>
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </GlassCard>

            {canSignOff ? (
              <Button
                onClick={handleSignOff}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-500 text-white shadow-lg hover:from-green-500 hover:to-emerald-400 transition-all h-12 text-sm font-semibold"
              >
                <Stamp size={16} className="mr-2" />
                {t('review.signOff')} — Verify Case
              </Button>
            ) : (
              <div className="rounded-lg bg-muted/30 border border-border/50 p-4 text-center">
                <Lock size={20} className="mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">Only Department Heads and Legal Advisors can sign off.</p>
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Reject Dialog */}
      {rejectDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass-card p-6 w-full max-w-md mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
              <AlertTriangle size={18} className="text-red-500" />
              Reject — Provide Reason
            </h3>
            <Textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder={t('review.rejectReason')}
              className="min-h-[100px] mb-4"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setRejectDialog(false); setRejectReason(''); }}>
                {t('common.cancel')}
              </Button>
              <Button
                variant="destructive"
                onClick={() => { setRejectDialog(false); setRejectReason(''); alert('Rejection submitted.'); }}
                disabled={!rejectReason.trim()}
              >
                Submit Rejection
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
