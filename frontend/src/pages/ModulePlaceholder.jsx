import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function ModulePlaceholder({ endpoint, title, description, extension }) {
  const [state, setState] = useState('loading');

  useEffect(() => {
    api.get(endpoint).then(() => setState('ready')).catch(() => setState('error'));
  }, [endpoint]);

  return <div className="page-content module-placeholder" data-ui>
    <header className="page-title-row"><div><h1>{title}</h1><p>{description}</p></div></header>
    <section className="module-placeholder-panel" aria-live="polite">
      <h2>Módulo preparado para integración</h2>
      <p>{state === 'loading' ? 'Verificando acceso y contrato del módulo…' : state === 'ready' ? 'Tu rol tiene acceso. La lógica de negocio se incorporará en este punto.' : 'No se pudo verificar el contrato del módulo.'}</p>
      <dl><div><dt>Permiso</dt><dd>Verificado por el servidor</dd></div><div><dt>Punto de extensión</dt><dd>{extension}</dd></div></dl>
    </section>
  </div>;
}
