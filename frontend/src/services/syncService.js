import api from './api';

export const getCambios = (params) => api.get('/sync-changes/', { params });
export const getConflictos = (fincaId) =>
  api.get('/sync-changes/conflicts/', { params: { finca: fincaId } });
export const resolverConflicto = (cambioId) => api.post(`/sync-changes/${cambioId}/resolve/`);
export const confirmarCambio = (cambioId) => api.post(`/sync-changes/${cambioId}/acknowledge/`);
