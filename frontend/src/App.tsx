import React, { useState } from 'react';
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

import { Precedents } from './components/Precedents';

function MainApp() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showToast, setShowToast] = useState(false);
  const [highlightedPage, setHighlightedPage] = useState<number | null>(null);
  const [caseDecision, setCaseDecision] = useState<'none' | 'appeal' | 'comply'>('none');
  
  const [cases, setCases] = useState([
    { id: 'ND-2023-SP-882', client: 'ABC Industries vs. State of Karnataka', court: 'Supreme Court of Delhi', type: 'Writ Petition', status: 'Review Pending', risk: 'High', days: 4 },
    { id: 'SLP/4567/2024', client: 'Ramaiah & Sons vs. Revenue Department', court: 'Karnataka High Court', type: 'SLP', status: 'Review Pending', risk: 'Medium', days: 12 },
    { id: 'CIV-9901-2023', client: 'Global Tech vs. Registrar of Patents', court: 'Bombay High Court', type: 'Appeal', status: 'Verified', risk: 'Low', days: 28 },
    { id: 'HC-2023-14', client: 'Sharma Corp vs. Union of India', court: 'Supreme Court of India', type: 'Civil Appeal', status: 'Review Pending', risk: 'High', days: 2 }
  ]);

  const updateCaseStatus = (decision: 'none' | 'appeal' | 'comply') => {
    setCaseDecision(decision);
    if (decision !== 'none' && selectedCaseId) {
      setCases(prev => prev.map(c => 
        c.id === selectedCaseId 
          ? { ...c, status: decision === 'appeal' ? 'Appeal' : 'Comply' } 
          : c
      ));
    }
  };

  const [actions, setActions] = useState([
    { 
      id: '1',
      title: "Deposit 50% Disputed Tax",
      source: "Source: Page 1, Para 2",
      description: "Ensure respondent company (Sharma Corp Pvt. Ltd.) deposits 50% of the disputed tax amount as directed by the Supreme Court.",
      tags: ['Finance Dept'],
      dueDate: "10 Dec 2023",
      isVerified: true
    },
    { 
      id: '2',
      title: "Submit Regulatory Compliance Report",
      source: "Source: Page 1, Para 3",
      description: "Review regulatory compliance of Sharma Corp for FY 2020-2022 and prepare a preliminary report for submission.",
      tags: ['Ministry of Corp Affairs', 'Legal Review'],
      dueDate: "11 Jan 2024",
      isVerified: false
    },
    { 
      id: '3',
      title: "Proceed with Asset Attachment",
      source: "Source: Page 1, Para 4",
      description: "Interim stay vacated. Initiate attachment of specified assets as listed in Annexure A of the original order.",
      tags: ['Enforcement Dir.'],
      isHighPriority: true,
      isVerified: false
    }
  ]);

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
          }
        }}
      />

      {/* Main Content Area */}
      <main className="flex-grow pl-[280px] h-screen overflow-y-auto">
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
                cases={cases}
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
              {/* Top Header */}
              <CaseHeader 
                refId={selectedCaseId || "ND-2023-SP-882"} 
                title="ABC Industries vs. State of Karnataka" 
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
                          verifiedActions={actions} 
                          onGoToVerify={() => setActiveTab('verify')}
                        />
                      )}
                      {activeTab === 'verify' && (
                        <VerifyActions 
                          actions={actions}
                          highlightedPage={highlightedPage}
                          onActionClick={(page) => {
                            setHighlightedPage(null); // Reset first to trigger effect if same page
                            setTimeout(() => setHighlightedPage(page), 50);
                          }}
                          onToggle={toggleAction}
                          onDelete={deleteAction}
                          onEdit={editAction}
                          onVerifyAll={verifyAll}
                        />
                      )}
                      {activeTab === 'precedents' && (
                        <Precedents />
                      )}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
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

