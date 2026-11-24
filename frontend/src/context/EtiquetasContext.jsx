import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';
import { LABELS_CHANGED_EVENT, getResourceLabels } from '../services/rbacService';

// Etiquetas de las opciones del dashboard (editables desde Control de acceso).
// Una sola consulta alimenta el menú lateral y el título de cada página, así
// ambos siempre muestran el mismo nombre.
const EtiquetasContext = createContext({ etiqueta: (_codigo, porDefecto) => porDefecto, opciones: [] });

export function EtiquetasProvider({ children }) {
  const { user } = useAuth();
  const [datos, setDatos] = useState({ etiquetas: {}, opciones: [] });

  useEffect(() => {
    let activo = true;
    const cargar = () => getResourceLabels()
      .then((response) => {
        if (activo) setDatos({ etiquetas: response.data?.etiquetas || {}, opciones: response.data?.opciones || [] });
      })
      .catch(() => {}); // sin respuesta se usan los textos por defecto
    cargar();
    window.addEventListener(LABELS_CHANGED_EVENT, cargar);
    return () => { activo = false; window.removeEventListener(LABELS_CHANGED_EVENT, cargar); };
  }, [user?.id]);

  const valor = useMemo(() => ({
    etiqueta: (codigo, porDefecto) => datos.etiquetas[codigo] || porDefecto,
    opciones: datos.opciones,
  }), [datos]);

  return <EtiquetasContext.Provider value={valor}>{children}</EtiquetasContext.Provider>;
}

export const useEtiquetas = () => useContext(EtiquetasContext);
