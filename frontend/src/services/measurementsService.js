import api from './api';

// Mediciones y pesajes son registros inmutables: solo se listan y se crean.
// Corregir uno no lo edita, crea otro que apunta al original con `corrige`.
export const getMediciones = (params) => api.get('/measurements/', { params });
export const createMedicion = (data) => api.post('/measurements/', data);

export const getMedidasMorfometricas = (medicionId) =>
  api.get('/morphometric-measurements/', { params: { medicion: medicionId } });
export const createMedidaMorfometrica = (data) => api.post('/morphometric-measurements/', data);

export const getPesajes = (params) => api.get('/scale-weighings/', { params });
export const createPesaje = (data) => api.post('/scale-weighings/', data);

// Catálogos que necesitan los formularios.
export const getDispositivos = () => api.get('/devices/');
export const createDispositivo = (data) => api.post('/devices/', data);
export const getModelosIa = () => api.get('/ai-models/');
export const getTiposMedida = () => api.get('/measurement-types/');
