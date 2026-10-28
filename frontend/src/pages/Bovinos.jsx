import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  getBovinos,
  createBovino,
  updateBovino,
  aprobarPerfilBovino,
  desactivarBovino,
  getPotreros,
  createPotrero,
  getRazas,
} from '../services/cattleService';

function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-campo-900">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        {children}
      </div>
    </div>
  );
}

const estadoBadge = {
  perfil_pendiente: { label: 'Pendiente de perfil', color: 'bg-amber-100 text-amber-700' },
  activo: { label: 'Activo', color: 'bg-green-100 text-green-700' },
  vendido: { label: 'Vendido', color: 'bg-gray-100 text-gray-600' },
  muerto: { label: 'Muerto', color: 'bg-gray-100 text-gray-600' },
  retirado: { label: 'Retirado', color: 'bg-gray-100 text-gray-600' },
};

const sexoLabel = { macho: 'Macho', hembra: 'Hembra' };

const formVacio = {
  arete: '', raza: '', sexo: 'hembra', potrero: '',
  categoria_productiva: '', estado_fisiologico: '', fecha_nacimiento_estimada: '',
};

export default function Bovinos() {
  const { fincaActiva, rolActivo } = useAuth();
  // RF-09: solo propietario y administrador editan/aprueban/dan de baja.
  const puedeGestionar = rolActivo === 'propietario' || rolActivo === 'administrador';

  const [bovinos, setBovinos] = useState([]);
  const [potreros, setPotreros] = useState([]);
  const [razas, setRazas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(formVacio);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Alta rápida de potrero cuando la finca todavía no tiene ninguno.
  const [nuevoPotrero, setNuevoPotrero] = useState('');
  const [creandoPotrero, setCreandoPotrero] = useState(false);

  // Modal de baja (vendido / muerto / retirado).
  const [bajaTarget, setBajaTarget] = useState(null);
  const [bajaForm, setBajaForm] = useState({ estado: 'vendido', motivo: '' });
  const [bajaSaving, setBajaSaving] = useState(false);
  const [bajaError, setBajaError] = useState(null);

  const fincaId = fincaActiva?.id;

  const fetchDatos = () => {
    if (!fincaId) { setLoading(false); return; }
    setLoading(true);
    Promise.all([getBovinos(fincaId), getPotreros(fincaId)])
      .then(([resBovinos, resPotreros]) => {
        setBovinos(resBovinos.data.results || resBovinos.data || []);
        setPotreros(resPotreros.data.results || resPotreros.data || []);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDatos(); }, [fincaId]);

  useEffect(() => {
    getRazas().then((res) => setRazas(res.data.results || res.data || []));
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ ...formVacio, potrero: potreros[0]?.id || '', raza: razas[0]?.id || '' });
    setNuevoPotrero('');
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (bovino) => {
    setEditing(bovino);
    setForm({
      arete: bovino.arete,
      raza: bovino.raza,
      sexo: bovino.sexo,
      potrero: bovino.potrero,
      categoria_productiva: bovino.categoria_productiva,
      estado_fisiologico: bovino.estado_fisiologico || '',
      fecha_nacimiento_estimada: bovino.fecha_nacimiento_estimada || '',
    });
    setError(null);
    setModalOpen(true);
  };

  const handleCrearPotrero = async () => {
    if (!nuevoPotrero.trim()) return;
    setCreandoPotrero(true);
    try {
      const res = await createPotrero({ finca: fincaId, nombre: nuevoPotrero.trim() });
      const creado = res.data;
      setPotreros((prev) => [...prev, creado]);
      setForm((prev) => ({ ...prev, potrero: creado.id }));
      setNuevoPotrero('');
    } catch (err) {
      setError(err.response?.data?.nombre?.[0] || 'No se pudo crear el potrero.');
    } finally {
      setCreandoPotrero(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.potrero) {
      setError('Selecciona o crea un potrero primero.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        arete: form.arete,
        raza: form.raza,
        sexo: form.sexo,
        potrero: form.potrero,
        categoria_productiva: form.categoria_productiva,
        estado_fisiologico: form.estado_fisiologico || '',
        fecha_nacimiento_estimada: form.fecha_nacimiento_estimada || null,
      };
      if (editing) {
        await updateBovino(editing.id, payload);
      } else {
        await createBovino({ ...payload, finca: fincaId });
      }
      setModalOpen(false);
      fetchDatos();
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

  const handleAprobar = async (bovino) => {
    try {
      await aprobarPerfilBovino(bovino.id);
      fetchDatos();
    } catch (err) {
      alert(err.response?.data?.detail || 'No se pudo aprobar el perfil.');
    }
  };

  const abrirBaja = (bovino) => {
    setBajaTarget(bovino);
    setBajaForm({ estado: 'vendido', motivo: '' });
    setBajaError(null);
  };

  const handleBaja = async (e) => {
    e.preventDefault();
    setBajaError(null);
    setBajaSaving(true);
    try {
      await desactivarBovino(bajaTarget.id, bajaForm.estado, bajaForm.motivo);
      setBajaTarget(null);
      fetchDatos();
    } catch (err) {
      const data = err.response?.data;
      setBajaError(data?.motivo?.[0] || data?.estado?.[0] || data?.detail || 'Error al dar de baja.');
    } finally {
      setBajaSaving(false);
    }
  };

  const nombreRaza = (id) => razas.find((r) => r.id === id)?.nombre || '—';
  const nombrePotrero = (id) => potreros.find((p) => p.id === id)?.nombre || '—';

  if (!fincaId) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
        <p className="text-5xl mb-4">🐄</p>
        <p className="text-gray-500 text-lg">No tienes una finca activa.</p>
        <p className="text-gray-400 text-sm mt-1">Elige una finca en el selector de arriba, o crea/únete a una primero.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-campo-900">Bovinos</h1>
          <p className="text-sm text-gray-500">{fincaActiva?.nombre}</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 px-4 py-2.5 bg-campo-600 text-white rounded-lg text-sm font-medium hover:bg-campo-700 transition"
        >
          <span className="text-lg leading-none">+</span> Registrar bovino
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-8 h-8 border-4 border-campo-300 border-t-campo-600 rounded-full animate-spin" />
        </div>
      ) : bovinos.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
          <p className="text-5xl mb-4">🐄</p>
          <p className="text-gray-500 text-lg">No hay bovinos registrados en esta finca.</p>
          <p className="text-gray-400 text-sm mt-1">Registra el primero con el botón de arriba.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-campo-50 text-sm text-campo-700">
              <tr>
                <th className="px-5 py-3 font-semibold">Arete</th>
                <th className="px-5 py-3 font-semibold">Raza</th>
                <th className="px-5 py-3 font-semibold">Sexo</th>
                <th className="px-5 py-3 font-semibold">Potrero</th>
                <th className="px-5 py-3 font-semibold">Categoría</th>
                <th className="px-5 py-3 font-semibold">Estado</th>
                <th className="px-5 py-3 font-semibold text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-campo-50 text-sm">
              {bovinos.map((b) => {
                const estado = estadoBadge[b.estado_operativo] || { label: b.estado_operativo, color: 'bg-gray-100 text-gray-700' };
                const deBaja = Boolean(b.desactivado_en);
                return (
                  <tr key={b.id} className="hover:bg-campo-50/50">
                    <td className="px-5 py-3.5 font-medium text-campo-900">{b.arete}</td>
                    <td className="px-5 py-3.5 text-gray-600">{nombreRaza(b.raza)}</td>
                    <td className="px-5 py-3.5 text-gray-600">{sexoLabel[b.sexo] || b.sexo}</td>
                    <td className="px-5 py-3.5 text-gray-600">{nombrePotrero(b.potrero)}</td>
                    <td className="px-5 py-3.5 text-gray-600">{b.categoria_productiva || '—'}</td>
                    <td className="px-5 py-3.5">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${estado.color}`}>{estado.label}</span>
                      {deBaja && b.motivo_desactivacion && (
                        <p className="text-[11px] text-gray-400 mt-1">{b.motivo_desactivacion}</p>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right whitespace-nowrap">
                      {!deBaja && puedeGestionar && b.estado_operativo === 'perfil_pendiente' && (
                        <button onClick={() => handleAprobar(b)} className="text-campo-600 hover:text-campo-800 text-xs font-medium hover:underline mr-3">
                          Aprobar perfil
                        </button>
                      )}
                      {!deBaja && puedeGestionar && (
                        <button onClick={() => openEdit(b)} className="text-campo-600 hover:text-campo-800 text-xs font-medium hover:underline mr-3">
                          Editar
                        </button>
                      )}
                      {!deBaja && puedeGestionar && (
                        <button onClick={() => abrirBaja(b)} className="text-red-500 hover:text-red-700 text-xs font-medium hover:underline">
                          Dar de baja
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal crear/editar bovino */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? 'Editar bovino' : 'Registrar bovino'}>
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Arete</label>
              <input
                type="text" required placeholder="ej: A-0231"
                value={form.arete}
                onChange={(e) => setForm({ ...form, arete: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-campo-800 mb-1">Raza</label>
                <select
                  required value={form.raza}
                  onChange={(e) => setForm({ ...form, raza: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 outline-none text-sm"
                >
                  <option value="" disabled>Selecciona…</option>
                  {razas.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-campo-800 mb-1">Sexo</label>
                <select
                  value={form.sexo}
                  onChange={(e) => setForm({ ...form, sexo: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 outline-none text-sm"
                >
                  <option value="hembra">Hembra</option>
                  <option value="macho">Macho</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Potrero</label>
              {potreros.length > 0 ? (
                <select
                  required value={form.potrero}
                  onChange={(e) => setForm({ ...form, potrero: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 outline-none text-sm"
                >
                  <option value="" disabled>Selecciona…</option>
                  {potreros.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                </select>
              ) : (
                <p className="text-xs text-gray-400 mb-2">Esta finca todavía no tiene potreros.</p>
              )}
              {puedeGestionar && (
                <div className="flex gap-2 mt-2">
                  <input
                    type="text" placeholder="Nombre de un potrero nuevo (ej: Potrero 1)"
                    value={nuevoPotrero}
                    onChange={(e) => setNuevoPotrero(e.target.value)}
                    className="flex-1 px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 outline-none text-sm"
                  />
                  <button
                    type="button" onClick={handleCrearPotrero} disabled={creandoPotrero || !nuevoPotrero.trim()}
                    className="px-3 py-2 rounded-lg border border-campo-300 text-campo-700 text-sm font-medium hover:bg-campo-50 disabled:opacity-50 transition"
                  >
                    {creandoPotrero ? '...' : '+ Crear'}
                  </button>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Categoría productiva</label>
              <input
                type="text" required placeholder="ej: Cría, Levante, Ceba, Lechería"
                value={form.categoria_productiva}
                onChange={(e) => setForm({ ...form, categoria_productiva: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-campo-800 mb-1">
                  Estado fisiológico <span className="text-gray-400 font-normal">(opcional)</span>
                </label>
                <input
                  type="text" placeholder="ej: Gestante, Lactando"
                  value={form.estado_fisiologico}
                  onChange={(e) => setForm({ ...form, estado_fisiologico: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-campo-800 mb-1">
                  Nacimiento <span className="text-gray-400 font-normal">(aprox., opcional)</span>
                </label>
                <input
                  type="date"
                  value={form.fecha_nacimiento_estimada}
                  onChange={(e) => setForm({ ...form, fecha_nacimiento_estimada: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
                />
              </div>
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button type="button" onClick={() => setModalOpen(false)} className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="flex-1 py-2.5 rounded-lg bg-campo-600 text-white text-sm font-medium hover:bg-campo-700 disabled:opacity-50 transition">
              {saving ? 'Guardando...' : editing ? 'Actualizar' : 'Registrar'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal dar de baja */}
      <Modal open={Boolean(bajaTarget)} onClose={() => setBajaTarget(null)} title={`Dar de baja a ${bajaTarget?.arete || ''}`}>
        <form onSubmit={handleBaja}>
          {bajaError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{bajaError}</div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Motivo</label>
              <select
                value={bajaForm.estado}
                onChange={(e) => setBajaForm({ ...bajaForm, estado: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 outline-none text-sm"
              >
                <option value="vendido">Vendido</option>
                <option value="muerto">Muerto</option>
                <option value="retirado">Retirado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Detalle</label>
              <input
                type="text" required placeholder="ej: Vendido a finca vecina el 12/10"
                value={bajaForm.motivo}
                onChange={(e) => setBajaForm({ ...bajaForm, motivo: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button type="button" onClick={() => setBajaTarget(null)} className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition">
              Cancelar
            </button>
            <button type="submit" disabled={bajaSaving} className="flex-1 py-2.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition">
              {bajaSaving ? 'Guardando...' : 'Confirmar baja'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
