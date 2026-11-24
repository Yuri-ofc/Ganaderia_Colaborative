import React from 'react';
import { Navigate, useParams } from 'react-router-dom';
import Icon from '../components/Icon';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';

// Pantalla de las opciones creadas desde Control de acceso. Solo se abre si el
// código es una opción del menú y el usuario tiene el recurso asignado.
export default function OpcionPersonalizada() {
  const { codigo } = useParams();
  const { user, loading } = useAuth();
  const { etiqueta, opciones } = useEtiquetas();

  if (loading) return <div className="app-loading" aria-label="Cargando sesión"><span /></div>;
  const permitido = user?.is_superuser || user?.roles?.includes('SUPR') || user?.recursos?.includes(codigo);
  if (!permitido) return <Navigate to="/propietario" replace />;
  // El menú se carga aparte: mientras no llegue, no se decide si existe.
  const existe = opciones.some((opcion) => opcion.nombre === codigo);
  const titulo = etiqueta(codigo, codigo);

  return (
    <div className="page-content module-placeholder" data-ui>
      <header className="page-title-row"><div><h1>{titulo}</h1><p>Opción agregada desde Control de acceso.</p></div></header>
      <section className="module-placeholder-panel" aria-live="polite">
        <Icon name="alert" />
        <h2>Funcionalidad en proceso de Implementación</h2>
        <p>{existe || opciones.length === 0 ? 'Esta opción ya está disponible en el menú; su contenido se incorporará en este punto.' : 'Esta opción ya no existe en el menú.'}</p>
      </section>
    </div>
  );
}
