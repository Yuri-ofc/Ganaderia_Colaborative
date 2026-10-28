import api from './api';

// Razas: catálogo global, solo lectura para usuarios normales (solo personal
// de Django puede crear razas nuevas).
export const getRazas = () => api.get('/breeds/');

// Potreros: por finca. Crearlos requiere ser propietario o administrador.
export const getPotreros = (fincaId) => api.get('/lots/', { params: { finca: fincaId } });
export const createPotrero = (data) => api.post('/lots/', data);

// Bovinos
export const getBovinos = (fincaId) => api.get('/cattle/', { params: { finca: fincaId } });
export const createBovino = (data) => api.post('/cattle/', data);
export const updateBovino = (id, data) => api.patch(`/cattle/${id}/`, data);
export const aprobarPerfilBovino = (id) => api.post(`/cattle/${id}/approve-profile/`);
export const desactivarBovino = (id, estado, motivo) =>
  api.post(`/cattle/${id}/deactivate/`, { estado, motivo });
