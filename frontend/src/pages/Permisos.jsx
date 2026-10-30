import React, { useMemo, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import { ROLES, RECURSOS } from '../data/rbac';

const ESTILO_ESTADO = {
  si: { icon: 'check', clase: 'bg-green-100 text-green-700', texto: 'Permitido' },
  no: { icon: 'close', clase: 'bg-red-50 text-red-500', texto: 'No permitido' },
  condicional: { icon: 'alert', clase: 'bg-amber-100 text-amber-700', texto: 'Condicional' },
  na: { icon: 'dash', clase: 'bg-gray-100 text-gray-400', texto: 'No aplica' },
};

function Celda({ estado, enFoco, onClick }) {
  const estilo = ESTILO_ESTADO[estado] || ESTILO_ESTADO.na;
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-9 h-9 rounded-full grid place-items-center transition ${estilo.clase} ${enFoco ? 'ring-2 ring-offset-1 ring-campo-500' : 'opacity-40 hover:opacity-100'}`}
      title={estilo.texto}
      aria-label={estilo.texto}
    >
      <Icon name={estilo.icon} className="icon" />
    </button>
  );
}

export default function Permisos() {
  const { rolActivo } = useAuth();
  const rolesValidos = ROLES.map((r) => r.id);
  const [focoRol, setFocoRol] = useState(
    rolesValidos.includes(rolActivo) ? rolActivo : 'todos'
  );
  const [busqueda, setBusqueda] = useState('');
  const [colapsados, setColapsados] = useState(new Set());
  const [seleccion, setSeleccion] = useState(null);

  const recursosFiltrados = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();
    if (!texto) return RECURSOS;
    return RECURSOS.map((r) => ({
      ...r,
      acciones: r.acciones.filter(
        (a) => a.accion.toLowerCase().includes(texto) || r.nombre.toLowerCase().includes(texto)
      ),
    })).filter((r) => r.acciones.length > 0);
  }, [busqueda]);

  const toggleResource = (id) => {
    setColapsados((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const expandirTodo = () => setColapsados(new Set());
  const colapsarTodo = () => setColapsados(new Set(RECURSOS.map((r) => r.id)));

  const seleccionar = (recurso, accion, rol) => {
    setSeleccion({ recurso, accion, rol });
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-campo-900 flex items-center gap-2">
            <Icon name="shield" className="icon text-campo-600" />
            Permisos por rol
          </h1>
          <p className="text-sm text-gray-500">
            Qué puede hacer cada rol en el sistema, según las reglas aplicadas hoy en el backend.
          </p>
        </div>
        <input
          type="text"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          placeholder="Buscar una acción o recurso…"
          className="px-3 py-2 rounded-lg border border-gray-300 text-sm focus:ring-2 focus:ring-campo-500 outline-none sm:w-64"
        />
      </div>

      {/* Filtro de rol: dimensiona el resto de columnas para resaltar una sola */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide mr-1">Resaltar rol:</span>
        <button
          type="button"
          onClick={() => setFocoRol('todos')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
            focoRol === 'todos' ? 'bg-campo-600 text-white border-campo-600' : 'bg-white text-gray-600 border-gray-300 hover:border-campo-400'
          }`}
        >
          Todos
        </button>
        {ROLES.map((r) => (
          <button
            key={r.id}
            type="button"
            onClick={() => setFocoRol(r.id)}
            title={r.descripcion}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${
              focoRol === r.id ? 'bg-campo-600 text-white border-campo-600' : 'bg-white text-gray-600 border-gray-300 hover:border-campo-400'
            }`}
          >
            {r.nombre}
            {rolActivo === r.id && <span className="ml-1 text-[10px] opacity-80">(tú)</span>}
          </button>
        ))}
        <button
          type="button"
          onClick={colapsados.size === RECURSOS.length ? expandirTodo : colapsarTodo}
          className="ml-auto px-3 py-1.5 rounded-full text-xs font-medium border border-gray-300 text-gray-600 hover:border-campo-400 transition"
        >
          {colapsados.size === RECURSOS.length ? 'Expandir todo' : 'Colapsar todo'}
        </button>
      </div>

      {/* Leyenda */}
      <div className="flex flex-wrap items-center gap-4 mb-5 text-xs text-gray-500">
        {Object.entries(ESTILO_ESTADO).map(([clave, estilo]) => (
          <span key={clave} className="flex items-center gap-1.5">
            <span className={`w-6 h-6 rounded-full grid place-items-center ${estilo.clase}`}>
              <Icon name={estilo.icon} />
            </span>
            {estilo.texto}
          </span>
        ))}
      </div>

      {/* Panel de detalle de la celda seleccionada */}
      <div className="bg-campo-50 border border-campo-100 rounded-xl p-4 mb-6 min-h-[88px]">
        {seleccion ? (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${ESTILO_ESTADO[seleccion.accion.estado[seleccion.rol] || 'na'].clase}`}>
                {ESTILO_ESTADO[seleccion.accion.estado[seleccion.rol] || 'na'].texto}
              </span>
              <span className="text-sm font-semibold text-campo-900">
                {ROLES.find((r) => r.id === seleccion.rol)?.nombre} · {seleccion.accion.accion}
              </span>
            </div>
            <p className="text-sm text-gray-600">
              {seleccion.accion.detalle || 'Sin condiciones adicionales a las de su rol en la finca.'}
            </p>
            {seleccion.accion.referencia && (
              <p className="text-xs text-gray-400 mt-1.5 font-mono">{seleccion.accion.referencia}</p>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            Haz clic en cualquier celda de la tabla para ver exactamente qué regla aplica y dónde está definida en el código.
          </p>
        )}
      </div>

      {/* Matriz por recurso */}
      <div className="space-y-4">
        {recursosFiltrados.map((recurso) => {
          const abierto = !colapsados.has(recurso.id);
          return (
            <div key={recurso.id} className="bg-white rounded-xl shadow-sm border border-campo-100 overflow-hidden">
              <button
                type="button"
                onClick={() => toggleResource(recurso.id)}
                className="w-full flex items-center justify-between px-5 py-3.5 bg-campo-50 text-left"
              >
                <span className="flex items-center gap-2 font-semibold text-campo-900 text-sm">
                  <Icon name={recurso.icon} className="icon text-campo-600" />
                  {recurso.nombre}
                </span>
                <Icon name="chevron" className={`icon text-campo-600 transition-transform ${abierto ? 'rotate-180' : ''}`} />
              </button>
              {abierto && (
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-campo-50 text-xs text-gray-500">
                      <th className="px-5 py-2 font-semibold w-1/3">Acción</th>
                      {ROLES.map((r) => (
                        <th key={r.id} className="px-2 py-2 font-semibold text-center">
                          {r.nombre}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-campo-50 text-sm">
                    {recurso.acciones.map((accion) => (
                      <tr key={accion.accion} className="hover:bg-campo-50/40">
                        <td className="px-5 py-3 text-campo-900">{accion.accion}</td>
                        {ROLES.map((r) => (
                          <td key={r.id} className="px-2 py-2 text-center">
                            <div className="flex justify-center">
                              <Celda
                                estado={accion.estado[r.id] || 'na'}
                                enFoco={focoRol === 'todos' || focoRol === r.id}
                                onClick={() => seleccionar(recurso, accion, r.id)}
                              />
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          );
        })}
        {recursosFiltrados.length === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-campo-100 p-12 text-center">
            <p className="text-gray-500">Ninguna acción coincide con "{busqueda}".</p>
          </div>
        )}
      </div>
    </div>
  );
}
