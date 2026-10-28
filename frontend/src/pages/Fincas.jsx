import React, { useEffect, useState } from 'react';
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { useAuth } from '../context/AuthContext';
import {
  getFincas,
  createFinca,
  updateFinca,
  deleteFinca,
} from '../services/farmService';

// Fix clásico del ícono por defecto de Leaflet cuando se usa con bundlers:
// cargamos los PNG oficiales desde el CDN para evitar depender de rutas locales.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Centro inicial del mapa cuando no hay coordenadas previas (centro geográfico de Colombia).
const CENTRO_COLOMBIA = [4.5709, -74.2973];
const ZOOM_INICIAL = 6;

// Insignia de rol que el usuario tiene EN CADA finca (puede variar entre tarjetas).
const rolBadge = {
  propietario: { label: 'Propietario', color: 'bg-campo-100 text-campo-700' },
  administrador: { label: 'Administrador', color: 'bg-amber-100 text-amber-700' },
  operario: { label: 'Operario', color: 'bg-blue-100 text-blue-700' },
};

// --- Modal genérico ---
function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-campo-900">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// Detecta si una cadena luce como "lat,lng" para formatearla con el ícono 📍.
function parsearCoordenadas(texto) {
  if (!texto || typeof texto !== 'string') return null;
  const limpio = texto.replace(/\s/g, '');
  const match = limpio.match(/^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/);
  if (!match) return null;
  const lat = Number(match[1]);
  const lng = Number(match[2]);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
  if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return null;
  return { lat, lng };
}

function formatearCoord(valor) {
  return Number(valor).toFixed(6);
}

// Mantiene el mapa centrado en la posición cuando ésta cambia (p. ej. al abrirlo con coordenadas previas).
function RecentrarMapa({ posicion }) {
  const map = useMap();
  useEffect(() => {
    if (posicion) map.setView(posicion, Math.max(map.getZoom(), 12));
  }, [posicion, map]);
  return null;
}

// Captura clics del mapa para ubicar o mover el marcador.
function MarcadorInteractivo({ posicion, onPick }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  if (!posicion) return null;
  return (
    <Marker
      position={posicion}
      draggable
      eventHandlers={{
        dragend: (e) => {
          const { lat, lng } = e.target.getLatLng();
          onPick(lat, lng);
        },
      }}
    />
  );
}

export default function Fincas() {
  // Crear una finca te vuelve su propietario (RF-02). Se restringe esa
  // acción a quien ya está actuando como propietario; administrador y
  // operario solo consultan/editan según lo que el backend ya les permite.
  const { rolActivo } = useAuth();
  const puedeCrear = rolActivo === 'propietario';
  const [fincas, setFincas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nombre: '', ubicacion: '', lat: null, lng: null });
  const [mapaAbierto, setMapaAbierto] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const fetchFincas = () => {
    setLoading(true);
    getFincas()
      .then((res) => setFincas(res.data.results || res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchFincas(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ nombre: '', ubicacion: '', lat: null, lng: null });
    setMapaAbierto(false);
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (finca) => {
    const coords = parsearCoordenadas(finca.ubicacion);
    setEditing(finca);
    setForm({
      nombre: finca.nombre,
      ubicacion: finca.ubicacion || '',
      lat: coords?.lat ?? null,
      lng: coords?.lng ?? null,
    });
    setMapaAbierto(false);
    setError(null);
    setModalOpen(true);
  };

  // Se dispara desde el mapa (clic o arrastre del marcador).
  const seleccionarPunto = (lat, lng) => {
    const latFmt = formatearCoord(lat);
    const lngFmt = formatearCoord(lng);
    setForm((prev) => ({ ...prev, lat, lng, ubicacion: `${latFmt}, ${lngFmt}` }));
  };

  // Si el propietario edita el texto a mano, re-sincroniza las coordenadas si siguen siendo válidas.
  const onUbicacionChange = (e) => {
    const texto = e.target.value;
    const coords = parsearCoordenadas(texto);
    setForm((prev) => ({
      ...prev,
      ubicacion: texto,
      lat: coords?.lat ?? null,
      lng: coords?.lng ?? null,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = { nombre: form.nombre, ubicacion: form.ubicacion };
      if (editing) {
        await updateFinca(editing.id, payload);
      } else {
        await createFinca(payload);
      }
      setModalOpen(false);
      fetchFincas();
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        const msgs = [];
        for (const key in data) {
          const val = Array.isArray(data[key]) ? data[key].join(', ') : data[key];
          msgs.push(val);
        }
        setError(msgs.join(' | '));
      } else {
        setError('Error al guardar.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (finca) => {
    if (!window.confirm(`¿Eliminar la finca "${finca.nombre}"?`)) return;
    try {
      await deleteFinca(finca.id);
      fetchFincas();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al eliminar.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-campo-300 border-t-campo-600 rounded-full animate-spin" />
      </div>
    );
  }

  const posicionMapa = form.lat != null && form.lng != null ? [form.lat, form.lng] : null;
  const centroMapa = posicionMapa || CENTRO_COLOMBIA;
  const zoomMapa = posicionMapa ? 13 : ZOOM_INICIAL;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-campo-900">Mis Fincas</h1>
          <p className="text-sm text-gray-500">Gestiona las fincas de tu propiedad.</p>
        </div>
        {puedeCrear && (
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 bg-campo-600 text-white rounded-lg text-sm font-medium hover:bg-campo-700 transition"
          >
            <span className="text-lg leading-none">+</span> Nueva finca
          </button>
        )}
      </div>

      {fincas.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
          <p className="text-5xl mb-4">🌾</p>
          <p className="text-gray-500 text-lg mb-2">No tienes fincas registradas</p>
          {puedeCrear ? (
            <>
              <p className="text-gray-400 text-sm mb-6">Crea tu primera finca para empezar a gestionar tu ganado.</p>
              <button
                onClick={openCreate}
                className="px-6 py-2.5 bg-campo-600 text-white rounded-lg text-sm font-medium hover:bg-campo-700 transition"
              >
                Crear mi primera finca
              </button>
            </>
          ) : (
            <p className="text-gray-400 text-sm">Todavía no te han asignado a ninguna finca.</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {fincas.map((finca) => {
            const coords = parsearCoordenadas(finca.ubicacion);
            const textoUbicacion = coords
              ? `📍 ${formatearCoord(coords.lat)}, ${formatearCoord(coords.lng)}`
              : (finca.ubicacion || 'Sin ubicación');
            return (
              <div
                key={finca.id}
                className="bg-white rounded-xl shadow-sm border border-campo-100 p-5 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-campo-100 flex items-center justify-center text-xl">
                      🌾
                    </div>
                    <div>
                      <h3 className="font-semibold text-campo-900">{finca.nombre}</h3>
                      <p className="text-sm text-gray-400">{textoUbicacion}</p>
                    </div>
                  </div>
                </div>

                <div className="mt-3">
                  <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${rolBadge[finca.mi_rol]?.color || 'bg-gray-100 text-gray-600'}`}>
                    {rolBadge[finca.mi_rol]?.label || finca.mi_rol}
                  </span>
                </div>

                {/* RF-10 / RNF-11: solo el propietario de ESTA finca puede editarla o eliminarla.
                    Administrador y operario solo la consultan. */}
                {finca.mi_rol === 'propietario' && (
                  <div className="mt-4 pt-4 border-t border-campo-50 flex items-center gap-2">
                    <button
                      onClick={() => openEdit(finca)}
                      className="flex-1 py-2 text-sm font-medium text-campo-600 bg-campo-50 rounded-lg hover:bg-campo-100 transition"
                    >
                      ✏️ Editar
                    </button>
                    <button
                      onClick={() => handleDelete(finca)}
                      className="flex-1 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition"
                    >
                      🗑️ Eliminar
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modal crear/editar */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? 'Editar Finca' : 'Nueva Finca'}
      >
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">
                Nombre de la finca
              </label>
              <input
                type="text"
                required
                placeholder="Ej: Hacienda La Esperanza"
                value={form.nombre}
                onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">
                Ubicación <span className="text-gray-400 font-normal">(opcional)</span>
              </label>
              <input
                type="text"
                placeholder='Ej: Vereda El Porvenir, Montería  o  "9.242200, -75.384700"'
                value={form.ubicacion}
                onChange={onUbicacionChange}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
              <button
                type="button"
                onClick={() => setMapaAbierto((v) => !v)}
                className="mt-2 text-xs font-medium text-campo-700 hover:text-campo-900 underline"
              >
                {mapaAbierto ? 'Ocultar mapa' : '📍 Seleccionar en mapa'}
              </button>
              {mapaAbierto && (
                <div className="mt-2 rounded-lg overflow-hidden border border-campo-100">
                  <MapContainer
                    key={editing?.id || 'nueva'}
                    center={centroMapa}
                    zoom={zoomMapa}
                    style={{ height: 300, width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                    <RecentrarMapa posicion={posicionMapa} />
                    <MarcadorInteractivo posicion={posicionMapa} onPick={seleccionarPunto} />
                  </MapContainer>
                  <p className="px-3 py-1.5 text-[11px] text-gray-500 bg-campo-50">
                    Haz clic en el mapa para fijar la ubicación; arrastra el marcador para ajustarla.
                  </p>
                </div>
              )}
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg bg-campo-600 text-white text-sm font-medium hover:bg-campo-700 disabled:opacity-50 transition"
            >
              {saving ? 'Guardando...' : editing ? 'Actualizar' : 'Crear finca'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
