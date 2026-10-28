import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../components/Icon';
import { getFincas } from '../services/farmService';

const roleCopy = {
  propietario: { title: 'Tus fincas', intro: 'Tienes control completo sobre los espacios que creaste.', action: 'Crear finca' },
  administrador: { title: 'Fincas administradas', intro: 'Coordina el equipo y las invitaciones de las fincas que administras.', action: 'Ver equipo' },
  operario: { title: 'Fincas asignadas', intro: 'Consulta las fincas a las que tienes acceso y el trabajo disponible.', action: 'Ver fincas' },
};

const roleLabel = { propietario: 'Propietario', administrador: 'Administrador', operario: 'Operario' };

export default function Dashboard({ audience = 'operario' }) {
  const [fincas, setFincas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const copy = roleCopy[audience];

  useEffect(() => {
    getFincas().then((response) => setFincas(response.data.results || response.data || [])).catch(() => setError(true)).finally(() => setLoading(false));
  }, []);

  const summary = useMemo(() => ({
    propias: fincas.filter((finca) => finca.mi_rol === 'propietario').length,
    administradas: fincas.filter((finca) => finca.mi_rol === 'administrador').length,
    asignadas: fincas.filter((finca) => finca.mi_rol === 'operario').length,
  }), [fincas]);

  if (loading) return <div className="page-loader"><span /></div>;

  return <div className="page-content" data-ui>
    <header className="page-title-row">
      <div><h1>{copy.title}</h1><p>{copy.intro}</p></div>
      <Link className="button button-primary" to={audience === 'propietario' ? '/fincas' : audience === 'administrador' ? '/miembros' : '/fincas'}>{copy.action}<Icon name="arrow" /></Link>
    </header>
    {error && <p className="form-message is-error">No se pudieron cargar las fincas. Actualiza la página para intentarlo otra vez.</p>}
    <section className="metric-strip" aria-label="Resumen de acceso">
      <div><span>Fincas propias</span><strong>{summary.propias}</strong><small>puedes configurar y administrar</small></div>
      <div><span>Fincas administradas</span><strong>{summary.administradas}</strong><small>puedes gestionar el equipo</small></div>
      <div><span>Fincas asignadas</span><strong>{summary.asignadas}</strong><small>acceso operativo</small></div>
    </section>
    <div className="dashboard-grid">
      <section>
        <div className="section-heading"><h2>Acceso reciente</h2><Link to="/fincas">Ver todas</Link></div>
        {fincas.length ? <div className="farm-list">{fincas.slice(0, 5).map((finca) => <Link to="/fincas" key={finca.id} className="farm-row"><div className="farm-mark"><Icon name="farm" /></div><div><strong>{finca.nombre}</strong><span>{finca.ubicacion || 'Ubicación sin registrar'}</span></div><em className={`role-mark role-${finca.mi_rol}`}>{roleLabel[finca.mi_rol] || 'Acceso'}</em><Icon name="arrow" className="row-arrow" /></Link>)}</div> : <div className="empty-state"><Icon name="farm" /><h2>Aún no tienes fincas</h2><p>Comienza creando una finca para organizar a tu equipo.</p><Link className="button button-primary" to="/fincas">Crear mi primera finca</Link></div>}
      </section>
      <aside className="dashboard-rail">
        <h2>Lo que puedes hacer</h2>
        <div className="task-list">
          <Link to="/fincas"><Icon name="farm" /><span><strong>{audience === 'propietario' ? 'Configura tus fincas' : 'Consulta las fincas'}</strong><small>Nombre, ubicación y acceso.</small></span><Icon name="arrow" /></Link>
          {audience !== 'operario' && <Link to="/miembros"><Icon name="people" /><span><strong>Organiza el equipo</strong><small>Asigna roles dentro de cada finca.</small></span><Icon name="arrow" /></Link>}
          {audience !== 'operario' && <Link to="/invitaciones"><Icon name="mail" /><span><strong>Envía invitaciones</strong><small>Incorpora a nuevos colaboradores.</small></span><Icon name="arrow" /></Link>}
        </div>
      </aside>
    </div>
  </div>;
}
