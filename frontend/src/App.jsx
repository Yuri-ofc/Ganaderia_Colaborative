import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Fincas from './pages/Fincas';
import Bovinos from './pages/Bovinos';
import Membresias from './pages/Membresias';
import Invitaciones from './pages/Invitaciones';
import RbacAdmin from './pages/RbacAdmin';
import DashboardLayout from './components/DashboardLayout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleRoute from './components/RoleRoute';
import ResourceRoute from './components/ResourceRoute';
import { AuthProvider } from './context/AuthContext';

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
        <Route path="/" element={<Login />} />
        <Route path="/registro" element={<Signup />} />
        <Route path="/signup" element={<Navigate to="/registro" replace />} />
        <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
          <Route
            path="/propietario"
            element={
              <RoleRoute rolesPermitidos={ROLES_SOLO_PROPIETARIO}>
                <Dashboard audience="propietario" />
              </RoleRoute>
            }
          />
          <Route
            path="/administracion"
            element={
              <RoleRoute rolesPermitidos={ROLES_GESTION}>
                <Dashboard audience="administrador" />
              </RoleRoute>
            }
          />
          <Route
            path="/operario"
            element={
              <RoleRoute rolesPermitidos={ROLES_TODOS}>
                <Dashboard audience="operario" />
              </RoleRoute>
            }
          />
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
              <RoleRoute rolesPermitidos={ROLES_TODOS}>
                <Bovinos />
              </RoleRoute>
            }
          />
          <Route
            path="/miembros"
            element={
              <RoleRoute rolesPermitidos={ROLES_SOLO_PROPIETARIO}>
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
              <RoleRoute rolesPermitidos={ROLES_TODOS}>
                <Invitaciones />
              </RoleRoute>
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
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
