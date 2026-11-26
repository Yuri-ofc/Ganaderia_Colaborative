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
import Mediciones from './pages/Mediciones';
import Pesajes from './pages/Pesajes';
import Vision from './pages/Vision';
import Sincronizacion from './pages/Sincronizacion';
import Respaldos from './pages/Respaldos';
import Exportaciones from './pages/Exportaciones';
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
          <Route
            path="/mediciones"
            element={
              <RoleRoute rolesPermitidos={ROLES_TODOS} recurso="MEDI">
                <Mediciones />
              </RoleRoute>
            }
          />
          <Route
            path="/pesajes"
            element={
              <RoleRoute rolesPermitidos={ROLES_TODOS} recurso="PESA">
                <Pesajes />
              </RoleRoute>
            }
          />
          <Route path="/vision" element={<ResourceRoute recurso="VCOM"><Vision /></ResourceRoute>} />
          <Route path="/sincronizacion" element={<ResourceRoute recurso="SYNC"><Sincronizacion /></ResourceRoute>} />
          <Route path="/respaldos" element={<ResourceRoute recurso="RESP"><Respaldos /></ResourceRoute>} />
          <Route path="/exportaciones" element={<ResourceRoute recurso="EXPO"><Exportaciones /></ResourceRoute>} />
          {/* Restaurar vive dentro de Respaldos; la ruta anterior se conserva
              para no romper enlaces guardados. */}
          <Route path="/recuperacion" element={<Navigate to="/respaldos" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
