import React, { useEffect, useMemo, useState } from 'react';
import Icon from '../components/Icon';
import Modal from '../components/Modal';
import TrendChart from '../components/TrendChart';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';
import { getBovinos } from '../services/cattleService';
import { createPesaje, getPesajes } from '../services/measurementsService';
import { filasDe, mensajeDeError } from '../services/apiError';

const fechaHoraLocal = (valor = new Date()) => {
  const desfase = valor.getTimezoneOffset() * 60000;
  return new Date(valor.getTime() - desfase).toISOString().slice(0, 16);
};

const fechaLegible = (valor) =>
  new Date(valor).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

const TIPOS_BASCULA = [
  'Báscula de corral',
  'Báscula electrónica portátil',
  'Báscula mecánica',
  'Báscula de plataforma',
  'Cinta bovinométrica',
];

const formularioVacio = { bovino: '', pesado_en: '', tipo_bascula: '', peso_real_kg: '' };

export default function Pesajes() {
  const { etiqueta } = useEtiquetas();
  const { fincaActiva } = useAuth();
  const fincaId = fincaActiva?.id;

  const [bovinos, setBovinos] = useState([]);
  const [pesajes, setPesajes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [filtroBovino, setFiltroBovino] = useState('');
  const [modalAbierto, setModalAbierto] = useState(false);
  const [corrigiendo, setCorrigiendo] = useState(null);
  const [formulario, setFormulario] = useState(formularioVacio);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [errorCarga, setErrorCarga] = useState(null);

  const cargar = () => {
    if (!fincaId) { setCargando(false); return; }
    setCargando(true);
    setErrorCarga(null);
    Promise.all([
      getBovinos(fincaId),
      getPesajes({ finca: fincaId, ...(filtroBovino ? { bovino: filtroBovino } : {}) }),
    ])
      .then(([respuestaBovinos, respuestaPesajes]) => {
        setBovinos(filasDe(respuestaBovinos));
        setPesajes(filasDe(respuestaPesajes));
      })
      .catch((err) => setErrorCarga(mensajeDeError(err, 'No se pudieron cargar los pesajes.')))
      .finally(() => setCargando(false));
  };

  useEffect(cargar, [fincaId, filtroBovino]);

  const aretePorId = useMemo(
    () => Object.fromEntries(bovinos.map((bovino) => [bovino.id, bovino.arete])),
    [bovinos],
  );

  // Un pesaje corregido no se borra: queda enlazado desde su corrección.
  const corregidos = useMemo(
    () => new Set(pesajes.map((pesaje) => pesaje.corrige).filter(Boolean)),
    [pesajes],
  );

  const serie = useMemo(() => {
    if (!filtroBovino) return [];
    return pesajes
      .filter((pesaje) => !corregidos.has(pesaje.id))
      .map((pesaje) => ({
        id: pesaje.id, fecha: pesaje.pesado_en, valor: Number(pesaje.peso_real_kg),
      }));
  }, [pesajes, filtroBovino, corregidos]);

  const abrirCreacion = () => {
    setCorrigiendo(null);
    setFormulario({
      ...formularioVacio,
      bovino: filtroBovino || bovinos[0]?.id || '',
      pesado_en: fechaHoraLocal(),
    });
    setError(null);
    setModalAbierto(true);
  };

  const abrirCorreccion = (pesaje) => {
    setCorrigiendo(pesaje);
    setFormulario({
      bovino: pesaje.bovino,
      pesado_en: fechaHoraLocal(new Date(pesaje.pesado_en)),
      tipo_bascula: pesaje.tipo_bascula,
      peso_real_kg: String(pesaje.peso_real_kg),
    });
    setError(null);
    setModalAbierto(true);
  };

  const guardar = async (evento) => {
    evento.preventDefault();
    setError(null);
    setGuardando(true);
    try {
      await createPesaje({
        bovino: formulario.bovino,
        pesado_en: new Date(formulario.pesado_en).toISOString(),
        tipo_bascula: formulario.tipo_bascula,
        peso_real_kg: formulario.peso_real_kg,
        ...(corrigiendo ? { corrige: corrigiendo.id } : {}),
      });
      setModalAbierto(false);
      cargar();
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo registrar el pesaje.'));
    } finally {
      setGuardando(false);
    }
  };

  if (!fincaId) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <Icon name="farm" />
          <h2>No hay una finca activa</h2>
          <p>Elige una finca en el selector de arriba para ver sus pesajes.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('PESA', 'Pesajes')}</h1>
          <p>Peso real tomado en báscula. Cada registro es histórico: para enmendar uno se añade una corrección y el original se conserva.</p>
        </div>
        <button type="button" className="button button-primary" onClick={abrirCreacion} disabled={bovinos.length === 0}>
          <Icon name="plus" /> Registrar pesaje
        </button>
      </header>

      {errorCarga && <div className="notice notice-danger"><Icon name="alert" /><p>{errorCarga}</p></div>}

      <div className="filter-bar">
        <label>
          Bovino
          <select value={filtroBovino} onChange={(evento) => setFiltroBovino(evento.target.value)}>
            <option value="">Todos los bovinos</option>
            {bovinos.map((bovino) => (
              <option key={bovino.id} value={bovino.id}>{bovino.arete}</option>
            ))}
          </select>
        </label>
        {filtroBovino && (
          <button type="button" className="button button-ghost link-button" onClick={() => setFiltroBovino('')}>
            Quitar filtro
          </button>
        )}
      </div>

      {cargando ? (
        <div className="page-loader"><span /></div>
      ) : bovinos.length === 0 ? (
        <div className="empty-state">
          <Icon name="cattle" />
          <h2>Primero registra bovinos</h2>
          <p>Los pesajes se toman sobre un bovino de la finca; aún no hay ninguno.</p>
        </div>
      ) : (
        <>
          {/* Con un solo registro la línea no dice nada; basta la tabla. */}
          {serie.length > 1 && (
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Evolución del peso</h2>
                  <p>Bovino {aretePorId[filtroBovino]}. Se omiten los registros que ya fueron corregidos.</p>
                </div>
              </div>
              <TrendChart puntos={serie} unidad="kg" titulo="Peso en báscula" />
            </section>
          )}

          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Historial</h2>
                <p>{pesajes.length} {pesajes.length === 1 ? 'registro' : 'registros'}{filtroBovino ? ` de ${aretePorId[filtroBovino]}` : ' en la finca'}.</p>
              </div>
            </div>
            {pesajes.length === 0 ? (
              <div className="empty-state">
                <Icon name="dash" />
                <h2>Sin pesajes todavía</h2>
                <p>Registra el primero para empezar a ver la evolución del peso.</p>
                <button type="button" className="button button-primary" onClick={abrirCreacion}>
                  <Icon name="plus" /> Registrar pesaje
                </button>
              </div>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Bovino</th>
                      <th>Fecha del pesaje</th>
                      <th>Báscula</th>
                      <th className="is-numeric">Peso</th>
                      <th>Estado</th>
                      <th aria-label="Acciones" />
                    </tr>
                  </thead>
                  <tbody>
                    {pesajes.map((pesaje) => (
                      <tr key={pesaje.id}>
                        <td><strong>{aretePorId[pesaje.bovino] || '—'}</strong></td>
                        <td>{fechaLegible(pesaje.pesado_en)}</td>
                        <td>{pesaje.tipo_bascula}</td>
                        <td className="is-numeric">{pesaje.peso_real_kg} kg</td>
                        <td>
                          {corregidos.has(pesaje.id) ? (
                            <span className="badge badge-muted">Corregido después</span>
                          ) : pesaje.corrige ? (
                            <span className="badge badge-warn">Es una corrección</span>
                          ) : (
                            <span className="badge badge-ok">Vigente</span>
                          )}
                        </td>
                        <td className="table-actions">
                          <button type="button" className="link-button" onClick={() => abrirCorreccion(pesaje)}>
                            Corregir
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      <Modal
        open={modalAbierto}
        onClose={() => setModalAbierto(false)}
        title={corrigiendo ? 'Corregir pesaje' : 'Registrar pesaje'}
      >
        <form className="modal-form" onSubmit={guardar}>
          {error && <div className="form-message is-error">{error}</div>}
          {corrigiendo && (
            <div className="notice notice-info">
              <Icon name="alert" />
              <p>
                <strong>Esto no modifica el registro anterior.</strong>
                Se guardará un pesaje nuevo enlazado al del {fechaLegible(corrigiendo.pesado_en)}, que queda en el historial marcado como corregido.
              </p>
            </div>
          )}
          <label>
            Bovino
            <select
              required
              value={formulario.bovino}
              disabled={Boolean(corrigiendo)}
              onChange={(evento) => setFormulario({ ...formulario, bovino: evento.target.value })}
            >
              <option value="" disabled>Selecciona…</option>
              {bovinos.map((bovino) => (
                <option key={bovino.id} value={bovino.id}>{bovino.arete}</option>
              ))}
            </select>
          </label>
          <div className="form-grid">
            <label>
              Fecha y hora
              <input
                type="datetime-local" required
                value={formulario.pesado_en}
                onChange={(evento) => setFormulario({ ...formulario, pesado_en: evento.target.value })}
              />
            </label>
            <label>
              Peso real <span>(kg)</span>
              <input
                type="number" required min="0.01" step="0.01" placeholder="ej: 412.5"
                value={formulario.peso_real_kg}
                onChange={(evento) => setFormulario({ ...formulario, peso_real_kg: evento.target.value })}
              />
            </label>
          </div>
          <label>
            Tipo de báscula
            <select
              required
              value={formulario.tipo_bascula}
              onChange={(evento) => setFormulario({ ...formulario, tipo_bascula: evento.target.value })}
            >
              <option value="" disabled>Selecciona…</option>
              {TIPOS_BASCULA.map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
            </select>
          </label>
          <div className="modal-form-actions">
            <button type="button" className="button button-ghost" onClick={() => setModalAbierto(false)}>
              Cancelar
            </button>
            <button type="submit" className="button button-primary" disabled={guardando}>
              {guardando ? 'Guardando…' : corrigiendo ? 'Guardar corrección' : 'Registrar'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
