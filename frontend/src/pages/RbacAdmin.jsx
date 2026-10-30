import React, { useEffect, useMemo, useState } from 'react';
import Icon from '../components/Icon';
import {
  createResource,
  createRole,
  deleteResource,
  deleteRole,
  getRbacUsers,
  getResources,
  getRoles,
  updateRole,
  updateUserRoles,
} from '../services/rbacService';

const unwrap = (response) => response.data.results || response.data || [];
const messageFrom = (error, fallback) => {
  const data = error.response?.data;
  if (!data) return fallback;
  return data.detail || Object.values(data).flat().join(' ') || fallback;
};

export default function RbacAdmin() {
  const [roles, setRoles] = useState([]);
  const [resources, setResources] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedRoleId, setSelectedRoleId] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [roleName, setRoleName] = useState('');
  const [editRoleName, setEditRoleName] = useState('');
  const [resourceName, setResourceName] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const selectedRole = useMemo(
    () => roles.find((role) => role.Rol_ID === selectedRoleId) || null,
    [roles, selectedRoleId],
  );
  const selectedUser = useMemo(
    () => users.find((user) => user.id === selectedUserId) || null,
    [users, selectedUserId],
  );

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [rolesResponse, resourcesResponse, usersResponse] = await Promise.all([
        getRoles(), getResources(), getRbacUsers(),
      ]);
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

  const updateRolesLocal = (updated) => {
    setRoles((current) => current.map((role) => (role.Rol_ID === updated.Rol_ID ? updated : role)));
  };

  const saveRolePermissions = async (resourceId, enabled) => {
    if (!selectedRole) return;
    setSaving(true);
    setError('');
    const ids = selectedRole.recursos.map((resource) => resource.idrecurso);
    const recursos_ids = enabled ? [...ids, resourceId] : ids.filter((id) => id !== resourceId);
    try {
      const response = await updateRole(selectedRole.Rol_ID, { recursos_ids });
      updateRolesLocal(response.data);
      setNotice(`Permisos de ${response.data.Rol_nombre} actualizados.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudieron actualizar los permisos.'));
    } finally {
      setSaving(false);
    }
  };

  const createNewRole = async (event) => {
    event.preventDefault();
    const Rol_nombre = roleName.trim().toUpperCase();
    if (Rol_nombre.length !== 4) {
      setError('El código del rol debe tener exactamente cuatro caracteres.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const response = await createRole({ Rol_nombre, recursos_ids: [] });
      setRoles((current) => [...current, response.data].sort((a, b) => a.Rol_nombre.localeCompare(b.Rol_nombre)));
      setSelectedRoleId(response.data.Rol_ID);
      setRoleName('');
      setNotice(`Rol ${response.data.Rol_nombre} creado.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo crear el rol.'));
    } finally {
      setSaving(false);
    }
  };

  const renameRole = async (event) => {
    event.preventDefault();
    if (!selectedRole) return;
    const Rol_nombre = editRoleName.trim().toUpperCase();
    if (Rol_nombre.length !== 4) {
      setError('El código del rol debe tener exactamente cuatro caracteres.');
      return;
    }
    setSaving(true);
    try {
      const response = await updateRole(selectedRole.Rol_ID, { Rol_nombre });
      updateRolesLocal(response.data);
      setNotice(`Rol actualizado a ${response.data.Rol_nombre}.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo editar el rol.'));
    } finally {
      setSaving(false);
    }
  };

  const removeRole = async () => {
    if (!selectedRole || !window.confirm(`¿Eliminar el rol ${selectedRole.Rol_nombre}? También se quitará de sus usuarios.`)) return;
    setSaving(true);
    try {
      await deleteRole(selectedRole.Rol_ID);
      const kept = roles.filter((role) => role.Rol_ID !== selectedRole.Rol_ID);
      setRoles(kept);
      setSelectedRoleId(kept[0]?.Rol_ID || null);
      setUsers((current) => current.map((user) => ({
        ...user,
        roles: user.roles.filter((role) => role.Rol_ID !== selectedRole.Rol_ID),
      })));
      setNotice(`Rol ${selectedRole.Rol_nombre} eliminado.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo eliminar el rol.'));
    } finally {
      setSaving(false);
    }
  };

  const createNewResource = async (event) => {
    event.preventDefault();
    const nombre = resourceName.trim().toUpperCase();
    if (nombre.length !== 4) {
      setError('El código del recurso debe tener exactamente cuatro caracteres.');
      return;
    }
    setSaving(true);
    try {
      const response = await createResource({ nombre });
      setResources((current) => [...current, response.data].sort((a, b) => a.nombre.localeCompare(b.nombre)));
      setResourceName('');
      setNotice(`Recurso ${response.data.nombre} creado.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo crear el recurso.'));
    } finally {
      setSaving(false);
    }
  };

  const removeResource = async (resource) => {
    if (!window.confirm(`¿Eliminar el recurso ${resource.nombre}? Se quitará de todos los roles.`)) return;
    setSaving(true);
    try {
      await deleteResource(resource.idrecurso);
      setResources((current) => current.filter((item) => item.idrecurso !== resource.idrecurso));
      setRoles((current) => current.map((role) => ({
        ...role,
        recursos: role.recursos.filter((item) => item.idrecurso !== resource.idrecurso),
      })));
      setNotice(`Recurso ${resource.nombre} eliminado.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo eliminar el recurso.'));
    } finally {
      setSaving(false);
    }
  };

  const searchUsers = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const response = await getRbacUsers(search.trim());
      setUsers(unwrap(response));
      setSelectedUserId(null);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudo buscar usuarios.'));
    } finally {
      setSaving(false);
    }
  };

  const toggleUserRole = async (roleId, enabled) => {
    if (!selectedUser) return;
    const ids = selectedUser.roles.map((role) => role.Rol_ID);
    const roles_ids = enabled ? [...ids, roleId] : ids.filter((id) => id !== roleId);
    setSaving(true);
    try {
      const response = await updateUserRoles(selectedUser.id, roles_ids);
      setUsers((current) => current.map((user) => (user.id === selectedUser.id ? response.data : user)));
      setNotice(`Roles de ${response.data.username} actualizados.`);
    } catch (requestError) {
      setError(messageFrom(requestError, 'No se pudieron asignar los roles.'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page-loader"><span /></div>;

  return (
    <div className="page-content rbac-page" data-ui>
      <header className="page-title-row">
        <div>
          <h1>Control de acceso</h1>
          <p>Gestiona quién puede usar cada recurso del sistema.</p>
        </div>
        <button className="button button-primary" type="button" onClick={load} disabled={saving}>Actualizar</button>
      </header>

      {(error || notice) && <p className={`rbac-message ${error ? 'is-error' : 'is-success'}`} role={error ? 'alert' : 'status'}>{error || notice}</p>}

      <section className="metric-strip" aria-label="Resumen RBAC">
        <div><span>Roles configurados</span><strong>{roles.length}</strong><small>códigos de acceso activos</small></div>
        <div><span>Recursos protegidos</span><strong>{resources.length}</strong><small>verificados en el servidor</small></div>
        <div><span>Usuarios visibles</span><strong>{users.length}</strong><small>en esta consulta</small></div>
      </section>

      <div className="rbac-layout">
        <section className="rbac-panel">
          <div className="section-heading"><h2>Roles</h2><span>{roles.length} en total</span></div>
          <div className="rbac-role-list">
            {roles.map((role) => (
              <button key={role.Rol_ID} type="button" className={`rbac-role-row ${selectedRoleId === role.Rol_ID ? 'is-selected' : ''}`} onClick={() => setSelectedRoleId(role.Rol_ID)}>
                <span>{role.Rol_nombre}</span><small>{role.recursos.length} recursos</small>
              </button>
            ))}
          </div>
          <form className="rbac-inline-form" onSubmit={createNewRole}>
            <label htmlFor="new-role">Nuevo rol</label>
            <div><input id="new-role" value={roleName} maxLength="4" placeholder="EJ: AUDI" onChange={(event) => setRoleName(event.target.value)} /><button className="button" type="submit" disabled={saving}>Crear</button></div>
          </form>
        </section>

        <section className="rbac-panel rbac-permissions">
          {selectedRole ? <>
            <div className="section-heading"><div><h2>Permisos de {selectedRole.Rol_nombre}</h2><p>Selecciona los recursos que puede usar este rol.</p></div><button className="icon-button" type="button" title="Eliminar rol" onClick={removeRole} disabled={saving}><Icon name="trash" /></button></div>
            <form className="rbac-edit-role" onSubmit={renameRole}><label htmlFor="edit-role">Código del rol</label><div><input id="edit-role" value={editRoleName} maxLength="4" onChange={(event) => setEditRoleName(event.target.value)} /><button className="button" type="submit" disabled={saving}>Guardar</button></div></form>
            <div className="rbac-resource-grid">
              {resources.map((resource) => {
                const enabled = selectedRole.recursos.some((item) => item.idrecurso === resource.idrecurso);
                return <label key={resource.idrecurso} className="rbac-check-row"><input type="checkbox" checked={enabled} disabled={saving} onChange={(event) => saveRolePermissions(resource.idrecurso, event.target.checked)} /><span>{resource.nombre}</span><button type="button" className="icon-button" title={`Eliminar ${resource.nombre}`} onClick={() => removeResource(resource)} disabled={saving}><Icon name="trash" /></button></label>;
              })}
            </div>
            <form className="rbac-inline-form rbac-resource-form" onSubmit={createNewResource}>
              <label htmlFor="new-resource">Nuevo recurso</label>
              <div><input id="new-resource" value={resourceName} maxLength="4" placeholder="EJ: RPRT" onChange={(event) => setResourceName(event.target.value)} /><button className="button" type="submit" disabled={saving}>Agregar</button></div>
            </form>
          </> : <div className="empty-state"><Icon name="shield" /><h2>Selecciona un rol</h2><p>Crea o elige un rol para asignar sus recursos.</p></div>}
        </section>
      </div>

      <section className="rbac-users">
        <div className="section-heading"><div><h2>Asignación a usuarios</h2><p>Un usuario puede tener más de un rol.</p></div></div>
        <form className="rbac-search" onSubmit={searchUsers}><label htmlFor="rbac-user-search">Buscar por nombre de usuario</label><div><input id="rbac-user-search" value={search} placeholder="Escribe para filtrar" onChange={(event) => setSearch(event.target.value)} /><button className="button" type="submit" disabled={saving}><Icon name="search" />Buscar</button></div></form>
        <div className="rbac-users-grid">
          <div className="rbac-user-list" aria-label="Usuarios">
            {users.map((user) => <button type="button" key={user.id} className={`rbac-user-row ${selectedUserId === user.id ? 'is-selected' : ''}`} onClick={() => setSelectedUserId(user.id)}><span><strong>{user.username}</strong><small>{user.email || 'Sin correo registrado'}</small></span><em>{user.roles.map((role) => role.Rol_nombre).join(' · ') || 'Sin rol'}</em></button>)}
          </div>
          <div className="rbac-user-roles">
            {selectedUser ? <><h3>Roles de {selectedUser.username}</h3><p>Los cambios se guardan inmediatamente.</p>{roles.map((role) => <label key={role.Rol_ID} className="rbac-check-row"><input type="checkbox" checked={selectedUser.roles.some((item) => item.Rol_ID === role.Rol_ID)} disabled={saving} onChange={(event) => toggleUserRole(role.Rol_ID, event.target.checked)} /><span>{role.Rol_nombre}</span></label>)}</> : <p className="rbac-muted">Selecciona un usuario para asignarle roles.</p>}
          </div>
        </div>
      </section>

      <section className="rbac-pending" aria-label="Pendiente de implementación"><h2>Extensiones de dashboard</h2><p>Pendiente de implementación: reportes de auditoría y permisos específicos para nuevos módulos de visión computacional.</p></section>
    </div>
  );
}
