import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  getFincas,
  getInvitaciones,
  createInvitacion,
  cancelInvitacion,
  acceptInvitacion,
} from '../services/farmService';

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

const estadoLabels = {
  pendiente: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-700' },
  aceptada: { label: 'Aceptada', color: 'bg-green-100 text-green-700' },
  cancelada: { label: 'Cancelada', color: 'bg-gray-100 text-gray-500' },
  expirada: { label: 'Expirada', color: 'bg-red-100 text-red-600' },
};

export default function Invitaciones() {
  const [fincas, setFincas] = useState([]);
  const [selectedFinca, setSelectedFinca] = useState('');
  const [invitaciones, setInvitaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalCreate, setModalCreate] = useState(false);
  const [modalAccept, setModalAccept] = useState(false);
  const [form, setForm] = useState({ telefono: '', email: '', rol: 'operario', expira_en: '' });
  const [tokenAccept, setTokenAccept] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [acceptMsg, setAcceptMsg] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();

  // Si llegamos desde el enlace del correo de invitación (?token=...), se
  // precarga el código y se abre directamente el modal de aceptar.
  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setTokenAccept(token);
      setModalAccept(true);
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete('token');
        return next;
      }, { replace: true });
    }
  }, []);

  useEffect(() => {
    getFincas()
      .then((res) => {
        const list = res.data.results || res.data;
        // RF-04: solo el propietario invita. Si una finca llega con otro
        // mi_rol (p. ej. eres operario en otra), el backend la devolvería
        // vacía de todas formas; no la ofrecemos en el selector.
        const propias = list.filter((f) => f.mi_rol === 'propietario');
        setFincas(propias);
        if (propias.length > 0) setSelectedFinca(propias[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const fetchInvitaciones = () => {
    if (!selectedFinca) return;
    setLoading(true);
    getInvitaciones(selectedFinca)
      .then((res) => setInvitaciones(res.data.results || res.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchInvitaciones(); }, [selectedFinca]);

  // Default expira_en a 7 días adelante
  const getDefaultExpiry = () => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().slice(0, 16);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      await createInvitacion({
        finca: selectedFinca,
        telefono: form.telefono,
        email: form.email,
        rol: form.rol,
        expira_en: new Date(form.expira_en).toISOString(),
      });
      setModalCreate(false);
      setForm({ telefono: '', email: '', rol: 'operario', expira_en: '' });
      fetchInvitaciones();
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
        setError('Error al crear invitación.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (inv) => {
    if (!window.confirm('¿Cancelar esta invitación?')) return;
    try {
      await cancelInvitacion(inv.id);
      fetchInvitaciones();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al cancelar.');
    }
  };

  const handleAccept = async (e) => {
    e.preventDefault();
    setAcceptMsg(null);
    setError(null);
    setSaving(true);
    try {
      const res = await acceptInvitacion(tokenAccept);
      setAcceptMsg(`✅ ¡Invitación aceptada! Finca: ${res.data.finca_id}`);
      setTokenAccept('');
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
        setError('Error al aceptar invitación.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-campo-900">Invitaciones</h1>
          <p className="text-sm text-gray-500">Invita ganaderos a tus fincas o acepta invitaciones.</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
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
            onClick={() => { setError(null); setForm({ ...form, expira_en: getDefaultExpiry() }); setModalCreate(true); }}
            disabled={!selectedFinca}
            className="flex items-center gap-2 px-4 py-2.5 bg-campo-600 text-white rounded-lg text-sm font-medium hover:bg-campo-700 transition disabled:opacity-50"
          >
            <span className="text-lg leading-none">+</span> Invitar
          </button>
          <button
            onClick={() => { setError(null); setAcceptMsg(null); setModalAccept(true); }}
            className="flex items-center gap-2 px-4 py-2.5 bg-white border border-campo-300 text-campo-700 rounded-lg text-sm font-medium hover:bg-campo-50 transition"
          >
            🔑 Aceptar invitación
          </button>
        </div>
      </div>

      {fincas.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
          <p className="text-gray-500">Solo puedes invitar a fincas donde eres propietario.</p>
          <p className="text-gray-400 text-sm mt-1">Crea tu primera finca en la sección "Fincas".</p>
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-8 h-8 border-4 border-campo-300 border-t-campo-600 rounded-full animate-spin" />
        </div>
      ) : invitaciones.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
          <p className="text-5xl mb-4">✉️</p>
          <p className="text-gray-500 text-lg">No hay invitaciones para esta finca.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-campo-100 overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-campo-50 text-sm text-campo-700">
              <tr>
                <th className="px-5 py-3 font-semibold">Teléfono</th>
                <th className="px-5 py-3 font-semibold">Correo</th>
                <th className="px-5 py-3 font-semibold">Rol</th>
                <th className="px-5 py-3 font-semibold">Estado</th>
                <th className="px-5 py-3 font-semibold">Expira</th>
                <th className="px-5 py-3 font-semibold text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-campo-50 text-sm">
              {invitaciones.map((inv) => {
                const estado = estadoLabels[inv.estado] || { label: inv.estado, color: 'bg-gray-100 text-gray-700' };
                return (
                  <tr key={inv.id} className="hover:bg-campo-50/50">
                    <td className="px-5 py-3.5 font-medium text-campo-900">{inv.telefono}</td>
                    <td className="px-5 py-3.5 text-gray-500">{inv.email || '—'}</td>
                    <td className="px-5 py-3.5 capitalize">{inv.rol}</td>
                    <td className="px-5 py-3.5">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${estado.color}`}>
                        {estado.label}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-gray-500">
                      {new Date(inv.expira_en).toLocaleDateString('es-CO')}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {inv.estado === 'pendiente' && (
                        <button
                          onClick={() => handleCancel(inv)}
                          className="text-red-500 hover:text-red-700 text-xs font-medium hover:underline"
                        >
                          Cancelar
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

      {/* Modal crear invitación */}
      <Modal open={modalCreate} onClose={() => setModalCreate(false)} title="Invitar a finca">
        <form onSubmit={handleCreate}>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Teléfono</label>
              <input
                type="tel"
                required
                placeholder="+57 300 123 4567"
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Correo electrónico</label>
              <input
                type="email"
                required
                placeholder="nombre@correo.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
              <p className="text-xs text-gray-400 mt-1">A este correo llega el enlace para unirse a la finca.</p>
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
            <div>
              <label className="block text-sm font-semibold text-campo-800 mb-1">Fecha de expiración</label>
              <input
                type="datetime-local"
                required
                value={form.expira_en}
                onChange={(e) => setForm({ ...form, expira_en: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
              />
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={() => setModalCreate(false)}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg bg-campo-600 text-white text-sm font-medium hover:bg-campo-700 disabled:opacity-50 transition"
            >
              {saving ? 'Enviando...' : 'Enviar invitación'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal aceptar invitación */}
      <Modal open={modalAccept} onClose={() => setModalAccept(false)} title="Aceptar Invitación">
        <form onSubmit={handleAccept}>
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}
          {acceptMsg && (
            <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">
              {acceptMsg}
            </div>
          )}
          <div>
            <label className="block text-sm font-semibold text-campo-800 mb-1">Token de invitación</label>
            <input
              type="text"
              required
              placeholder="ej: a1b2c3d4-e5f6-..."
              value={tokenAccept}
              onChange={(e) => setTokenAccept(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-campo-500 focus:border-campo-500 outline-none transition text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">
              Ingrese el token UUID que le compartió el administrador de la finca.
            </p>
          </div>
          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={() => setModalAccept(false)}
              className="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 text-sm font-medium hover:bg-gray-50 transition"
            >
              Cerrar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 py-2.5 rounded-lg bg-campo-600 text-white text-sm font-medium hover:bg-campo-700 disabled:opacity-50 transition"
            >
              {saving ? 'Aceptando...' : 'Aceptar invitación'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
