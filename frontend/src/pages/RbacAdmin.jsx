import React, { useEffect, useMemo, useState } from 'react';
import Icon from '../components/Icon';
import { useEtiquetas } from '../context/EtiquetasContext';
import {
  LABELS_CHANGED_EVENT,
  createMenuOption,
  createRbacUser,
  createResource,
  createRole,
  deleteResource,
  deleteRole,
  getRbacUsers,
  getResources,
  getRoles,
  updateResource,
  updateRole,
  updateUserRoles,
} from '../services/rbacService';

const LABEL_MAX = 60;
const TABS = [
  { id: 'usuarios', label: 'Usuarios', hint: 'Crear cuentas y asignar roles' },
  { id: 'roles', label: 'Roles y permisos', hint: 'Qué opciones abre cada rol' },
  { id: 'opciones', label: 'Opciones del menú', hint: 'Nombres y opciones nuevas' },
];
const ROLE_HINT = { SUPR: 'Superadministrador', PROP: 'Propietario', ADMI: 'Administrador', OPER: 'Operario' };
const EMPTY_NEW_USER = { username: '', email: '', telefono: '', password: '', confirmPassword: '' };
const FIELD_ES = { username: 'Usuario', email: 'Correo', telefono: 'Teléfono', password: 'Contraseña', etiqueta: 'Etiqueta' };

const unwrap = (response) => response.data.results || response.data || [];
const byLabel = (a, b) => (a.etiqueta || a.nombre).localeCompare(b.etiqueta || b.nombre, 'es');
const messageFrom = (error, fallback) => {
  const data = error.response?.data;
  if (!data) return fallback;
  if (typeof data === 'string') return fallback;
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([field, value]) => {
      const text = Array.isArray(value) ? value.join(' ') : String(value);
      return FIELD_ES[field] ? `${FIELD_ES[field]}: ${text}` : text;
    })
    .join(' · ') || fallback;
};

export default function RbacAdmin() {
  const { etiqueta } = useEtiquetas();
  const [tab, setTab] = useState('usuarios');
  const [roles, setRoles] = useState([]);
  const [resources, setResources] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedRoleId, setSelectedRoleId] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [roleName, setRoleName] = useState('');
  const [editRoleName, setEditRoleName] = useState('');
  const [search, setSearch] = useState('');
  const [showNewUser, setShowNewUser] = useState(false);
  const [newUser, setNewUser] = useState(EMPTY_NEW_USER);
  const [editingResourceId, setEditingResourceId] = useState(null);
  const [resourceLabel, setResourceLabel] = useState('');
  const [optionLabel, setOptionLabel] = useState('');
  const [advancedCode, setAdvancedCode] = useState('');
  const [advancedLabel, setAdvancedLabel] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const selectedRole = useMemo(() => roles.find((role) => role.Rol_ID === selectedRoleId) || null, [roles, selectedRoleId]);
  const selectedUser = useMemo(() => users.find((user) => user.id === selectedUserId) || null, [users, selectedUserId]);
  const sortedResources = useMemo(() => [...resources].sort(byLabel), [resources]);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [rolesResponse, resourcesResponse, usersResponse] = await Promise.all([getRoles(), getResources(), getRbacUsers()]);
      const loadedRoles = unwrap(rolesResponse);
      setRoles(loadedRoles);
      setResources(unwrap(resourcesResponse));
      setUsers(unwrap(usersResponse));
      setSelectedRoleId((current) => current || loadedRoles[0]?.Rol_ID || null);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo cargar el control de acceso.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => { setEditRoleName(selectedRole?.Rol_nombre || ''); }, [selectedRole]);

  // Ejecuta una acción con el mismo manejo de estado y mensajes en todo el panel.
  const run = async (action, fallbackError) => {
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (requestError) {
      setError(messageFrom(requestError, fallbackError));
    } finally {
      setSaving(false);
    }
  };
  const announceLabelsChanged = () => window.dispatchEvent(new Event(LABELS_CHANGED_EVENT));
  const replaceRole = (updated) => setRoles((current) => current.map((role) => (role.Rol_ID === updated.Rol_ID ? updated : role)));

  /* ---------- Usuarios ---------- */
  const searchUsers = (event) => {
    event.preventDefault();
    run(async () => {
      const response = await getRbacUsers(search.trim());
      setUsers(unwrap(response));
      setSelectedUserId(null);
    }, 'No se pudo buscar usuarios.');
  };

  const updateNewUser = (event) => setNewUser((current) => ({ ...current, [event.target.name]: event.target.value }));

  const createUser = (event) => {
    event.preventDefault();
    if (newUser.password !== newUser.confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    run(async () => {
      const response = await createRbacUser({
        username: newUser.username.trim(),
        email: newUser.email.trim(),
        telefono: newUser.telefono.trim() || undefined,
        password: newUser.password,
      });
      setUsers((current) => [...current, response.data].sort((a, b) => a.username.localeCompare(b.username)));
      setSelectedUserId(response.data.id);
      setNewUser(EMPTY_NEW_USER);
      setShowNewUser(false);
      setNotice(`Usuario ${response.data.username} creado. Ya puede iniciar sesión; elige sus roles a la derecha.`);
    }, 'No se pudo crear el usuario.');
  };

  const toggleUserRole = (roleId, enabled) => {
    if (!selectedUser) return;
    const ids = selectedUser.roles.map((role) => role.Rol_ID);
    const roles_ids = enabled ? [...ids, roleId] : ids.filter((id) => id !== roleId);
    run(async () => {
      const response = await updateUserRoles(selectedUser.id, roles_ids);
      setUsers((current) => current.map((user) => (user.id === selectedUser.id ? response.data : user)));
      setNotice(`Roles de ${response.data.username} actualizados.`);
    }, 'No se pudieron asignar los roles.');
  };

  /* ---------- Roles y permisos ---------- */
  const toggleRoleResource = (resourceId, enabled) => {
    if (!selectedRole) return;
    const ids = selectedRole.recursos.map((resource) => resource.idrecurso);
    const recursos_ids = enabled ? [...ids, resourceId] : ids.filter((id) => id !== resourceId);
    run(async () => {
      const response = await updateRole(selectedRole.Rol_ID, { recursos_ids });
      replaceRole(response.data);
      setNotice(`Permisos de ${response.data.Rol_nombre} actualizados.`);
    }, 'No se pudieron actualizar los permisos.');
  };

  const createNewRole = (event) => {
    event.preventDefault();
    const Rol_nombre = roleName.trim().toUpperCase();
    if (Rol_nombre.length !== 4) {
      setError('El código del rol debe tener exactamente cuatro caracteres.');
      return;
    }
    run(async () => {
      const response = await createRole({ Rol_nombre, recursos_ids: [] });
      setRoles((current) => [...current, response.data].sort((a, b) => a.Rol_nombre.localeCompare(b.Rol_nombre)));
      setSelectedRoleId(response.data.Rol_ID);
      setRoleName('');
      setNotice(`Rol ${response.data.Rol_nombre} creado. Marca abajo las opciones que podrá usar.`);
    }, 'No se pudo crear el rol.');
  };

  const renameRole = (event) => {
    event.preventDefault();
    if (!selectedRole) return;
    const Rol_nombre = editRoleName.trim().toUpperCase();
    if (Rol_nombre.length !== 4) {
      setError('El código del rol debe tener exactamente cuatro caracteres.');
      return;
    }
    run(async () => {
      const response = await updateRole(selectedRole.Rol_ID, { Rol_nombre });
      replaceRole(response.data);
      setNotice(`Rol actualizado a ${response.data.Rol_nombre}.`);
    }, 'No se pudo editar el rol.');
  };

  const removeRole = () => {
    if (!selectedRole || !window.confirm(`¿Eliminar el rol ${selectedRole.Rol_nombre}? También se quitará de sus usuarios.`)) return;
    run(async () => {
      await deleteRole(selectedRole.Rol_ID);
      const kept = roles.filter((role) => role.Rol_ID !== selectedRole.Rol_ID);
      setRoles(kept);
      setSelectedRoleId(kept[0]?.Rol_ID || null);
      setUsers((current) => current.map((user) => ({ ...user, roles: user.roles.filter((role) => role.Rol_ID !== selectedRole.Rol_ID) })));
      setNotice(`Rol ${selectedRole.Rol_nombre} eliminado.`);
    }, 'No se pudo eliminar el rol.');
  };

  /* ---------- Opciones del menú ---------- */
  const startEditLabel = (resource) => {
    setEditingResourceId(resource.idrecurso);
    setResourceLabel(resource.etiqueta || resource.nombre);
  };

  const saveResourceLabel = (event) => {
    event.preventDefault();
    const nueva = resourceLabel.trim().replace(/\s+/g, ' ');
    if (!nueva) {
      setError('La etiqueta no puede estar vacía: es el nombre que se muestra en el menú.');
      return;
    }
    run(async () => {
      const response = await updateResource(editingResourceId, { etiqueta: nueva });
      const updated = response.data;
      setResources((current) => current.map((item) => (item.idrecurso === updated.idrecurso ? updated : item)));
      setRoles((current) => current.map((role) => ({
        ...role,
        recursos: role.recursos.map((item) => (item.idrecurso === updated.idrecurso ? updated : item)),
      })));
      setEditingResourceId(null);
      announceLabelsChanged();
      setNotice(`La opción ${updated.nombre} ahora se llama "${updated.etiqueta}" en el menú y en su página.`);
    }, 'No se pudo cambiar la etiqueta.');
  };

  const createOption = (event) => {
    event.preventDefault();
    const nueva = optionLabel.trim().replace(/\s+/g, ' ');
    if (!nueva) {
      setError('Escribe el nombre de la opción.');
      return;
    }
    run(async () => {
      const response = await createMenuOption(nueva);
      setResources((current) => [...current, response.data]);
      setOptionLabel('');
      announceLabelsChanged();
      setNotice(`Opción "${response.data.etiqueta}" creada. Para verla en el menú, asígnala a un rol en "Roles y permisos".`);
    }, 'No se pudo crear la opción.');
  };

  const createPermission = (event) => {
    event.preventDefault();
    const nombre = advancedCode.trim().toUpperCase();
    if (nombre.length !== 4) {
      setError('El código del permiso debe tener exactamente cuatro caracteres.');
      return;
    }
    const etiquetaNueva = advancedLabel.trim();
    run(async () => {
      const response = await createResource(etiquetaNueva ? { nombre, etiqueta: etiquetaNueva } : { nombre });
      setResources((current) => [...current, response.data]);
      setAdvancedCode('');
      setAdvancedLabel('');
      announceLabelsChanged();
      setNotice(`Permiso ${response.data.nombre} creado.`);
    }, 'No se pudo crear el permiso.');
  };

  const removeResource = (resource) => {
    if (!window.confirm(`¿Eliminar "${resource.etiqueta || resource.nombre}"? Se quitará de todos los roles y del menú.`)) return;
    run(async () => {
      await deleteResource(resource.idrecurso);
      setResources((current) => current.filter((item) => item.idrecurso !== resource.idrecurso));
      setRoles((current) => current.map((role) => ({ ...role, recursos: role.recursos.filter((item) => item.idrecurso !== resource.idrecurso) })));
      announceLabelsChanged();
      setNotice(`"${resource.etiqueta || resource.nombre}" eliminada.`);
    }, 'No se pudo eliminar.');
  };

  if (loading) return <div className="page-loader"><span /></div>;

  const menuOptions = resources.filter((resource) => resource.opcion_menu);

  return (
    <div className="page-content rbac-page" data-ui>
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('RBAC', 'Control de acceso')}</h1>
          <p>Un usuario tiene uno o más roles, y cada rol abre ciertas opciones del menú.</p>
        </div>
        <button className="button button-primary" type="button" onClick={load} disabled={saving}>Actualizar</button>
      </header>

      {(error || notice) && <p className={`rbac-message ${error ? 'is-error' : 'is-success'}`} role={error ? 'alert' : 'status'}>{error || notice}</p>}

      <section className="metric-strip" aria-label="Resumen de accesos">
        <div><span>Usuarios</span><strong>{users.length}</strong><small>en esta consulta</small></div>
        <div><span>Roles</span><strong>{roles.length}</strong><small>conjuntos de permisos</small></div>
        <div><span>Opciones y permisos</span><strong>{resources.length}</strong><small>{menuOptions.length} agregadas por ti</small></div>
      </section>

      <div className="rbac-tabs" role="tablist" aria-label="Secciones de control de acceso">
        {TABS.map((item, index) => (
          <button key={item.id} type="button" role="tab" id={`tab-${item.id}`} aria-selected={tab === item.id} aria-controls={`panel-${item.id}`} className={`rbac-tab ${tab === item.id ? 'is-active' : ''}`} onClick={() => setTab(item.id)}>
            <strong><em>{index + 1}</em>{item.label}</strong><small>{item.hint}</small>
          </button>
        ))}
      </div>

      {tab === 'usuarios' && (
        <section className="rbac-users" role="tabpanel" id="panel-usuarios" aria-labelledby="tab-usuarios">
          <div className="rbac-toolbar">
            <form className="rbac-search" onSubmit={searchUsers}>
              <label htmlFor="rbac-user-search">Buscar por nombre de usuario</label>
              <div><input id="rbac-user-search" value={search} placeholder="Escribe para filtrar" onChange={(event) => setSearch(event.target.value)} /><button className="button" type="submit" disabled={saving}><Icon name="search" />Buscar</button></div>
            </form>
            <button className="button button-primary" type="button" onClick={() => setShowNewUser((value) => !value)} aria-expanded={showNewUser}><Icon name={showNewUser ? 'close' : 'plus'} />{showNewUser ? 'Cerrar' : 'Crear usuario'}</button>
          </div>

          {showNewUser && (
            <form className="rbac-new-user" onSubmit={createUser}>
              <h3>Nueva cuenta</h3>
              <div className="form-grid">
                <label>Nombre de usuario<input name="username" required autoComplete="off" value={newUser.username} onChange={updateNewUser} placeholder="ej. ana_ganadera" /></label>
                <label>Teléfono <span>opcional</span><input name="telefono" type="tel" autoComplete="off" value={newUser.telefono} onChange={updateNewUser} placeholder="+57 300 000 0000" /></label>
              </div>
              <label>Correo electrónico<input name="email" type="email" required autoComplete="off" value={newUser.email} onChange={updateNewUser} placeholder="nombre@correo.com" /></label>
              <div className="form-grid">
                <label>Contraseña<input name="password" type="password" required minLength="8" autoComplete="new-password" value={newUser.password} onChange={updateNewUser} placeholder="Mínimo 8 caracteres" /></label>
                <label>Confirmar contraseña<input name="confirmPassword" type="password" required minLength="8" autoComplete="new-password" value={newUser.confirmPassword} onChange={updateNewUser} placeholder="Repite la contraseña" aria-invalid={newUser.confirmPassword && newUser.password !== newUser.confirmPassword ? 'true' : undefined} /></label>
              </div>
              <div className="rbac-new-user-actions"><button className="button" type="submit" disabled={saving}>{saving ? 'Creando…' : 'Crear cuenta'}</button><small>Inicia sesión con este correo y contraseña, igual que una cuenta registrada.</small></div>
            </form>
          )}

          <div className="rbac-users-grid">
            <div className="rbac-user-list" aria-label="Usuarios">
              {users.length === 0 && <p className="rbac-muted rbac-empty">No hay usuarios para mostrar.</p>}
              {users.map((user) => (
                <button type="button" key={user.id} className={`rbac-user-row ${selectedUserId === user.id ? 'is-selected' : ''}`} onClick={() => setSelectedUserId(user.id)}>
                  <span><strong>{user.username}</strong><small>{user.email || 'Sin correo registrado'}</small></span>
                  <em>{user.roles.map((role) => role.Rol_nombre).join(' · ') || 'Sin rol'}</em>
                </button>
              ))}
            </div>
            <div className="rbac-user-roles">
              {selectedUser ? (
                <>
                  <h3>Roles de {selectedUser.username}</h3>
                  <p>Marca los roles que tendrá. Se guarda al instante.</p>
                  {roles.map((role) => (
                    <label key={role.Rol_ID} className="rbac-check-row">
                      <input type="checkbox" checked={selectedUser.roles.some((item) => item.Rol_ID === role.Rol_ID)} disabled={saving} onChange={(event) => toggleUserRole(role.Rol_ID, event.target.checked)} />
                      <span>{role.Rol_nombre}<small className="rbac-code">{ROLE_HINT[role.Rol_nombre] || 'Rol personalizado'} · {role.recursos.length} opciones</small></span>
                    </label>
                  ))}
                </>
              ) : <p className="rbac-muted">Selecciona un usuario de la lista para elegir sus roles.</p>}
            </div>
          </div>
        </section>
      )}

      {tab === 'roles' && (
        <div className="rbac-layout" role="tabpanel" id="panel-roles" aria-labelledby="tab-roles">
          <section className="rbac-panel">
            <div className="section-heading"><h2>Roles</h2><span>{roles.length} en total</span></div>
            <div className="rbac-role-list">
              {roles.map((role) => (
                <button key={role.Rol_ID} type="button" className={`rbac-role-row ${selectedRoleId === role.Rol_ID ? 'is-selected' : ''}`} onClick={() => setSelectedRoleId(role.Rol_ID)}>
                  <span>{role.Rol_nombre}<small className="rbac-code">{ROLE_HINT[role.Rol_nombre] || 'Rol personalizado'}</small></span><small>{role.recursos.length} opciones</small>
                </button>
              ))}
            </div>
            <form className="rbac-inline-form" onSubmit={createNewRole}>
              <label htmlFor="new-role">Nuevo rol (código de 4 caracteres)</label>
              <div><input id="new-role" value={roleName} maxLength="4" placeholder="EJ: AUDI" onChange={(event) => setRoleName(event.target.value)} /><button className="button" type="submit" disabled={saving}>Crear</button></div>
            </form>
          </section>

          <section className="rbac-panel rbac-permissions">
            {selectedRole ? (
              <>
                <div className="section-heading">
                  <div><h2>Opciones que abre {selectedRole.Rol_nombre}</h2><p>Marca lo que podrá usar quien tenga este rol. Se guarda al instante.</p></div>
                  <button className="icon-button" type="button" title="Eliminar rol" onClick={removeRole} disabled={saving}><Icon name="trash" /></button>
                </div>
                <form className="rbac-edit-role" onSubmit={renameRole}>
                  <label htmlFor="edit-role">Código del rol</label>
                  <div><input id="edit-role" value={editRoleName} maxLength="4" onChange={(event) => setEditRoleName(event.target.value)} /><button className="button" type="submit" disabled={saving}>Guardar</button></div>
                </form>
                <div className="rbac-resource-grid">
                  {sortedResources.map((resource) => (
                    <label key={resource.idrecurso} className="rbac-check-row">
                      <input type="checkbox" checked={selectedRole.recursos.some((item) => item.idrecurso === resource.idrecurso)} disabled={saving} onChange={(event) => toggleRoleResource(resource.idrecurso, event.target.checked)} />
                      <span>{resource.etiqueta || resource.nombre}<small className="rbac-code">{resource.nombre}</small></span>
                    </label>
                  ))}
                </div>
              </>
            ) : <div className="empty-state"><Icon name="shield" /><h2>Selecciona un rol</h2><p>Crea o elige un rol para definir qué opciones abre.</p></div>}
          </section>
        </div>
      )}

      {tab === 'opciones' && (
        <div className="rbac-layout rbac-layout-options" role="tabpanel" id="panel-opciones" aria-labelledby="tab-opciones">
          <section className="rbac-panel">
            <div className="section-heading"><div><h2>Nombre de cada opción</h2><p>El nombre se muestra en el menú lateral y como título de su página.</p></div></div>
            <div className="rbac-option-list">
              {sortedResources.map((resource) => (editingResourceId === resource.idrecurso ? (
                <form key={resource.idrecurso} className="rbac-label-edit" onSubmit={saveResourceLabel}>
                  <label htmlFor={`label-${resource.idrecurso}`}>Nuevo nombre para {resource.nombre}</label>
                  <div>
                    <input id={`label-${resource.idrecurso}`} value={resourceLabel} maxLength={LABEL_MAX} autoFocus onChange={(event) => setResourceLabel(event.target.value)} />
                    <button className="button" type="submit" disabled={saving}>Guardar</button>
                    <button className="button" type="button" onClick={() => setEditingResourceId(null)}>Cancelar</button>
                  </div>
                  <small>{resourceLabel.length}/{LABEL_MAX} caracteres</small>
                </form>
              ) : (
                <div key={resource.idrecurso} className="rbac-option-row">
                  <span><strong>{resource.etiqueta || resource.nombre}</strong><small className="rbac-code">{resource.nombre} · {resource.opcion_menu ? 'Agregada por ti' : 'Predefinida'}</small></span>
                  <button type="button" className="icon-button" title={`Cambiar nombre de ${resource.etiqueta || resource.nombre}`} onClick={() => startEditLabel(resource)} disabled={saving}><Icon name="edit" /></button>
                  {resource.opcion_menu
                    ? <button type="button" className="icon-button is-danger" title={`Eliminar ${resource.etiqueta || resource.nombre}`} onClick={() => removeResource(resource)} disabled={saving}><Icon name="trash" /></button>
                    : <span className="rbac-option-spacer" aria-hidden="true" />}
                </div>
              )))}
            </div>
          </section>

          <section className="rbac-panel">
            <div className="section-heading"><div><h2>Agregar opción al dashboard</h2><p>Crea una entrada nueva en el menú lateral.</p></div></div>
            <form className="rbac-inline-form rbac-new-option" onSubmit={createOption}>
              <label htmlFor="new-option">Nombre de la opción</label>
              <div><input id="new-option" value={optionLabel} maxLength={LABEL_MAX} placeholder="Ej: Reportes de campo" onChange={(event) => setOptionLabel(event.target.value)} /><button className="button" type="submit" disabled={saving}><Icon name="plus" />Agregar</button></div>
              <small>Mostrará "Funcionalidad en proceso de Implementación". Después, asígnala a un rol en "Roles y permisos" para que aparezca en el menú.</small>
            </form>
            <details className="rbac-advanced">
              <summary>Avanzado: crear un permiso sin opción de menú</summary>
              <form className="rbac-inline-form" onSubmit={createPermission}>
                <label htmlFor="advanced-code">Código (4 caracteres) y nombre opcional</label>
                <div><input id="advanced-code" value={advancedCode} maxLength="4" placeholder="EJ: RPRT" onChange={(event) => setAdvancedCode(event.target.value)} /><input aria-label="Nombre del permiso" value={advancedLabel} maxLength={LABEL_MAX} placeholder="Nombre (opcional)" onChange={(event) => setAdvancedLabel(event.target.value)} /><button className="button" type="submit" disabled={saving}>Crear</button></div>
              </form>
            </details>
          </section>
        </div>
      )}
    </div>
  );
}
