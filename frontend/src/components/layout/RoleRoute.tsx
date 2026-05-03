import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import type { Role } from '@/types';

interface RoleRouteProps {
  allowedRoles: Role[];
}

export default function RoleRoute({ allowedRoles }: RoleRouteProps) {
  const { user } = useAuth();

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
