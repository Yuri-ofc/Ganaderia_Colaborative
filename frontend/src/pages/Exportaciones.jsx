import React, { useState } from 'react';
import Icon from '../components/Icon';
import { useAuth } from '../context/AuthContext';
import { useEtiquetas } from '../context/EtiquetasContext';
import { exportarDatos } from '../services/backupsService';
import { mensajeDeError } from '../services/apiError';

const CONJUNTOS = [
  { codigo: 'bovinos', titulo: 'Bovinos', detalle: 'Arete, raza, sexo, categoría, potrero y estado.' },
  { codigo: 'mediciones', titulo: 'Mediciones', detalle: 'Peso estimado, condición corporal, confianza y modelo usado.' },
  { codigo: 'pesajes', titulo: 'Pesajes', detalle: 'Peso real en báscula con su fecha y tipo de báscula.' },
  { codigo: 'potreros', titulo: 'Potreros', detalle: 'Nombre y fecha de creación de cada potrero.' },
  { codigo: 'miembros', titulo: 'Equipo', detalle: 'Usuario, correo y rol de cada miembro de la finca.' },
];

export default function Exportaciones() {
  const { etiqueta } = useEtiquetas();
  const { fincaActiva } = useAuth();
  const fincaId = fincaActiva?.id;

  const [seleccion, setSeleccion] = useState(['bovinos']);
  const [formato, setFormato] = useState('csv');
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState(null);
  const [mensaje, setMensaje] = useState(null);

  const alternar = (codigo) => {
    setSeleccion((previa) =>
      previa.includes(codigo) ? previa.filter((otro) => otro !== codigo) : [...previa, codigo]);
  };

  const descargar = async () => {
    setDescargando(true);
    setError(null);
    setMensaje(null);
    try {
      await exportarDatos(fincaId, formato, seleccion);
      setMensaje('Exportación generada; revisa las descargas del navegador.');
    } catch (err) {
      setError(err.message || mensajeDeError(err, 'No se pudo generar la exportación.'));
    } finally {
      setDescargando(false);
    }
  };

  if (!fincaId) {
    return (
      <div className="page-content">
        <div className="empty-state">
          <Icon name="farm" />
          <h2>No hay una finca activa</h2>
          <p>Elige una finca en el selector de arriba para exportar sus datos.</p>
        </div>
      </div>
    );
  }

  // Varios conjuntos no caben en una sola tabla CSV, así que el servidor los
  // entrega comprimidos; conviene decirlo antes de descargar.
  const comprimido = formato === 'csv' && seleccion.length > 1;

  return (
    <div className="page-content">
      <header className="page-title-row">
        <div>
          <h1>{etiqueta('EXPO', 'Exportaciones')}</h1>
          <p>Datos de {fincaActiva?.nombre} en un archivo legible, para usarlos en una hoja de cálculo o en otro sistema.</p>
        </div>
      </header>

      <div className="notice notice-info">
        <Icon name="alert" />
        <p>
          <strong>Una exportación no es un respaldo.</strong>
          Sirve para leer y analizar los datos fuera del sistema; no va cifrada y no se puede usar para restaurar la finca. Para eso está el módulo de respaldos.
        </p>
      </div>

      {error && <div className="notice notice-danger"><Icon name="alert" /><p>{error}</p></div>}
      {mensaje && <div className="notice notice-info"><Icon name="check" /><p>{mensaje}</p></div>}

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Qué exportar</h2>
            <p>Elige uno o varios conjuntos de datos.</p>
          </div>
        </div>
        <div className="rbac-resource-grid">
          {CONJUNTOS.map((conjunto) => (
            <label className="rbac-check-row" key={conjunto.codigo}>
              <input
                type="checkbox"
                checked={seleccion.includes(conjunto.codigo)}
                onChange={() => alternar(conjunto.codigo)}
              />
              <span>
                {conjunto.titulo}
                <small className="rbac-code">{conjunto.detalle}</small>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <h2>Formato</h2>
            <p>CSV abre directo en Excel o LibreOffice; JSON conserva la estructura para otro programa.</p>
          </div>
        </div>
        <div className="filter-bar">
          <label>
            Archivo
            <select value={formato} onChange={(evento) => setFormato(evento.target.value)}>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </label>
          <button
            type="button" className="button button-primary"
            onClick={descargar} disabled={descargando || seleccion.length === 0}
          >
            <Icon name="arrow" /> {descargando ? 'Generando…' : 'Descargar exportación'}
          </button>
        </div>
        {seleccion.length === 0 && <p className="hint">Marca al menos un conjunto de datos.</p>}
        {comprimido && (
          <p className="hint">
            Se descargará un .zip con un CSV por conjunto, porque varias tablas no caben en un solo archivo CSV.
          </p>
        )}
      </section>
    </div>
  );
}
