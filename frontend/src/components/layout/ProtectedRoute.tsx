import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import type { Role } from '@/types';
import LoadingSpinner from '@/components/common/LoadingSpinner';

interface ProtectedRouteProps {
  allowedRoles?: Role[];
  children: React.ReactNode;
}

export default function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) return <LoadingSpinner text="Authenticating..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
