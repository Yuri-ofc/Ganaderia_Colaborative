import api from './api';

export const getRoles = () => api.get('/rbac/roles/');
export const createRole = (data) => api.post('/rbac/roles/', data);
export const updateRole = (id, data) => api.patch(`/rbac/roles/${id}/`, data);
export const deleteRole = (id) => api.delete(`/rbac/roles/${id}/`);

export const getResources = () => api.get('/rbac/resources/');
export const createResource = (data) => api.post('/rbac/resources/', data);
export const deleteResource = (id) => api.delete(`/rbac/resources/${id}/`);

export const getRbacUsers = (q = '') => api.get('/rbac/usuarios/', { params: q ? { q } : {} });
export const updateUserRoles = (id, roles_ids) => api.put(`/rbac/usuarios/${id}/roles/`, { roles_ids });
