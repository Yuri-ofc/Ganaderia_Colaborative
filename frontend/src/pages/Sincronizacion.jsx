import React, { useEffect, useMemo, useState } from 'react';
import Icon from '../components/Icon';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';
import { getCambios, getConflictos, resolverConflicto } from '../services/syncService';
import { filasDe, mensajeDeError } from '../services/apiError';

const ESTADOS = {
  pendiente: { texto: 'Pendiente', clase: 'badge-warn' },
  sincronizado: { texto: 'Sincronizado', clase: 'badge-ok' },
  conflicto: { texto: 'En conflicto', clase: 'badge-danger' },
  descartado: { texto: 'Descartado', clase: 'badge-muted' },
};

const ACCIONES = { crear: 'Creación', actualizar: 'Actualización', eliminar: 'Eliminación' };

const fechaLegible = (valor) =>
  new Date(valor).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

export default function Sincronizacion() {
  const { etiqueta } = useEtiquetas();
  const { fincaActiva, rolActivo, user } = useAuth();
  const fincaId = fincaActiva?.id;
  // Elegir qué cambio sobrevive lo decide el backend solo para propietario y
  // administrador; aquí únicamente se evita ofrecer un botón que daría 403.
  const puedeResolver = ['propietario', 'administrador', 'superadmin'].includes(rolActivo)
    || user?.is_superuser;

  const [cambios, setCambios] = useState([]);
  const [conflictos, setConflictos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(null);
  const [mensaje, setMensaje] = useState(null);
  const [resolviendo, setResolviendo] = useState(null);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [filtroRecurso, setFiltroRecurso] = useState('');

  const cargar = () => {
    if (!fincaId) { setCargando(false); return; }
    setCargando(true);
    setErrorCarga(null);
    const parametros = {
      finca: fincaId,
      ...(filtroEstado ? { estado: filtroEstado } : {}),
      ...(filtroRecurso ? { recurso: filtroRecurso } : {}),
    };
    // Los conflictos se consultan primero porque ese endpoint recalcula los
    // estados antes de que se pinte la tabla.
    getConflictos(fincaId)
      .then((respuesta) => {
        setConflictos(respuesta.data || []);
        return getCambios(parametros);
      })
      .then((respuesta) => setCambios(filasDe(respuesta)))
      .catch((err) => setErrorCarga(mensajeDeError(err, 'No se pudo cargar la cola de sincronización.')))
      .finally(() => setCargando(false));
  };

  useEffect(cargar, [fincaId, filtroEstado, filtroRecurso]);

  const recursos = useMemo(
    () => [...new Set(cambios.map((cambio) => cambio.recurso))].sort(),
    [cambios],
  );

  const resumen = useMemo(() => {
    const conteo = { pendiente: 0, sincronizado: 0, conflicto: 0, descartado: 0 };
    cambios.forEach((cambio) => { conteo[cambio.estado] = (conteo[cambio.estado] || 0) + 1; });
    return conteo;
  }, [cambios]);

  const resolver = async (cambioId) => {
    setResolviendo(cambioId);
    setMensaje(null);
    try {
      await resolverConflicto(cambioId);
      setMensaje('Conflicto resuelto: el cambio elegido queda en la cola y el resto se descartó.');
      cargar();
    } catch (err) {
      setErrorCarga(mensajeDeError(err, 'No se pudo resolver el conflicto.'));
    } finally {
      setResolviendo(null);
    }
  };

  if (!fincaId) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <Icon name="farm" />
          <h2>No hay una finca activa</h2>
          <p>Elige una finca en el selector de arriba para revisar su cola de sincronización.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('SYNC', 'Sincronización')}</h1>
          <p>Cambios que los dispositivos registraron sin conexión. Cuando dos editan el mismo objeto hay que decidir cuál vale.</p>
        </div>
        <button type="button" className="button button-ghost" onClick={cargar}>
          <Icon name="arrow" /> Actualizar
        </button>
      </header>

      {errorCarga && <div className="notice notice-danger"><Icon name="alert" /><p>{errorCarga}</p></div>}
      {mensaje && <div className="notice notice-info"><Icon name="check" /><p>{mensaje}</p></div>}

      <div className="metric-strip">
        <div>
          <span>Pendientes</span>
          <strong>{resumen.pendiente}</strong>
          <small>Esperan confirmación del dispositivo</small>
        </div>
        <div>
          <span>En conflicto</span>
          <strong>{resumen.conflicto}</strong>
          <small>Requieren una decisión</small>
        </div>
        <div>
          <span>Sincronizados</span>
          <strong>{resumen.sincronizado}</strong>
          <small>Ya confirmados</small>
        </div>
      </div>

      {conflictos.length > 0 && (
        <section className="panel">
          <div className="panel-head">
            <div>
              <h2>Conflictos por resolver</h2>
              <p>
                Dos o más cambios sin sincronizar afectan al mismo objeto. Se comparan los metadatos, no el contenido: elige cuál queda como válido y los demás se descartan dejando registro.
              </p>
            </div>
          </div>
          {conflictos.map((grupo) => (
            <article className="conflict-card" key={`${grupo.recurso}-${grupo.id_objeto}`}>
              <header>
                <strong>{grupo.recurso}</strong>
                <span className="badge badge-danger">{grupo.cambios.length} versiones</span>
                <code>{grupo.id_objeto}</code>
              </header>
              <div className="conflict-options">
                {grupo.cambios.map((cambio) => (
                  <div className="conflict-option" key={cambio.id}>
                    <dl>
                      <div><dt>Registrado</dt><dd>{fechaLegible(cambio.creado_en)}</dd></div>
                      <div><dt>Acción</dt><dd>{ACCIONES[cambio.accion] || cambio.accion}</dd></div>
                      <div><dt>Dispositivo</dt><dd>{cambio.dispositivo_nombre || '—'}</dd></div>
                      <div><dt>Registró</dt><dd>{cambio.creado_por_nombre || '—'}</dd></div>
                    </dl>
                    <pre>{JSON.stringify(cambio.contenido, null, 1)}</pre>
                    {cambio.id === grupo.sugerido && (
                      <span className="badge badge-ok">Más reciente</span>
                    )}
                    {puedeResolver ? (
                      <button
                        type="button" className="button button-primary"
                        onClick={() => resolver(cambio.id)} disabled={resolviendo === cambio.id}
                      >
                        {resolviendo === cambio.id ? 'Aplicando…' : 'Conservar este'}
                      </button>
                    ) : (
                      <p className="hint">Solo el propietario o un administrador puede resolverlo.</p>
                    )}
                  </div>
                ))}
              </div>
            </article>
          ))}
        </section>
      )}

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Cola de cambios</h2>
            <p>{cambios.length} {cambios.length === 1 ? 'cambio' : 'cambios'} con los filtros actuales.</p>
          </div>
        </div>
        <div className="filter-bar">
          <label>
            Estado
            <select value={filtroEstado} onChange={(evento) => setFiltroEstado(evento.target.value)}>
              <option value="">Todos</option>
              {Object.entries(ESTADOS).map(([valor, datos]) => (
                <option key={valor} value={valor}>{datos.texto}</option>
              ))}
            </select>
          </label>
          <label>
            Recurso
            <select value={filtroRecurso} onChange={(evento) => setFiltroRecurso(evento.target.value)}>
              <option value="">Todos</option>
              {recursos.map((recurso) => (
                <option key={recurso} value={recurso}>{recurso}</option>
              ))}
            </select>
          </label>
        </div>

        {cargando ? (
          <div className="page-loader"><span /></div>
        ) : cambios.length === 0 ? (
          <div className="empty-state">
            <Icon name="check" />
            <h2>La cola está vacía</h2>
            <p>No hay cambios offline esperando con estos filtros; es el estado normal cuando todo está sincronizado.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Recurso</th>
                  <th>Acción</th>
                  <th>Registrado</th>
                  <th>Sincronizado</th>
                  <th>Estado</th>
                  <th>Resolución</th>
                </tr>
              </thead>
              <tbody>
                {cambios.map((cambio) => {
                  const estado = ESTADOS[cambio.estado] || { texto: cambio.estado, clase: 'badge-muted' };
                  return (
                    <tr key={cambio.id}>
                      <td>
                        <strong>{cambio.recurso}</strong>
                        <small>{cambio.id_objeto}</small>
                      </td>
                      <td>{ACCIONES[cambio.accion] || cambio.accion}</td>
                      <td>{fechaLegible(cambio.creado_en)}</td>
                      <td>{cambio.sincronizado_en ? fechaLegible(cambio.sincronizado_en) : '—'}</td>
                      <td><span className={`badge ${estado.clase}`}>{estado.texto}</span></td>
                      <td>
                        {cambio.resuelto_en ? (
                          <>
                            <strong>{cambio.resuelto_por_nombre || '—'}</strong>
                            <small>{fechaLegible(cambio.resuelto_en)}</small>
                          </>
                        ) : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
