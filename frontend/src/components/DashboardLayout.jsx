import React, { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Icon from './Icon';
import { useEtiquetas } from '../context/EtiquetasContext';
import SelectorFinca from './SelectorFinca';

// Ruta de "Resumen" (dashboard) correspondiente a cada rol.
const rutaResumenPorRol = {
  propietario: '/propietario',
  administrador: '/administracion',
  operario: '/operario',
  superadmin: '/superadmin',
};

// El menú es una proyección de los recursos efectivos que entrega el backend.
// rolFinca solo restringe acciones cuyo contexto lo exige; nunca sustituye la
// validación del servidor.
// Recuperación no tiene entrada propia: su acción vive dentro de Respaldos,
// donde está el archivo que se va a restaurar (el servidor sigue exigiendo el
// recurso RECU para ejecutarla).
const itemsSecundarios = [
  { to: '/fincas', label: 'Fincas', icon: 'farm', recurso: 'FINC', bootstrap: true },
  { to: '/bovinos', label: 'Bovinos', icon: 'cattle', recurso: 'BOVI' },
  { to: '/mediciones', label: 'Mediciones', icon: 'chart', recurso: 'MEDI' },
  { to: '/pesajes', label: 'Pesajes', icon: 'scale', recurso: 'PESA' },
  { to: '/vision', label: 'Visión computacional', icon: 'camera', recurso: 'VCOM' },
  { to: '/miembros', label: 'Equipo', icon: 'people', recurso: 'MIEM', rolesFinca: ['propietario', 'administrador'] },
  { to: '/invitaciones', label: 'Invitaciones', icon: 'mail', recurso: 'INVT', rolesFinca: ['propietario', 'administrador'] },
  { to: '/sincronizacion', label: 'Sincronización', icon: 'sync', recurso: 'SYNC' },
  { to: '/respaldos', label: 'Respaldos', icon: 'archive', recurso: 'RESP' },
  { to: '/exportaciones', label: 'Exportaciones', icon: 'download', recurso: 'EXPO' },
];

export default function DashboardLayout() {
  const { handleLogout, user, rolActivo } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { etiqueta, opciones } = useEtiquetas();
  const initial = (user?.username || 'U').slice(0, 1).toUpperCase();

  const onLogout = async () => {
    await handleLogout();
    navigate('/', { replace: true });
  };

  // "Resumen" apunta al dashboard del rol que tienes EN LA FINCA ACTIVA.
  const resumenItem = rolActivo
    ? { to: rutaResumenPorRol[rolActivo] || '/propietario', label: 'Resumen', icon: 'grid', end: false }
    : null;

  const esSuperadmin = user?.is_superuser || user?.roles?.includes('SUPR');
  const tieneRecurso = (recurso) => esSuperadmin || user?.recursos?.includes(recurso);
  const itemsVisibles = itemsSecundarios.map((item) => ({ ...item, label: etiqueta(item.recurso, item.label) })).filter((item) => (
    (tieneRecurso(item.recurso) || (item.bootstrap && !user?.recursos?.length))
    && (!item.rolesFinca || esSuperadmin || item.rolesFinca.includes(rolActivo))
  ));
  const itemRbac = (user?.is_superuser || user?.recursos?.includes('RBAC'))
    ? { to: '/rbac', label: etiqueta('RBAC', 'Control de acceso'), icon: 'shield', end: true }
    : null;
  // Opciones agregadas desde Control de acceso: se ven con el recurso asignado.
  const itemsNuevos = opciones
    .filter((opcion) => tieneRecurso(opcion.nombre))
    .map((opcion) => ({ to: `/opcion/${opcion.nombre}`, label: opcion.etiqueta, icon: 'grid' }));
  const todosLosItems = [...(resumenItem ? [resumenItem] : []), ...itemsVisibles, ...itemsNuevos, ...(itemRbac ? [itemRbac] : [])];

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
