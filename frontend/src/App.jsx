import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Fincas from './pages/Fincas';
import Bovinos from './pages/Bovinos';
import Membresias from './pages/Membresias';
import Invitaciones from './pages/Invitaciones';
import RbacAdmin from './pages/RbacAdmin';
import OpcionPersonalizada from './pages/OpcionPersonalizada';
import ModulePlaceholder from './pages/ModulePlaceholder';
import DashboardLayout from './components/DashboardLayout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleRoute from './components/RoleRoute';
import ResourceRoute from './components/ResourceRoute';
import { AuthProvider } from './context/AuthContext';
import { EtiquetasProvider } from './context/EtiquetasContext';

// Reglas de acceso por rol (RF-04, RNF-11): /miembros e /invitaciones solo las
// gestiona el propietario; /administracion la ven propietario y administrador.
const ROLES_TODOS = ['propietario', 'administrador', 'operario'];
const ROLES_GESTION = ['propietario', 'administrador'];
const ROLES_SOLO_PROPIETARIO = ['propietario'];

function App() {
  return (
    <Router>
      <AuthProvider>
      <Routes>
        <Route path="/inicio" element={<Landing />} />
        <Route path="/" element={<Login />} />
        <Route path="/registro" element={<Signup />} />
        <Route path="/signup" element={<Navigate to="/registro" replace />} />
        <Route element={<ProtectedRoute><EtiquetasProvider><DashboardLayout /></EtiquetasProvider></ProtectedRoute>}>
          <Route
            path="/propietario"
            element={
              <RoleRoute rolesPermitidos={ROLES_SOLO_PROPIETARIO} recurso="FINC">
                <Dashboard audience="propietario" />
              </RoleRoute>
            }
          />
          <Route
            path="/administracion"
            element={
              <RoleRoute rolesPermitidos={ROLES_GESTION} recurso="FINC">
                <Dashboard audience="administrador" />
              </RoleRoute>
            }
          />
          <Route
            path="/operario"
            element={
              <RoleRoute rolesPermitidos={ROLES_TODOS} recurso="FINC">
                <Dashboard audience="operario" />
              </RoleRoute>
            }
          />
          <Route path="/superadmin" element={<ResourceRoute recurso="FINC"><Dashboard audience="superadmin" /></ResourceRoute>} />
          <Route path="/dashboard" element={<Navigate to="/propietario" replace />} />
          <Route
            path="/fincas"
            element={
              <RoleRoute rolesPermitidos={ROLES_TODOS}>
                <Fincas />
              </RoleRoute>
            }
          />
          <Route
            path="/bovinos"
            element={
              <RoleRoute rolesPermitidos={ROLES_TODOS} recurso="BOVI">
                <Bovinos />
              </RoleRoute>
            }
          />
          <Route
            path="/miembros"
            element={
              <RoleRoute rolesPermitidos={ROLES_GESTION} recurso="MIEM">
                <Membresias />
              </RoleRoute>
            }
          />
          <Route
            path="/invitaciones"
            element={
              // Crear/gestionar invitaciones es solo del propietario (ya filtrado
              // dentro de Invitaciones.jsx), pero ACEPTAR una invitación lo hace
              // quien fue invitado, que normalmente no es propietario de nada
              // todavía. Por eso la ruta queda abierta a los tres roles.
              <Invitaciones />
            }
          />
          <Route
            path="/permisos"
            element={<Navigate to="/rbac" replace />}
          />
          <Route
            path="/rbac"
            element={<ResourceRoute recurso="RBAC"><RbacAdmin /></ResourceRoute>}
          />
          <Route path="/opcion/:codigo" element={<OpcionPersonalizada />} />
          <Route path="/vision" element={<ResourceRoute recurso="VCOM"><ModulePlaceholder recurso="VCOM" endpoint="/modules/vision/" title="Visión computacional" description="Estructura de captura y análisis preparada para el módulo de IA." extension="apps.vision" /></ResourceRoute>} />
          <Route path="/sincronizacion" element={<ResourceRoute recurso="SYNC"><ModulePlaceholder recurso="SYNC" endpoint="/sync-changes/" title="Sincronización" description="Punto de integración para la cola offline y sus conflictos." extension="apps.sync" /></ResourceRoute>} />
          <Route path="/respaldos" element={<ResourceRoute recurso="RESP"><ModulePlaceholder recurso="RESP" endpoint="/backups/" title="Respaldos" description="Punto de integración para copias verificadas de la finca." extension="apps.backups" /></ResourceRoute>} />
          <Route path="/exportaciones" element={<ResourceRoute recurso="EXPO"><ModulePlaceholder recurso="EXPO" endpoint="/modules/exports/" title="Exportaciones" description="Contrato reservado para exportar datos sin exponer lógica todavía." extension="apps.backups.exports" /></ResourceRoute>} />
          <Route path="/recuperacion" element={<ResourceRoute recurso="RECU"><ModulePlaceholder recurso="RECU" endpoint="/modules/recovery/" title="Recuperación" description="Contrato reservado para recuperar respaldos verificados." extension="apps.backups.recovery" /></ResourceRoute>} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
