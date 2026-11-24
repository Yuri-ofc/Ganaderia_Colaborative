import api from './api';

export const getRoles = () => api.get('/rbac/roles/');
export const createRole = (data) => api.post('/rbac/roles/', data);
export const updateRole = (id, data) => api.patch(`/rbac/roles/${id}/`, data);
export const deleteRole = (id) => api.delete(`/rbac/roles/${id}/`);

export const getResources = () => api.get('/rbac/resources/');
export const createResource = (data) => api.post('/rbac/resources/', data);
export const updateResource = (id, data) => api.patch(`/rbac/resources/${id}/`, data);
export const deleteResource = (id) => api.delete(`/rbac/resources/${id}/`);

export const createMenuOption = (etiqueta) => api.post('/rbac/opciones/', { etiqueta });
export const getResourceLabels = () => api.get('/rbac/etiquetas/');

export const getRbacUsers = (q = '') => api.get('/rbac/usuarios/', { params: q ? { q } : {} });
export const updateUserRoles = (id, roles_ids) => api.put(`/rbac/usuarios/${id}/roles/`, { roles_ids });
export const createRbacUser = (data) => api.post('/rbac/usuarios/', data);

// Aviso para que el menú del dashboard recargue las etiquetas sin recargar la página.
export const LABELS_CHANGED_EVENT = 'rbac:etiquetas';
