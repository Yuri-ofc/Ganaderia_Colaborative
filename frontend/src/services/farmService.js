import api from './api';

export const getFincas = () => api.get('/farms/');

export const createFinca = (data) => api.post('/farms/', data);

export const updateFinca = (id, data) => api.patch(`/farms/${id}/`, data);

export const deleteFinca = (id) => api.delete(`/farms/${id}/`);

// Membresías
export const getMembresias = (fincaId) =>
  api.get('/memberships/', { params: fincaId ? { finca: fincaId } : {} });

export const createMembresia = (data) => api.post('/memberships/', data);

export const updateMembresia = (id, data) => api.patch(`/memberships/${id}/`, data);

export const deleteMembresia = (id) => api.delete(`/memberships/${id}/`);

// Invitaciones
export const getInvitaciones = (fincaId) =>
  api.get('/invitations/', { params: fincaId ? { finca: fincaId } : {} });

export const createInvitacion = (data) => api.post('/invitations/', data);

export const cancelInvitacion = (id) =>
  api.patch(`/invitations/${id}/`, { estado: 'cancelada' });

export const acceptInvitacion = (token) =>
  api.post('/invitations/accept/', { token });
