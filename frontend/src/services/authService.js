import api from './api';

export const login = (email, password) =>
  api.post('/auth/token/', { email, password });

export const register = (data) =>
  api.post('/auth/register/', data);

export const logout = () =>
  api.post('/auth/logout/');

export const getProfile = () => api.get('/auth/me/');

export const buscarUsuario = (q) =>
  api.get('/auth/buscar-usuario/', { params: { q } });
