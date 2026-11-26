import React, { useEffect, useState } from 'react';
import Icon from '../components/Icon';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';
import {
  descargarRespaldo,
  generarRespaldo,
  getRespaldos,
  restaurarRespaldo,
} from '../services/backupsService';
import { filasDe, mensajeDeError } from '../services/apiError';

const fechaLegible = (valor) =>
  new Date(valor).toLocaleString('es-CO', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });

const tamanoLegible = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export default function Respaldos() {
  const { etiqueta } = useEtiquetas();
  const { fincaActiva, user } = useAuth();
  const fincaId = fincaActiva?.id;
  // Restaurar es un recurso aparte de ver o generar: el servidor exige RECU.
  const puedeRestaurar = user?.is_superuser || user?.recursos?.includes('RECU');

  const [respaldos, setRespaldos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [mensaje, setMensaje] = useState(null);
  const [generando, setGenerando] = useState(false);
  const [cifrar, setCifrar] = useState(false);
  const [ocupado, setOcupado] = useState(null);

  const [objetivo, setObjetivo] = useState(null);
  const [confirmado, setConfirmado] = useState(false);
  const [restaurando, setRestaurando] = useState(false);

  const cargar = () => {
    if (!fincaId) { setCargando(false); return; }
    setCargando(true);
    getRespaldos(fincaId)
      .then((respuesta) => { setRespaldos(filasDe(respuesta)); setError(null); })
      .catch((err) => setError(mensajeDeError(err, 'No se pudieron cargar los respaldos.')))
      .finally(() => setCargando(false));
  };

  useEffect(cargar, [fincaId]);

  const generar = async () => {
    setGenerando(true);
    setError(null);
    setMensaje(null);
    try {
      await generarRespaldo(fincaId, cifrar);
      setMensaje('Respaldo generado y verificado.');
      cargar();
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo generar el respaldo.'));
    } finally {
      setGenerando(false);
    }
  };

  const descargar = async (respaldo) => {
    setOcupado(respaldo.id);
    setError(null);
    try {
      await descargarRespaldo(respaldo.id);
    } catch (err) {
      setError(err.message || mensajeDeError(err, 'No se pudo descargar el respaldo.'));
    } finally {
      setOcupado(null);
    }
  };

  const abrirRestauracion = (respaldo) => {
    setObjetivo(respaldo);
    setConfirmado(false);
    setError(null);
  };

  const restaurar = async () => {
    setRestaurando(true);
    setError(null);
    try {
      const respuesta = await restaurarRespaldo(objetivo.id);
      const total = Object.values(respuesta.data.restaurado || {}).reduce((suma, valor) => suma + valor, 0);
      setObjetivo(null);
      setMensaje(`Finca restaurada al estado del ${fechaLegible(objetivo.creado_en)}: ${total} registros.`);
      cargar();
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo restaurar el respaldo.'));
    } finally {
      setRestaurando(false);
    }
  };

  if (!fincaId) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <Icon name="farm" />
          <h2>No hay una finca activa</h2>
          <p>Elige una finca en el selector de arriba para gestionar sus respaldos.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('RESP', 'Respaldos')}</h1>
          <p>Copia completa de los datos de {fincaActiva?.nombre}: potreros, bovinos, mediciones, pesajes, equipo y cola de sincronización.</p>
        </div>
        <button type="button" className="button button-primary" onClick={generar} disabled={generando}>
          <Icon name="plus" /> {generando ? 'Generando…' : 'Generar respaldo'}
        </button>
      </header>

      {error && <div className="notice notice-danger"><Icon name="alert" /><p>{error}</p></div>}
      {mensaje && <div className="notice notice-info"><Icon name="check" /><p>{mensaje}</p></div>}

      <section className="panel panel-soft">
        <label className="checkbox-row">
          <input type="checkbox" checked={cifrar} onChange={(evento) => setCifrar(evento.target.checked)} />
          Cifrar el archivo del próximo respaldo
        </label>
        <p className="hint">
          Requiere que el servidor tenga configurada la clave <code>BACKUP_ENCRYPTION_KEY</code>. Un respaldo cifrado solo se puede restaurar con esa misma clave, así que consérvala.
        </p>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Respaldos de la finca</h2>
            <p>Cada archivo guarda su huella SHA-256; se comprueba antes de descargar o restaurar.</p>
          </div>
        </div>
        {cargando ? (
          <div className="page-loader"><span /></div>
        ) : respaldos.length === 0 ? (
          <div className="empty-state">
            <Icon name="dash" />
            <h2>Sin respaldos todavía</h2>
            <p>Genera el primero para poder volver a este punto si algo sale mal.</p>
            <button type="button" className="button button-primary" onClick={generar} disabled={generando}>
              <Icon name="plus" /> Generar respaldo
            </button>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th className="is-numeric">Tamaño</th>
                  <th>Cifrado</th>
                  <th>Integridad</th>
                  <th>Huella</th>
                  <th aria-label="Acciones" />
                </tr>
              </thead>
              <tbody>
                {respaldos.map((respaldo) => (
                  <tr key={respaldo.id}>
                    <td>
                      <strong>{fechaLegible(respaldo.creado_en)}</strong>
                      <small>Formato {respaldo.version}</small>
                    </td>
                    <td className="is-numeric">{tamanoLegible(respaldo.tamano_bytes)}</td>
                    <td>
                      {respaldo.cifrado
                        ? <span className="badge badge-ok">Cifrado</span>
                        : <span className="badge badge-muted">Sin cifrar</span>}
                    </td>
                    <td>
                      {respaldo.integridad_verificada
                        ? <span className="badge badge-ok">Verificada</span>
                        : <span className="badge badge-danger">Archivo alterado</span>}
                    </td>
                    <td><small>{respaldo.suma_verificacion.slice(0, 12)}…</small></td>
                    <td className="table-actions">
                      <button
                        type="button" className="link-button"
                        onClick={() => descargar(respaldo)} disabled={ocupado === respaldo.id}
                      >
                        {ocupado === respaldo.id ? 'Descargando…' : 'Descargar'}
                      </button>
                      {puedeRestaurar && (
                        <button
                          type="button" className="link-button is-danger"
                          onClick={() => abrirRestauracion(respaldo)}
                        >
                          Restaurar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {!puedeRestaurar && respaldos.length > 0 && (
          <p className="hint">Restaurar un respaldo requiere el acceso de recuperación, que tu cuenta no tiene asignado.</p>
        )}
      </section>

      <Modal open={Boolean(objetivo)} onClose={() => setObjetivo(null)} title="Restaurar respaldo">
        {objetivo && (
          <div className="modal-form">
            <div className="notice notice-danger">
              <Icon name="alert" />
              <p>
                <strong>Esto reemplaza los datos actuales de la finca.</strong>
                Todo lo registrado después del {fechaLegible(objetivo.creado_en)} se pierde: bovinos, mediciones, pesajes, movimientos y miembros vuelven al estado del respaldo. La operación es completa o no se aplica.
              </p>
            </div>
            <dl className="detail-list">
              <div><dt>Finca</dt><dd>{fincaActiva?.nombre}</dd></div>
              <div><dt>Respaldo del</dt><dd>{fechaLegible(objetivo.creado_en)}</dd></div>
              <div><dt>Tamaño</dt><dd>{tamanoLegible(objetivo.tamano_bytes)}</dd></div>
              <div><dt>Cifrado</dt><dd>{objetivo.cifrado ? 'Sí' : 'No'}</dd></div>
            </dl>
            <label className="modal-confirm">
              <input
                type="checkbox" checked={confirmado}
                onChange={(evento) => setConfirmado(evento.target.checked)}
              />
              Entiendo que los datos posteriores a este respaldo se perderán.
            </label>
            <div className="modal-form-actions">
              <button type="button" className="button button-ghost" onClick={() => setObjetivo(null)}>
                Cancelar
              </button>
              <button
                type="button" className="button button-danger"
                onClick={restaurar} disabled={!confirmado || restaurando}
              >
                {restaurando ? 'Restaurando…' : 'Restaurar la finca'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
