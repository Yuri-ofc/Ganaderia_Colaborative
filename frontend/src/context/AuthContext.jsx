import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { getProfile, logout as logoutService } from '../services/authService';
import { getFincas } from '../services/farmService';

const AuthContext = createContext(null);

// Clave en localStorage para recordar la finca activa entre sesiones.
const CLAVE_FINCA_ACTIVA = 'fincaActivaId';

// Finca por defecto cuando no hay ninguna guardada: prefiere donde eres
// propietario, si no administrador, si no la primera disponible.
function elegirFincaDefault(fincas) {
  if (!fincas || fincas.length === 0) return null;
  return (
    fincas.find((f) => f.mi_rol === 'propietario')
    || fincas.find((f) => f.mi_rol === 'administrador')
    || fincas[0]
  );
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [user, setUser] = useState(null);
  const [fincas, setFincas] = useState([]);
  const [fincaActivaId, setFincaActivaId] = useState(() => localStorage.getItem(CLAVE_FINCA_ACTIVA));
  const [loading, setLoading] = useState(Boolean(token));

  const isAuthenticated = !!token;

  // El rol del usuario se interpreta siempre en el contexto de la finca activa.
  // Sin fincas, usamos 'propietario' como estado inicial para que la cuenta
  // nueva pueda crear su primera finca desde /propietario.
  const rolActivo = useMemo(() => {
    if (!fincas.length) return 'propietario';
    const activa = fincas.find((f) => f.id === fincaActivaId);
    return activa?.mi_rol || null;
  }, [fincas, fincaActivaId]);

  // La finca activa real (objeto, no sólo id) para que las pantallas puedan leerla directo.
  const fincaActiva = useMemo(
    () => fincas.find((f) => f.id === fincaActivaId) || null,
    [fincas, fincaActivaId],
  );

  const refreshFincas = async () => {
    try {
      const response = await getFincas();
      const lista = response.data.results || response.data || [];
      setFincas(lista);
      // Si la finca activa guardada ya no existe, elegimos un default.
      const vigente = lista.find((f) => f.id === fincaActivaId);
      if (!vigente) {
        const def = elegirFincaDefault(lista);
        if (def) {
          setFincaActivaId(def.id);
          localStorage.setItem(CLAVE_FINCA_ACTIVA, def.id);
        } else {
          setFincaActivaId(null);
          localStorage.removeItem(CLAVE_FINCA_ACTIVA);
        }
      }
      return lista;
    } catch {
      setFincas([]);
      return [];
    }
  };

  const setFincaActiva = (id) => {
    if (!id) {
      setFincaActivaId(null);
      localStorage.removeItem(CLAVE_FINCA_ACTIVA);
      return;
    }
    setFincaActivaId(id);
    localStorage.setItem(CLAVE_FINCA_ACTIVA, id);
  };

  const loadProfile = async () => {
    if (!localStorage.getItem('authToken')) return null;
    try {
      const response = await getProfile();
      setUser(response.data);
      await refreshFincas();
      return response.data;
    } catch {
      localStorage.removeItem('authToken');
      localStorage.removeItem(CLAVE_FINCA_ACTIVA);
      setToken(null);
      setUser(null);
      setFincas([]);
      setFincaActivaId(null);
      return null;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) loadProfile();
    else setLoading(false);
  }, []);

  const saveToken = async (newToken) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
    setLoading(true);
    return loadProfile();
  };

  const handleLogout = async () => {
    try {
      await logoutService();
    } catch (e) {
      // Si falla el logout en servidor, igual cerramos sesión local
    }
    localStorage.removeItem('authToken');
    localStorage.removeItem(CLAVE_FINCA_ACTIVA);
    setToken(null);
    setUser(null);
    setFincas([]);
    setFincaActivaId(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        fincas,
        fincaActiva,
        fincaActivaId,
        rolActivo,
        isAuthenticated,
        saveToken,
        handleLogout,
        loading,
        loadProfile,
        setFincaActiva,
        refreshFincas,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return context;
}
