import React, { useState, useEffect } from 'react';
import { getFincas, getMembresias, createMembresia, updateMembresia, deleteMembresia } from '../services/farmService';
import { buscarUsuario } from '../services/authService';

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

const rolLabels = {
  administrador: { label: 'Administrador', color: 'bg-campo-100 text-campo-700' },
  operario: { label: 'Operario', color: 'bg-amber-100 text-amber-700' },
};

export default function Membresias() {
  const [fincas, setFincas] = useState([]);
  const [selectedFinca, setSelectedFinca] = useState('');
  const [membresias, setMembresias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ usuarioId: '', rol: 'operario' });
  const [busqueda, setBusqueda] = useState('');
  const [resultadosBusqueda, setResultadosBusqueda] = useState([]);
  const [buscando, setBuscando] = useState(false);
  const [mostrarLista, setMostrarLista] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [cambiandoRolId, setCambiandoRolId] = useState(null);

  useEffect(() => {
    getFincas()
      .then((res) => {
        const list = res.data.results || res.data;
        // RF-04: solo el propietario gestiona miembros. Si una finca te llega
        // aquí con mi_rol distinto (p. ej. eres operario en otra), el backend
        // la devolvería vacía de todas formas; mejor no ofrecerla en el selector.
        const propias = list.filter((f) => f.mi_rol === 'propietario');
        setFincas(propias);
        if (propias.length > 0) setSelectedFinca(propias[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedFinca) return;
    setLoading(true);
    getMembresias(selectedFinca)
      .then((res) => setMembresias(res.data.results || res.data))
      .finally(() => setLoading(false));
  }, [selectedFinca]);

  // Debounce de 400 ms sobre la búsqueda. Mínimo 3 caracteres para disparar la consulta.
  useEffect(() => {
    const texto = busqueda.trim();
    if (texto.length < 3) {
      setResultadosBusqueda([]);
      setBuscando(false);
      return undefined;
    }
    setBuscando(true);
    const timer = setTimeout(async () => {
      try {
        const res = await buscarUsuario(texto);
        setResultadosBusqueda(res.data || []);
      } catch {
        setResultadosBusqueda([]);
      } finally {
        setBuscando(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [busqueda]);

  const limpiarModal = () => {
    setForm({ usuarioId: '', rol: 'operario' });
    setBusqueda('');
    setResultadosBusqueda([]);
    setMostrarLista(false);
    setError(null);
  };

  const abrirModal = () => {
    limpiarModal();
    setModalOpen(true);
  };

  const cerrarModal = () => {
    setModalOpen(false);
    limpiarModal();
  };

  const onBusquedaChange = (e) => {
    const valor = e.target.value;
    setBusqueda(valor);
    setMostrarLista(true);
    // Si el usuario edita el texto, se deshace la selección previa.
    if (form.usuarioId) setForm({ ...form, usuarioId: '' });
  };

  const seleccionarUsuario = (u) => {
    setForm({ ...form, usuarioId: u.id });
    setBusqueda(u.username);
    setResultadosBusqueda([]);
    setMostrarLista(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!form.usuarioId) {
      setError('Selecciona un usuario de la lista.');
      return;
    }
    setSaving(true);
    try {
      await createMembresia({
        finca: selectedFinca,
        usuario: form.usuarioId,
        rol: form.rol,
      });
      setModalOpen(false);
      limpiarModal();
      // Refrescar
      const res = await getMembresias(selectedFinca);
      setMembresias(res.data.results || res.data);
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
        setError('Error al agregar miembro.');
      }
    } finally {
      setSaving(false);
    }
  };

  // RF-04: el propietario puede cambiar el rol de un miembro ya existente
  // (operario <-> administrador) sin tener que retirarlo y volver a agregarlo.
  const handleCambiarRol = async (membresia, nuevoRol) => {
    if (nuevoRol === membresia.rol) return;
    setCambiandoRolId(membresia.id);
    try {
      await updateMembresia(membresia.id, { rol: nuevoRol });
      const res = await getMembresias(selectedFinca);
      setMembresias(res.data.results || res.data);
    } catch (err) {
      const data = err.response?.data;
      alert(data?.detail || Object.values(data || {})[0] || 'Error al cambiar el rol.');
    } finally {
      setCambiandoRolId(null);
    }
  };

  const handleDelete = async (membresia) => {
    const nombre = membresia.usuario?.username || membresia.usuario;
    if (!window.confirm(`¿Retirar a "${nombre}" de la finca?`)) return;
    try {
      await deleteMembresia(membresia.id);
      const res = await getMembresias(selectedFinca);
      setMembresias(res.data.results || res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al retirar miembro.');
    }
  };

  const hayTextoSuficiente = busqueda.trim().length >= 3;
  const seleccionConfirmada = Boolean(form.usuarioId) && !mostrarLista;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-campo-900">Miembros</h1>
          <p className="text-sm text-gray-500">Administra los miembros de tus fincas.</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedFinca}
            onChange={(e) => setSelectedFinca(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-campo-500 outline-none"
          >
            {fincas.map((f) => (
              <option key={f.id} value={f.id}>{f.nombre}</option>
            ))}
          </select>
          <button
            onClick={abrirModal}
            disabled={!selectedFinca}
            className="flex items-center gap-2 px-4 py-2.5 bg-campo-600 text-white rounded-lg text-sm font-medium hover:bg-campo-700 transition disabled:opacity-50"
          >
            <span className="text-lg leading-none">+</span> Agregar
          </button>
        </div>
      </div>

      {fincas.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
          <p className="text-gray-500">Solo puedes gestionar miembros de fincas donde eres propietario.</p>
          <p className="text-gray-400 text-sm mt-1">Crea tu primera finca en la sección "Fincas".</p>
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-8 h-8 border-4 border-campo-300 border-t-campo-600 rounded-full animate-spin" />
        </div>
      ) : membresias.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
          <p className="text-5xl mb-4">👥</p>
          <p className="text-gray-500 text-lg">No hay miembros en esta finca.</p>
          <p className="text-gray-400 text-sm mt-1">Agrega miembros o envía invitaciones por teléfono.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-campo-50 text-sm text-campo-700">
              <tr>
                <th className="px-5 py-3 font-semibold">Usuario</th>
                <th className="px-5 py-3 font-semibold">Rol</th>
                <th className="px-5 py-3 font-semibold">Invitado por</th>
                <th className="px-5 py-3 font-semibold text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-campo-50 text-sm">
              {membresias.map((m) => {
                const rol = rolLabels[m.rol] || { label: m.rol, color: 'bg-gray-100 text-gray-700' };
                return (
                  <tr key={m.id} className="hover:bg-campo-50/50">
                    <td className="px-5 py-3.5 font-medium text-campo-900">
                      {typeof m.usuario === 'object' ? m.usuario.username : m.usuario}
                    </td>
                    <td className="px-5 py-3.5">
                      <select
                        value={m.rol}
                        disabled={cambiandoRolId === m.id}
                        onChange={(e) => handleCambiarRol(m, e.target.value)}
                        className={`text-xs px-2 py-1 rounded-full font-medium border-0 outline-none cursor-pointer disabled:opacity-50 disabled:cursor-wait ${rol.color}`}
                        aria-label={`Rol de ${typeof m.usuario === 'object' ? m.usuario.username : m.usuario}`}
                      >
                        <option value="operario">Operario</option>
                        <option value="administrador">Administrador</option>
                      </select>
                    </td>
                    <td className="px-5 py-3.5 text-gray-500">
                      {typeof m.invitado_por === 'object' ? m.invitado_por.username : m.invitado_por || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(m)}
                        className="text-red-500 hover:text-red-700 text-xs font-medium hover:underline"
                      >
                        Retirar
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal agregar miembro */}
      <Modal open={modalOpen} onClose={cerrarModal} title="Agregar Miembro">
        <form onSubmit={handleSubmit}>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div className="relative">
              <label className="block text-sm font-semibold text-campo-800 mb-1">
                Buscar usuario por nombre o teléfono
              </label>
              <input
                type="text"
                autoComplete="off"
                placeholder="Mínimo 3 caracteres (ej: ana_ganadera o 300…)"
                value={busqueda}
                onChange={onBusquedaChange}
                onFocus={() => setMostrarLista(true)}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
              {hayTextoSuficiente && mostrarLista && (
                <div className="absolute left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto z-10">
                  {buscando && (
                    <div className="px-4 py-2.5 text-sm text-gray-500">Buscando…</div>
                  )}
                  {!buscando && resultadosBusqueda.length === 0 && (
                    <div className="px-4 py-2.5 text-sm text-gray-500">Sin coincidencias.</div>
                  )}
                  {!buscando && resultadosBusqueda.map((u) => (
                    <button
                      key={u.id}
                      type="button"
                      onClick={() => seleccionarUsuario(u)}
                      className="w-full text-left px-4 py-2.5 text-sm hover:bg-campo-50 flex justify-between gap-3"
                    >
                      <span className="font-medium text-campo-900">{u.username}</span>
                      <span className="text-gray-500">{u.telefono || '—'}</span>
                    </button>
                  ))}
                </div>
              )}
              {seleccionConfirmada && (
                <p className="mt-1 text-xs text-campo-700">Usuario seleccionado: <strong>{busqueda}</strong></p>
              )}
            </div>
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Rol</label>
              <select
                value={form.rol}
                onChange={(e) => setForm({ ...form, rol: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 outline-none text-sm"
              >
                <option value="operario">Operario</option>
                <option value="administrador">Administrador</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={cerrarModal}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg bg-campo-600 text-white text-sm font-medium hover:bg-campo-700 disabled:opacity-50 transition"
            >
              {saving ? 'Guardando...' : 'Agregar miembro'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
