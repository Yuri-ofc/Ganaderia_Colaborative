import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Dashboard al que se envía a cada rol cuando intenta entrar a una ruta que no le corresponde.
const rutaDashboardPorRol = {
  propietario: '/propietario',
  administrador: '/administracion',
  operario: '/operario',
};

export default function RoleRoute({ rolesPermitidos, children }) {
  const { isAuthenticated, loading, rolActivo } = useAuth();

  if (loading) {
    return <div className="app-loading" aria-label="Cargando sesión"><span /></div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (!rolesPermitidos.includes(rolActivo)) {
    // Fallback a /propietario cuando aún no se ha resuelto el rol (p. ej. la primera finca sin crearse).
    const destino = rutaDashboardPorRol[rolActivo] || '/propietario';
    return <Navigate to={destino} replace />;
  }

  return children;
}
