import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import '@/lib/i18n';

import PageShell from '@/components/layout/PageShell';
import ProtectedRoute from '@/components/layout/ProtectedRoute';
import RoleRoute from '@/components/layout/RoleRoute';

import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';
import CasesListPage from '@/pages/CasesListPage';
import CaseDetailPage from '@/pages/CaseDetailPage';
import ActionPlanPage from '@/pages/ActionPlanPage';
import ReviewPage from '@/pages/ReviewPage';
import AnalyticsPage from '@/pages/AnalyticsPage';
import NotificationsPage from '@/pages/NotificationsPage';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              {/* Public */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected — all roles */}
              <Route element={<ProtectedRoute><PageShell /></ProtectedRoute>}>
                <Route path="/" element={<Navigate to="/dashboard" />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/cases" element={<CasesListPage />} />
                <Route path="/cases/:id" element={<CaseDetailPage />} />
                <Route path="/cases/:id/action-plan" element={<ActionPlanPage />} />
                <Route path="/notifications" element={<NotificationsPage />} />

                {/* Reviewer + Dept Head + Legal Advisor only */}
                <Route element={<RoleRoute allowedRoles={['reviewer', 'dept_head', 'legal_advisor']} />}>
                  <Route path="/cases/:id/review" element={<ReviewPage />} />
                  <Route path="/reviews" element={<ReviewPage />} />
                </Route>

                {/* Dept Officer + Dept Head + Legal Advisor only */}
                <Route element={<RoleRoute allowedRoles={['dept_officer', 'dept_head', 'legal_advisor']} />}>
                  <Route path="/analytics" element={<AnalyticsPage />} />
                </Route>
              </Route>

              {/* 404 */}
              <Route path="*" element={<Navigate to="/dashboard" />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
