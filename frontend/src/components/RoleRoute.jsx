import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Dashboard al que se envía a cada rol cuando intenta entrar a una ruta que no le corresponde.
const rutaDashboardPorRol = {
  propietario: '/propietario',
  administrador: '/administracion',
  operario: '/operario',
};

export default function RoleRoute({ rolesPermitidos, recurso, children }) {
  const { isAuthenticated, loading, rolActivo, user, fincas } = useAuth();
  const { pathname } = useLocation();

  if (loading) {
    return <div className="app-loading" aria-label="Cargando sesión"><span /></div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const tieneRecurso = !recurso || user?.is_superuser || user?.recursos?.includes(recurso);
  const rolPermitido = user?.is_superuser || rolActivo === 'superadmin'
    || rolesPermitidos.includes(rolActivo);

  if (tieneRecurso && rolPermitido) {
    return children;
  }

  const destino = rutaDashboardPorRol[rolActivo] || '/propietario';

  // Cuenta nueva: todavía no tiene fincas, membresías ni recursos FINC. El
  // panel de propietario es el único punto desde el que puede crear su
  // primera finca, así que se permite mientras no exista ninguna. El backend
  // sigue aplicando sus propias reglas y no se conceden permisos por esto.
  const esArranque = !fincas.length && destino === '/propietario' && pathname === destino;
  if (esArranque) {
    return children;
  }

  // Último recurso contra bucles: si el destino ya es la ruta actual, se
  // renderiza en lugar de redirigir sobre el mismo lugar indefinidamente.
  if (destino === pathname) {
    return children;
  }

  return <Navigate to={destino} replace />;
}
