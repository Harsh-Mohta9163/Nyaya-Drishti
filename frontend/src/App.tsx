import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { CaseHeader } from './components/CaseHeader';
import { CaseOverview } from './components/CaseOverview';
import { VerifyActions } from './components/VerifyActions';
import { Dashboard } from './components/Dashboard';
import { CaseList } from './components/CaseList';
import { motion, AnimatePresence } from 'motion/react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage';
import { fetchCase, CaseData, fetchRecommendation } from './api/client';
import { shortPartyTitle, extractCoreName } from './utils/truncate';

import { Precedents } from './components/Precedents';

function MainApp() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<CaseData | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showToast, setShowToast] = useState(false);
  const [highlightedPage, setHighlightedPage] = useState<number | null>(null);
  const [caseDecision, setCaseDecision] = useState<'none' | 'appeal' | 'comply'>('none');
  const [recommendation, setRecommendation] = useState<any | null>(null);
  const [isGeneratingAnalysis, setIsGeneratingAnalysis] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Fetch selected case from backend when a case is clicked
  useEffect(() => {
    if (!selectedCaseId) {
      setSelectedCase(null);
      setRecommendation(null);
      return;
    }
    fetchCase(selectedCaseId)
      .then(data => {
        setSelectedCase(data);
        // Check if recommendation already exists in judgment's action_plan
        const judgment = data.judgments?.[0];
        if (judgment?.action_plan?.full_rag_recommendation) {
          setRecommendation(judgment.action_plan.full_rag_recommendation);
        } else {
          setRecommendation(null);
        }
      })
      .catch(err => console.error('Failed to fetch case:', err));
  }, [selectedCaseId]);

  const handleGenerateAnalysis = async () => {
    if (!selectedCaseId) return;
    setIsGeneratingAnalysis(true);
    try {
      const rec = await fetchRecommendation(selectedCaseId);
      setRecommendation(rec);
      // Reload actions from recommendation if available
      if (rec.action_plan?.immediate_actions) {
         setActions(rec.action_plan.immediate_actions.map((act: string, i: number) => ({
             id: `rec-${i}`,
             title: act.slice(0, 50) + (act.length > 50 ? '...' : ''),
             description: act,
             isVerified: false,
             source: "RAG Recommendation"
         })));
      }
    } catch (error) {
      console.error(error);
      alert("Analysis failed to generate");
    } finally {
      setIsGeneratingAnalysis(false);
    }
  };

  const updateCaseStatus = (decision: 'none' | 'appeal' | 'comply') => {
    setCaseDecision(decision);
  };

  // Build actions from the real extracted court_directions
  const judgment = selectedCase?.judgments?.[0];
  const directions = judgment?.court_directions ?? [];
  
  const [actions, setActions] = useState<any[]>([]);
  
  // Rebuild actions when a new case is selected
  useEffect(() => {
    if (!judgment) {
      setActions([]);
      return;
    }
    const dirs = judgment.court_directions ?? [];
    const mapped = dirs.map((d: any, i: number) => ({
      id: String(i + 1),
      title: d.heading || d.text?.slice(0, 60) || `Direction ${i + 1}`,
      source: d.source_location ? `Source: Page ${d.source_location.page}` : `Source: Direction ${i + 1}`,
      description: d.text || d.description || '',
      tags: d.departments || d.tags || [],
      dueDate: d.deadline || '',
      isVerified: false,
    }));
    setActions(mapped.length > 0 ? mapped : [{
      id: '1',
      title: 'Review Operative Order',
      source: 'Extracted from judgment',
      description: judgment.operative_order_text || 'No operative order extracted.',
      tags: ['Legal Review'],
      isVerified: false,
    }]);
  }, [judgment?.id]);

  const toggleAction = (id: string) => {
    setActions(actions.map(a => a.id === id ? { ...a, isVerified: !a.isVerified } : a));
  };

  const deleteAction = (id: string) => {
    setActions(actions.filter(a => a.id !== id));
  };

  const editAction = (id: string, description: string) => {
    setActions(actions.map(a => a.id === id ? { ...a, description } : a));
  };

  const verifyAll = () => {
    setActions(actions.map(a => ({ ...a, isVerified: true })));
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  const allVerified = actions.length > 0 && actions.every(a => a.isVerified);

  // Derived display values from real data
  const caseTitle = selectedCase
    ? shortPartyTitle(selectedCase.petitioner_name, selectedCase.respondent_name)
    : '';
  const caseRefId = selectedCase?.case_number || selectedCaseId || '';

  return (
    <div className="flex bg-surface-dim min-h-screen">
      {/* Toast Notification */}
      <AnimatePresence>
        {showToast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed bottom-10 left-1/2 -translate-x-1/2 z-[100]"
          >
            <div className="bg-green-500 text-on-primary-blue font-bold px-8 py-4 rounded-xl shadow-2xl flex items-center gap-3">
              <span className="material-symbols-outlined">verified</span>
              Successfully Verified Action Plan
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sidebar Navigation */}
      <Sidebar 
        currentView={currentView}
        onNavigate={(view) => {
          setCurrentView(view);
          if (view === 'cases') {
            setSelectedCaseId(null);
            setActiveTab('overview');
            setCaseDecision('none');
          }
        }}
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(c => !c)}
      />

      {/* Main Content Area */}
      <main className="flex-grow h-screen overflow-y-auto transition-[padding] duration-[250ms] ease-in-out" style={{ paddingLeft: sidebarCollapsed ? 72 : 280 }}>
        <AnimatePresence mode="wait">
          {currentView === 'dashboard' ? (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.02 }}
              transition={{ duration: 0.3 }}
              className="px-10"
            >
              <Dashboard onSelectCase={(id) => {
              setSelectedCaseId(id);
              setCurrentView('cases');
            }} />
            </motion.div>
          ) : currentView === 'cases' && !selectedCaseId ? (
            <motion.div
              key="case-list"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="px-10"
            >
              <CaseList 
                onSelectCase={(id) => setSelectedCaseId(id)}
              />
            </motion.div>
          ) : (
            <motion.div
              key={`case-detail-${selectedCaseId}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col min-h-full"
            >
              {/* Loading state */}
              {!selectedCase ? (
                <div className="flex items-center justify-center h-64">
                  <span className="material-symbols-outlined text-4xl animate-spin text-primary-blue opacity-40">progress_activity</span>
                </div>
              ) : (
                <>
                  {/* Top Header — populated from DB */}
                  <CaseHeader 
                    refId={caseRefId}
                    title={caseTitle}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    allVerified={allVerified}
                    onBack={() => setSelectedCaseId(null)}
                    decision={caseDecision}
                    onDecision={updateCaseStatus}
                  />

                  {/* Tab Content Area */}
                  <div className="px-10 pb-10 flex-grow">
                    <div className="mx-auto w-full max-w-[1440px]">
                      <AnimatePresence mode="wait">
                        <motion.div
                          key={activeTab}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ duration: 0.3 }}
                        >
                          {activeTab === 'overview' && (
                            <CaseOverview 
                              caseData={selectedCase}
                              verifiedActions={actions} 
                              onGoToVerify={() => setActiveTab('verify')}
                              recommendation={recommendation}
                              isGenerating={isGeneratingAnalysis}
                              onGenerateAnalysis={handleGenerateAnalysis}
                            />
                          )}
                          {activeTab === 'verify' && (
                            <VerifyActions 
                              actions={actions}
                              pdfUrl={judgment?.pdf_file || judgment?.pdf_storage_url}
                              highlightedPage={highlightedPage}
                              onActionClick={(page) => {
                                setHighlightedPage(null);
                                setTimeout(() => setHighlightedPage(page), 50);
                              }}
                              onToggle={toggleAction}
                              onDelete={deleteAction}
                              onEdit={editAction}
                              onVerifyAll={verifyAll}
                            />
                          )}
                          {activeTab === 'precedents' && (
                            <Precedents 
                              recommendation={recommendation}
                              isGenerating={isGeneratingAnalysis}
                              onGenerateAnalysis={handleGenerateAnalysis}
                            />
                          )}
                        </motion.div>
                      </AnimatePresence>
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route 
        path="/*" 
        element={
          isAuthenticated ? <MainApp /> : <Navigate to="/login" replace />
        } 
      />
    </Routes>
  );
}
