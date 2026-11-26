import React, { useEffect, useMemo, useState } from 'react';
import Icon from '../components/Icon';
import Modal from '../components/Modal';
import TrendChart from '../components/TrendChart';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';
import { getBovinos } from '../services/cattleService';
import {
  createDispositivo,
  createMedicion,
  createMedidaMorfometrica,
  getDispositivos,
  getMediciones,
  getMedidasMorfometricas,
  getModelosIa,
  getTiposMedida,
} from '../services/measurementsService';
import { filasDe, mensajeDeError } from '../services/apiError';

const fechaHoraLocal = (valor = new Date()) => {
  const desfase = valor.getTimezoneOffset() * 60000;
  return new Date(valor.getTime() - desfase).toISOString().slice(0, 16);
};

const fechaLegible = (valor) =>
  new Date(valor).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

const formularioVacio = {
  bovino: '', dispositivo: '', modelo_ia: '', capturado_en: '', modo_captura: 'foto',
  peso_estimado_kg: '', intervalo_confianza_min_kg: '', intervalo_confianza_max_kg: '',
  condicion_corporal: '3.0', nivel_confianza: '80',
};

export default function Mediciones() {
  const { etiqueta } = useEtiquetas();
  const { fincaActiva } = useAuth();
  const fincaId = fincaActiva?.id;

  const [bovinos, setBovinos] = useState([]);
  const [mediciones, setMediciones] = useState([]);
  const [dispositivos, setDispositivos] = useState([]);
  const [modelos, setModelos] = useState([]);
  const [tipos, setTipos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(null);
  const [filtroBovino, setFiltroBovino] = useState('');

  const [modalAbierto, setModalAbierto] = useState(false);
  const [corrigiendo, setCorrigiendo] = useState(null);
  const [formulario, setFormulario] = useState(formularioVacio);
  const [morfometricas, setMorfometricas] = useState([]);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  const [nuevoDispositivo, setNuevoDispositivo] = useState('');
  const [creandoDispositivo, setCreandoDispositivo] = useState(false);

  const [detalle, setDetalle] = useState(null);
  const [detalleFilas, setDetalleFilas] = useState([]);

  const cargar = () => {
    if (!fincaId) { setCargando(false); return; }
    setCargando(true);
    setErrorCarga(null);
    Promise.all([
      getBovinos(fincaId),
      getMediciones({ finca: fincaId, ...(filtroBovino ? { bovino: filtroBovino } : {}) }),
    ])
      .then(([respuestaBovinos, respuestaMediciones]) => {
        setBovinos(filasDe(respuestaBovinos));
        setMediciones(filasDe(respuestaMediciones));
      })
      .catch((err) => setErrorCarga(mensajeDeError(err, 'No se pudieron cargar las mediciones.')))
      .finally(() => setCargando(false));
  };

  useEffect(cargar, [fincaId, filtroBovino]);

  useEffect(() => {
    Promise.all([getDispositivos(), getModelosIa(), getTiposMedida()])
      .then(([respuestaDispositivos, respuestaModelos, respuestaTipos]) => {
        setDispositivos(filasDe(respuestaDispositivos));
        setModelos(filasDe(respuestaModelos).filter((modelo) => modelo.activo));
        setTipos(filasDe(respuestaTipos));
      })
      .catch((err) => setErrorCarga(mensajeDeError(err, 'No se pudieron cargar los catálogos.')));
  }, []);

  const aretePorId = useMemo(
    () => Object.fromEntries(bovinos.map((bovino) => [bovino.id, bovino.arete])),
    [bovinos],
  );
  const versionPorId = useMemo(
    () => Object.fromEntries(modelos.map((modelo) => [modelo.id, modelo.version])),
    [modelos],
  );
  const corregidas = useMemo(
    () => new Set(mediciones.map((medicion) => medicion.corrige).filter(Boolean)),
    [mediciones],
  );

  const serie = useMemo(() => {
    if (!filtroBovino) return [];
    return mediciones
      .filter((medicion) => !corregidas.has(medicion.id))
      .map((medicion) => ({
        id: medicion.id, fecha: medicion.capturado_en, valor: Number(medicion.peso_estimado_kg),
      }));
  }, [mediciones, filtroBovino, corregidas]);

  // El servidor rechaza un peso fuera del intervalo; avisar antes de enviar
  // evita un viaje y un error genérico.
  const intervaloInvalido = (() => {
    const peso = Number(formulario.peso_estimado_kg);
    const minimo = Number(formulario.intervalo_confianza_min_kg);
    const maximo = Number(formulario.intervalo_confianza_max_kg);
    if (!formulario.peso_estimado_kg || !formulario.intervalo_confianza_min_kg || !formulario.intervalo_confianza_max_kg) {
      return null;
    }
    if (minimo > maximo) return 'El mínimo del intervalo no puede superar al máximo.';
    if (peso < minimo || peso > maximo) return 'El peso estimado debe quedar dentro del intervalo de confianza.';
    return null;
  })();

  const abrirCreacion = () => {
    setCorrigiendo(null);
    setMorfometricas([]);
    setFormulario({
      ...formularioVacio,
      bovino: filtroBovino || bovinos[0]?.id || '',
      dispositivo: dispositivos[0]?.id || '',
      modelo_ia: modelos[0]?.id || '',
      capturado_en: fechaHoraLocal(),
    });
    setError(null);
    setModalAbierto(true);
  };

  const abrirCorreccion = (medicion) => {
    setCorrigiendo(medicion);
    setMorfometricas([]);
    setFormulario({
      bovino: medicion.bovino,
      dispositivo: dispositivos.some((d) => d.id === medicion.dispositivo)
        ? medicion.dispositivo
        : dispositivos[0]?.id || '',
      modelo_ia: medicion.modelo_ia,
      capturado_en: fechaHoraLocal(new Date(medicion.capturado_en)),
      modo_captura: medicion.modo_captura,
      peso_estimado_kg: String(medicion.peso_estimado_kg),
      intervalo_confianza_min_kg: String(medicion.intervalo_confianza_min_kg),
      intervalo_confianza_max_kg: String(medicion.intervalo_confianza_max_kg),
      condicion_corporal: String(medicion.condicion_corporal),
      nivel_confianza: String(medicion.nivel_confianza),
    });
    setError(null);
    setModalAbierto(true);
  };

  const crearDispositivo = async () => {
    if (!nuevoDispositivo.trim()) return;
    setCreandoDispositivo(true);
    try {
      const respuesta = await createDispositivo({
        modelo: nuevoDispositivo.trim(), sistema_operativo: 'No especificado',
      });
      setDispositivos((previos) => [...previos, respuesta.data]);
      setFormulario((previo) => ({ ...previo, dispositivo: respuesta.data.id }));
      setNuevoDispositivo('');
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo registrar el dispositivo.'));
    } finally {
      setCreandoDispositivo(false);
    }
  };

  const guardar = async (evento) => {
    evento.preventDefault();
    if (intervaloInvalido) { setError(intervaloInvalido); return; }
    setError(null);
    setGuardando(true);
    try {
      const respuesta = await createMedicion({
        bovino: formulario.bovino,
        dispositivo: formulario.dispositivo,
        modelo_ia: formulario.modelo_ia,
        capturado_en: new Date(formulario.capturado_en).toISOString(),
        modo_captura: formulario.modo_captura,
        peso_estimado_kg: formulario.peso_estimado_kg,
        intervalo_confianza_min_kg: formulario.intervalo_confianza_min_kg,
        intervalo_confianza_max_kg: formulario.intervalo_confianza_max_kg,
        condicion_corporal: formulario.condicion_corporal,
        nivel_confianza: formulario.nivel_confianza,
        ...(corrigiendo ? { corrige: corrigiendo.id } : {}),
      });
      // Las medidas morfométricas cuelgan de la medición, así que se envían
      // después de tener su identificador.
      const utiles = morfometricas.filter((fila) => fila.tipo_medida && fila.valor !== '');
      for (const fila of utiles) {
        await createMedidaMorfometrica({
          medicion: respuesta.data.id, tipo_medida: fila.tipo_medida, valor: fila.valor,
        });
      }
      setModalAbierto(false);
      cargar();
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo registrar la medición.'));
    } finally {
      setGuardando(false);
    }
  };

  const verDetalle = async (medicion) => {
    setDetalle(medicion);
    setDetalleFilas([]);
    try {
      const respuesta = await getMedidasMorfometricas(medicion.id);
      setDetalleFilas(filasDe(respuesta));
    } catch {
      setDetalleFilas([]);
    }
  };

  if (!fincaId) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <Icon name="farm" />
          <h2>No hay una finca activa</h2>
          <p>Elige una finca en el selector de arriba para ver sus mediciones.</p>
        </div>
      </div>
    );
  }

  const faltanCatalogos = modelos.length === 0;

  return (
    <div className="page-content">
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('MEDI', 'Mediciones')}</h1>
          <p>Peso estimado, condición corporal y medidas morfométricas. Los registros son históricos: una enmienda se guarda como corrección enlazada.</p>
        </div>
        <button
          type="button" className="button button-primary" onClick={abrirCreacion}
          disabled={bovinos.length === 0 || faltanCatalogos}
        >
          <Icon name="plus" /> Registrar medición
        </button>
      </header>

      {errorCarga && <div className="notice notice-danger"><Icon name="alert" /><p>{errorCarga}</p></div>}
      {faltanCatalogos && (
        <div className="notice notice-warn">
          <Icon name="alert" />
          <p>
            <strong>Falta el catálogo de modelos.</strong>
            No hay ningún modelo de estimación activo, así que no se pueden registrar mediciones. Pide al administrador del sistema que ejecute las migraciones o registre uno.
          </p>
        </div>
      )}

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
          <button type="button" className="link-button" onClick={() => setFiltroBovino('')}>
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
          <p>Las mediciones se toman sobre un bovino de la finca; aún no hay ninguno.</p>
        </div>
      ) : (
        <>
          {/* Con un solo registro la línea no dice nada; basta la tabla. */}
          {serie.length > 1 && (
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Evolución del peso estimado</h2>
                  <p>Bovino {aretePorId[filtroBovino]}. Se omiten las mediciones ya corregidas.</p>
                </div>
              </div>
              <TrendChart puntos={serie} unidad="kg" titulo="Peso estimado" />
            </section>
          )}

          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Historial</h2>
                <p>{mediciones.length} {mediciones.length === 1 ? 'medición' : 'mediciones'}{filtroBovino ? ` de ${aretePorId[filtroBovino]}` : ' en la finca'}.</p>
              </div>
            </div>
            {mediciones.length === 0 ? (
              <div className="empty-state">
                <Icon name="dash" />
                <h2>Sin mediciones todavía</h2>
                <p>Registra la primera, o toma una captura desde el módulo de visión computacional.</p>
                <button type="button" className="button button-primary" onClick={abrirCreacion} disabled={faltanCatalogos}>
                  <Icon name="plus" /> Registrar medición
                </button>
              </div>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Bovino</th>
                      <th>Captura</th>
                      <th className="is-numeric">Peso estimado</th>
                      <th className="is-numeric">Cond. corporal</th>
                      <th className="is-numeric">Confianza</th>
                      <th>Origen</th>
                      <th aria-label="Acciones" />
                    </tr>
                  </thead>
                  <tbody>
                    {mediciones.map((medicion) => (
                      <tr key={medicion.id}>
                        <td><strong>{aretePorId[medicion.bovino] || '—'}</strong></td>
                        <td>
                          {fechaLegible(medicion.capturado_en)}
                          <small>{medicion.modo_captura === 'video' ? 'Video' : 'Foto'}</small>
                        </td>
                        <td className="is-numeric">
                          {medicion.peso_estimado_kg} kg
                          <small>{medicion.intervalo_confianza_min_kg} – {medicion.intervalo_confianza_max_kg}</small>
                        </td>
                        <td className="is-numeric">{medicion.condicion_corporal}</td>
                        <td className="is-numeric">{medicion.nivel_confianza}%</td>
                        <td>
                          {versionPorId[medicion.modelo_ia]?.startsWith('simulado') ? (
                            <span className="badge badge-warn">Simulada</span>
                          ) : (
                            <span className="badge badge-muted">{versionPorId[medicion.modelo_ia] || '—'}</span>
                          )}
                          {corregidas.has(medicion.id) && <small>Corregida después</small>}
                          {medicion.corrige && <small>Es una corrección</small>}
                        </td>
                        <td className="table-actions">
                          <button type="button" className="link-button" onClick={() => verDetalle(medicion)}>
                            Ver
                          </button>
                          <button type="button" className="link-button" onClick={() => abrirCorreccion(medicion)}>
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
        title={corrigiendo ? 'Corregir medición' : 'Registrar medición'}
      >
        <form className="modal-form" onSubmit={guardar}>
          {error && <div className="form-message is-error">{error}</div>}
          {corrigiendo && (
            <div className="notice notice-info">
              <Icon name="alert" />
              <p>
                <strong>Esto no modifica el registro anterior.</strong>
                Se guardará una medición nueva enlazada a la del {fechaLegible(corrigiendo.capturado_en)}, que queda marcada como corregida.
              </p>
            </div>
          )}
          <label>
            Bovino
            <select
              required value={formulario.bovino} disabled={Boolean(corrigiendo)}
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
              Fecha y hora de captura
              <input
                type="datetime-local" required value={formulario.capturado_en}
                onChange={(evento) => setFormulario({ ...formulario, capturado_en: evento.target.value })}
              />
            </label>
            <label>
              Modo de captura
              <select
                value={formulario.modo_captura}
                onChange={(evento) => setFormulario({ ...formulario, modo_captura: evento.target.value })}
              >
                <option value="foto">Foto</option>
                <option value="video">Video</option>
              </select>
            </label>
          </div>
          <label>
            Dispositivo
            {dispositivos.length > 0 ? (
              <select
                required value={formulario.dispositivo}
                onChange={(evento) => setFormulario({ ...formulario, dispositivo: evento.target.value })}
              >
                <option value="" disabled>Selecciona…</option>
                {dispositivos.map((dispositivo) => (
                  <option key={dispositivo.id} value={dispositivo.id}>{dispositivo.modelo}</option>
                ))}
              </select>
            ) : (
              <span>Todavía no tienes dispositivos registrados; crea uno aquí abajo.</span>
            )}
          </label>
          <div className="measure-row">
            <input
              type="text" placeholder="Nombre de un dispositivo nuevo (ej: Celular de campo)"
              value={nuevoDispositivo}
              onChange={(evento) => setNuevoDispositivo(evento.target.value)}
            />
            <button
              type="button" className="button button-ghost"
              onClick={crearDispositivo} disabled={creandoDispositivo || !nuevoDispositivo.trim()}
            >
              {creandoDispositivo ? '…' : 'Registrar'}
            </button>
            <span />
          </div>
          <label>
            Modelo de estimación
            <select
              required value={formulario.modelo_ia}
              onChange={(evento) => setFormulario({ ...formulario, modelo_ia: evento.target.value })}
            >
              <option value="" disabled>Selecciona…</option>
              {modelos.map((modelo) => (
                <option key={modelo.id} value={modelo.id}>{modelo.version}</option>
              ))}
            </select>
          </label>
          <div className="form-grid">
            <label>
              Peso estimado <span>(kg)</span>
              <input
                type="number" required min="0.01" step="0.01" placeholder="ej: 380.00"
                value={formulario.peso_estimado_kg}
                onChange={(evento) => setFormulario({ ...formulario, peso_estimado_kg: evento.target.value })}
              />
            </label>
            <label>
              Condición corporal <span>(1 a 5)</span>
              <input
                type="number" required min="0.1" max="5" step="0.1"
                value={formulario.condicion_corporal}
                onChange={(evento) => setFormulario({ ...formulario, condicion_corporal: evento.target.value })}
              />
            </label>
          </div>
          <div className="form-grid">
            <label>
              Intervalo mínimo <span>(kg)</span>
              <input
                type="number" required min="0" step="0.01"
                value={formulario.intervalo_confianza_min_kg}
                onChange={(evento) => setFormulario({ ...formulario, intervalo_confianza_min_kg: evento.target.value })}
              />
            </label>
            <label>
              Intervalo máximo <span>(kg)</span>
              <input
                type="number" required min="0" step="0.01"
                value={formulario.intervalo_confianza_max_kg}
                onChange={(evento) => setFormulario({ ...formulario, intervalo_confianza_max_kg: evento.target.value })}
              />
            </label>
          </div>
          {intervaloInvalido && <p className="auth-field-warning">{intervaloInvalido}</p>}
          <label>
            Nivel de confianza <span>(0 a 100)</span>
            <input
              type="number" required min="0" max="100" step="0.01"
              value={formulario.nivel_confianza}
              onChange={(evento) => setFormulario({ ...formulario, nivel_confianza: evento.target.value })}
            />
          </label>

          {tipos.length > 0 && !corrigiendo && (
            <div>
              <label htmlFor="morfometricas-ayuda">Medidas morfométricas <span>(opcional)</span></label>
              <p id="morfometricas-ayuda" className="hint">
                Cada tipo se puede registrar una sola vez por medición.
              </p>
              <div className="measure-rows">
                {morfometricas.map((fila, indice) => (
                  <div className="measure-row" key={indice}>
                    <select
                      value={fila.tipo_medida}
                      onChange={(evento) => setMorfometricas((previas) =>
                        previas.map((otra, i) => (i === indice ? { ...otra, tipo_medida: evento.target.value } : otra)))}
                    >
                      <option value="">Tipo de medida…</option>
                      {tipos
                        .filter((tipo) => tipo.id === fila.tipo_medida
                          || !morfometricas.some((otra) => otra.tipo_medida === tipo.id))
                        .map((tipo) => (
                          <option key={tipo.id} value={tipo.id}>{tipo.nombre} ({tipo.unidad})</option>
                        ))}
                    </select>
                    <input
                      type="number" min="0" step="0.01" placeholder="Valor"
                      value={fila.valor}
                      onChange={(evento) => setMorfometricas((previas) =>
                        previas.map((otra, i) => (i === indice ? { ...otra, valor: evento.target.value } : otra)))}
                    />
                    <button
                      type="button" className="icon-button" aria-label="Quitar medida"
                      onClick={() => setMorfometricas((previas) => previas.filter((_, i) => i !== indice))}
                    >
                      <Icon name="close" />
                    </button>
                  </div>
                ))}
              </div>
              {morfometricas.length < tipos.length && (
                <button
                  type="button" className="link-button is-spaced"
                  onClick={() => setMorfometricas((previas) => [...previas, { tipo_medida: '', valor: '' }])}
                >
                  + Añadir medida
                </button>
              )}
            </div>
          )}

          <div className="modal-form-actions">
            <button type="button" className="button button-ghost" onClick={() => setModalAbierto(false)}>
              Cancelar
            </button>
            <button type="submit" className="button button-primary" disabled={guardando || Boolean(intervaloInvalido)}>
              {guardando ? 'Guardando…' : corrigiendo ? 'Guardar corrección' : 'Registrar'}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(detalle)} onClose={() => setDetalle(null)} title="Detalle de la medición">
        {detalle && (
          <div className="modal-form">
            <dl className="detail-list">
              <div><dt>Bovino</dt><dd>{aretePorId[detalle.bovino] || '—'}</dd></div>
              <div><dt>Capturada</dt><dd>{fechaLegible(detalle.capturado_en)}</dd></div>
              <div><dt>Peso estimado</dt><dd>{detalle.peso_estimado_kg} kg</dd></div>
              <div>
                <dt>Intervalo</dt>
                <dd>{detalle.intervalo_confianza_min_kg} – {detalle.intervalo_confianza_max_kg} kg</dd>
              </div>
              <div><dt>Condición corporal</dt><dd>{detalle.condicion_corporal}</dd></div>
              <div><dt>Confianza</dt><dd>{detalle.nivel_confianza}%</dd></div>
              <div><dt>Modelo</dt><dd>{versionPorId[detalle.modelo_ia] || '—'}</dd></div>
            </dl>
            <div>
              <h2>Medidas morfométricas</h2>
              {detalleFilas.length === 0 ? (
                <p className="hint">Esta medición no tiene medidas morfométricas registradas.</p>
              ) : (
                <table className="data-table">
                  <tbody>
                    {detalleFilas.map((fila) => (
                      <tr key={fila.id}>
                        <td>{tipos.find((tipo) => tipo.id === fila.tipo_medida)?.nombre || '—'}</td>
                        <td className="is-numeric">
                          {fila.valor} {tipos.find((tipo) => tipo.id === fila.tipo_medida)?.unidad || ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
