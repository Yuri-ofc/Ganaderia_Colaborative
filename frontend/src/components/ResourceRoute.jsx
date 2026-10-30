import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ResourceRoute({ recurso, children }) {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) return <div className="app-loading" aria-label="Cargando sesión"><span /></div>;
  if (!isAuthenticated) return <Navigate to="/" replace />;
  if (!user?.is_superuser && !user?.recursos?.includes(recurso)) return <Navigate to="/propietario" replace />;
  return children;
}
