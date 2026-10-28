import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Texto de rol para la etiqueta de cada finca en el dropdown.
const etiquetaRol = {
  propietario: 'Propietario',
  administrador: 'Administrador',
  operario: 'Operario',
};

// Dashboard al que se redirige cuando el usuario cambia la finca activa.
const rutaPorRol = {
  propietario: '/propietario',
  administrador: '/administracion',
  operario: '/operario',
};

export default function SelectorFinca() {
  const { fincas, fincaActivaId, setFincaActiva } = useAuth();
  const navigate = useNavigate();

  if (!fincas || fincas.length === 0) return null;

  const onChange = (e) => {
    const id = e.target.value;
    setFincaActiva(id);
    const nueva = fincas.find((f) => f.id === id);
    // Al cambiar de finca, llevamos al usuario al dashboard que corresponde a
    // su rol en esa finca; así el sidebar y las opciones se recalculan.
    if (nueva) {
      navigate(rutaPorRol[nueva.mi_rol] || '/fincas', { replace: true });
    }
  };

  return (
    <label className="finca-switcher" title="Finca activa">
      <span className="finca-switcher-label">Finca</span>
      <select
        value={fincaActivaId || ''}
        onChange={onChange}
        aria-label="Finca activa"
      >
        {fincas.map((f) => (
          <option key={f.id} value={f.id}>
            {f.nombre} · {etiquetaRol[f.mi_rol] || f.mi_rol}
          </option>
        ))}
      </select>
    </label>
  );
}
