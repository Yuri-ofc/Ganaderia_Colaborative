import React, { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Icon from './Icon';
import SelectorFinca from './SelectorFinca';

// Ruta de "Resumen" (dashboard) correspondiente a cada rol.
const rutaResumenPorRol = {
  propietario: '/propietario',
  administrador: '/administracion',
  operario: '/operario',
};

// Items secundarios del menú, con los roles que pueden verlos EN LA FINCA ACTIVA.
const itemsSecundarios = [
  { to: '/fincas', label: 'Fincas', icon: 'farm', rolesPermitidos: ['propietario', 'administrador', 'operario'] },
  { to: '/bovinos', label: 'Bovinos', icon: 'cattle', rolesPermitidos: ['propietario', 'administrador', 'operario'] },
  { to: '/miembros', label: 'Equipo', icon: 'people', rolesPermitidos: ['propietario'] },
  // Crear invitaciones es solo del propietario, pero aceptar una lo hace
  // cualquier rol (quien fue invitado no suele ser propietario de nada).
  { to: '/invitaciones', label: 'Invitaciones', icon: 'mail', rolesPermitidos: ['propietario', 'administrador', 'operario'] },
];

export default function DashboardLayout() {
  const { handleLogout, user, rolActivo } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const initial = (user?.username || 'U').slice(0, 1).toUpperCase();

  const onLogout = async () => {
    await handleLogout();
    navigate('/', { replace: true });
  };

  // "Resumen" apunta al dashboard del rol que tienes EN LA FINCA ACTIVA.
  const resumenItem = rolActivo
    ? { to: rutaResumenPorRol[rolActivo] || '/propietario', label: 'Resumen', icon: 'grid', end: false }
    : null;

  const itemsVisibles = itemsSecundarios.filter((item) => item.rolesPermitidos.includes(rolActivo));
  const itemRbac = (user?.is_superuser || user?.recursos?.includes('RBAC'))
    ? { to: '/rbac', label: 'Control de acceso', icon: 'shield', end: true }
    : null;
  const todosLosItems = [...(resumenItem ? [resumenItem] : []), ...itemsVisibles, ...(itemRbac ? [itemRbac] : [])];

  const currentTitle = todosLosItems.find((item) => location.pathname === item.to)?.label || 'Ganadería';

  // Enlace de la marca: siempre lleva al Resumen del rol actual.
  const rutaMarca = resumenItem?.to || '/propietario';

  return (
    <div className="app-shell">
      {sidebarOpen && <button className="app-scrim" aria-label="Cerrar menú" onClick={() => setSidebarOpen(false)} />}
      <aside className={`app-sidebar ${sidebarOpen ? 'is-open' : ''}`}>
        <NavLink to={rutaMarca} className="app-brand" onClick={() => setSidebarOpen(false)}>
          <img src="/logo.jpeg" alt="Ganadería" />
          <span>Ganadería</span>
        </NavLink>
        <nav className="app-nav" aria-label="Navegación principal">
          {todosLosItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} onClick={() => setSidebarOpen(false)} className={({ isActive }) => `app-nav-link ${isActive ? 'is-active' : ''}`}>
              <Icon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="app-account">
          <div className="avatar">{initial}</div>
          <div className="min-w-0">
            <p>{user?.username || 'Usuario'}</p>
            <span>{user?.email || 'Sesión activa'}</span>
          </div>
          <button className="icon-button" onClick={onLogout} title="Cerrar sesión" aria-label="Cerrar sesión"><Icon name="logout" /></button>
        </div>
      </aside>
      <section className="app-workspace">
        <header className="app-topbar">
          <button className="app-menu-button" onClick={() => setSidebarOpen(true)} aria-label="Abrir menú"><Icon name="menu" /></button>
          <p>{currentTitle}</p>
          <div className="app-topbar-user">
            <SelectorFinca />
            <span>{user?.username || 'Usuario'}</span>
            <div className="avatar">{initial}</div>
          </div>
        </header>
        <main className="app-sheet"><Outlet /></main>
      </section>
    </div>
  );
}
