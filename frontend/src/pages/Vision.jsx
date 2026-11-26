import React, { useEffect, useMemo, useState } from 'react';
import Icon from '../components/Icon';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';
import { getBovinos, updateBovino } from '../services/cattleService';
import { createCaptura, getCapturas } from '../services/visionService';
import { filasDe, mensajeDeError } from '../services/apiError';

const fechaLegible = (valor) =>
  new Date(valor).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

const esVideo = (archivo) => Boolean(archivo?.type?.startsWith('video/'));

export default function Vision() {
  const { etiqueta } = useEtiquetas();
  const { fincaActiva } = useAuth();
  const fincaId = fincaActiva?.id;

  const [bovinos, setBovinos] = useState([]);
  const [capturas, setCapturas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(null);

  const [bovino, setBovino] = useState('');
  const [archivo, setArchivo] = useState(null);
  const [vistaPrevia, setVistaPrevia] = useState(null);
  const [analizando, setAnalizando] = useState(false);
  const [error, setError] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [guardandoFoto, setGuardandoFoto] = useState(false);
  const [fotoGuardada, setFotoGuardada] = useState(false);

  const cargar = () => {
    if (!fincaId) { setCargando(false); return; }
    setCargando(true);
    setErrorCarga(null);
    Promise.all([getBovinos(fincaId), getCapturas({ finca: fincaId })])
      .then(([respuestaBovinos, respuestaCapturas]) => {
        const lista = filasDe(respuestaBovinos);
        setBovinos(lista);
        setBovino((previo) => previo || lista[0]?.id || '');
        setCapturas(filasDe(respuestaCapturas));
      })
      .catch((err) => setErrorCarga(mensajeDeError(err, 'No se pudieron cargar las capturas.')))
      .finally(() => setCargando(false));
  };

  useEffect(cargar, [fincaId]);

  // La URL temporal del archivo local se libera al cambiarlo o al salir.
  useEffect(() => {
    if (!archivo || esVideo(archivo)) { setVistaPrevia(null); return undefined; }
    const url = URL.createObjectURL(archivo);
    setVistaPrevia(url);
    return () => URL.revokeObjectURL(url);
  }, [archivo]);

  const aretePorId = useMemo(
    () => Object.fromEntries(bovinos.map((fila) => [fila.id, fila.arete])),
    [bovinos],
  );

  const usarComoFotoPerfil = async () => {
    if (!resultado?.archivo || !resultado?.bovino) return;
    setGuardandoFoto(true);
    try {
      await updateBovino(resultado.bovino, { url_foto_perfil: resultado.archivo });
      setFotoGuardada(true);
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo asignar la foto de perfil.'));
    } finally {
      setGuardandoFoto(false);
    }
  };

  const analizar = async (evento) => {
    evento.preventDefault();
    if (!archivo) { setError('Elige una foto o un video de la captura.'); return; }
    setError(null);
    setFotoGuardada(false);
    setAnalizando(true);
    try {
      const respuesta = await createCaptura({
        bovino,
        tipoArchivo: esVideo(archivo) ? 'video' : 'foto',
        archivo,
      });
      setResultado(respuesta.data);
      setArchivo(null);
      cargar();
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo procesar la captura.'));
    } finally {
      setAnalizando(false);
    }
  };

  if (!fincaId) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <Icon name="farm" />
          <h2>No hay una finca activa</h2>
          <p>Elige una finca en el selector de arriba para analizar sus bovinos.</p>
        </div>
      </div>
    );
  }

  const medicion = resultado?.medicion_detalle;

  return (
    <div className="page-content">
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('VCOM', 'Visión computacional')}</h1>
          <p>Sube una foto o un video del bovino y el sistema registra una medición con su peso estimado y condición corporal.</p>
        </div>
      </header>

      {/* Aviso permanente: la estimación no proviene de un modelo entrenado y
          quien lee el dato tiene que saberlo. */}
      <div className="notice notice-warn">
        <Icon name="alert" />
        <p>
          <strong>Estimación simulada, no es un modelo de IA real.</strong>
          Los valores se calculan con una heurística a partir de la edad y el sexo del bovino, con una variación aleatoria. Sirven para probar el flujo completo, no como dato productivo. Cuando se integre un modelo entrenado, las mediciones nuevas dejarán de marcarse como simuladas.
        </p>
      </div>

      {errorCarga && <div className="notice notice-danger"><Icon name="alert" /><p>{errorCarga}</p></div>}

      {cargando ? (
        <div className="page-loader"><span /></div>
      ) : bovinos.length === 0 ? (
        <div className="empty-state">
          <Icon name="cattle" />
          <h2>Primero registra bovinos</h2>
          <p>La captura se analiza contra un bovino de la finca; aún no hay ninguno.</p>
        </div>
      ) : (
        <>
          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Nueva captura</h2>
                <p>El archivo queda guardado junto con la medición que genera, para poder auditarla después.</p>
              </div>
            </div>
            <form className="modal-form" onSubmit={analizar}>
              {error && <div className="form-message is-error">{error}</div>}
              <label>
                Bovino
                <select required value={bovino} onChange={(evento) => setBovino(evento.target.value)}>
                  {bovinos.map((fila) => (
                    <option key={fila.id} value={fila.id}>{fila.arete}</option>
                  ))}
                </select>
              </label>
              {/* El control nativo se oculta y la etiqueta hace de botón, para
                  que la zona entera sea pulsable y combine con el resto. */}
              <label className={`dropzone ${archivo ? 'is-loaded' : ''}`}>
                {vistaPrevia ? (
                  <img src={vistaPrevia} alt={`Vista previa de la captura de ${aretePorId[bovino] || 'el bovino'}`} />
                ) : (
                  <Icon name="camera" />
                )}
                <p>{archivo ? archivo.name : 'Elige una foto o un video del bovino'}</p>
                <span className="dropzone-action">
                  {archivo ? 'Cambiar archivo' : 'Seleccionar archivo'}
                </span>
                <input
                  type="file" accept="image/*,video/*"
                  onChange={(evento) => { setArchivo(evento.target.files?.[0] || null); setError(null); }}
                />
              </label>
              <div className="modal-form-actions">
                <button type="submit" className="button button-primary" disabled={analizando || !archivo}>
                  {analizando ? 'Analizando…' : 'Analizar captura'}
                </button>
              </div>
            </form>

            {medicion && (
              <>
                <div className="vision-result">
                  <div>
                    <span>Peso estimado</span>
                    <strong>{medicion.peso_estimado_kg} kg</strong>
                    <small>Intervalo {medicion.intervalo_confianza_min_kg} – {medicion.intervalo_confianza_max_kg} kg</small>
                  </div>
                  <div>
                    <span>Condición corporal</span>
                    <strong>{medicion.condicion_corporal}</strong>
                    <small>Escala de 1 a 5</small>
                  </div>
                  <div>
                    <span>Confianza</span>
                    <strong>{medicion.nivel_confianza}%</strong>
                    <small>Valor simulado</small>
                  </div>
                </div>
                <p className="hint">
                  Guardada como medición de {aretePorId[resultado.bovino] || 'el bovino'}; aparece en el módulo de mediciones marcada como simulada.
                </p>
                {resultado.tipo_archivo === 'foto' && (
                  <button
                    type="button"
                    className="button button-secondary"
                    disabled={guardandoFoto || fotoGuardada}
                    onClick={usarComoFotoPerfil}
                  >
                    {fotoGuardada ? '✓ Foto de perfil asignada' : guardandoFoto ? 'Guardando…' : 'Usar como foto de perfil'}
                  </button>
                )}
              </>
            )}
          </section>

          <section className="panel">
            <div className="panel-head">
              <div>
                <h2>Capturas anteriores</h2>
                <p>{capturas.length} {capturas.length === 1 ? 'captura' : 'capturas'} en esta finca.</p>
              </div>
            </div>
            {capturas.length === 0 ? (
              <div className="empty-state">
                <Icon name="dash" />
                <h2>Sin capturas todavía</h2>
                <p>Sube la primera foto para generar una medición.</p>
              </div>
            ) : (
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Bovino</th>
                      <th>Fecha</th>
                      <th>Tipo</th>
                      <th className="is-numeric">Peso estimado</th>
                      <th className="is-numeric">Cond. corporal</th>
                      <th>Origen</th>
                      <th>Archivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {capturas.map((captura) => (
                      <tr key={captura.id}>
                        <td><strong>{aretePorId[captura.bovino] || '—'}</strong></td>
                        <td>{fechaLegible(captura.creado_en)}</td>
                        <td>{captura.tipo_archivo === 'video' ? 'Video' : 'Foto'}</td>
                        <td className="is-numeric">
                          {captura.medicion_detalle ? `${captura.medicion_detalle.peso_estimado_kg} kg` : '—'}
                        </td>
                        <td className="is-numeric">
                          {captura.medicion_detalle?.condicion_corporal ?? '—'}
                        </td>
                        <td><span className="badge badge-warn">Simulada</span></td>
                        <td>
                          {captura.archivo ? (
                            <a className="link-button" href={captura.archivo} target="_blank" rel="noreferrer">
                              Ver archivo
                            </a>
                          ) : '—'}
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
    </div>
  );
}
