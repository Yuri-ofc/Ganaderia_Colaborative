import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ResourceRoute({ recurso, recursos, children }) {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) return <div className="app-loading" aria-label="Cargando sesión"><span /></div>;
  if (!isAuthenticated) return <Navigate to="/" replace />;
  const requeridos = recursos || (recurso ? [recurso] : []);
  const permitido = user?.is_superuser || requeridos.some((codigo) => user?.recursos?.includes(codigo));
  if (!permitido) return <Navigate to="/propietario" replace />;
  return children;
}
