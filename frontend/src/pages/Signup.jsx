import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { register } from '../services/authService';
import api from '../services/api';
import { getInitialDestination } from '../services/navigationService';

const CAMPOS_ES = {
  username: 'Usuario',
  email: 'Correo',
  password: 'Contraseña',
  telefono: 'Teléfono',
  detail: '',
  non_field_errors: '',
};

const errorText = (data) => {
  if (!data) return '';
  if (typeof data === 'string') return data;
  return Object.entries(data)
    .map(([campo, valor]) => {
      const texto = Array.isArray(valor) ? valor.join(' ') : String(valor);
      const etiqueta = CAMPOS_ES[campo];
      if (etiqueta === undefined) return `${campo}: ${texto}`;
      return etiqueta ? `${etiqueta}: ${texto}` : texto;
    })
    .join(' · ');
};

const EyeIcon = ({ open }) => (
  open ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a19.72 19.72 0 0 1 4.22-5.19" />
      <path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a19.74 19.74 0 0 1-3.17 4.19" />
      <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
);

const roles = [
  {
    title: 'Propietario',
    desc: 'Crea y administra tus fincas',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M3 11.5 12 4l9 7.5" />
        <path d="M5 10v10h14V10" />
        <path d="M10 20v-5h4v5" />
      </svg>
    ),
  },
  {
    title: 'Administrador',
    desc: 'Gestiona el equipo y potreros',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M17 20v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
        <circle cx="10" cy="7" r="3.2" />
        <path d="M21 20v-2a4 4 0 0 0-3-3.87" />
        <path d="M16.5 3.6a3.2 3.2 0 0 1 0 6.2" />
      </svg>
    ),
  },
  {
    title: 'Operario',
    desc: 'Registra mediciones y pesajes',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <line x1="4" y1="20" x2="4" y2="10" />
        <line x1="10" y1="20" x2="10" y2="4" />
        <line x1="16" y1="20" x2="16" y2="13" />
        <line x1="22" y1="20" x2="2" y2="20" />
      </svg>
    ),
  },
];

export default function Signup() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    telefono: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { saveToken } = useAuth();
  const navigate = useNavigate();

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (form.password !== form.confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register({
        username: form.username,
        email: form.email,
        telefono: form.telefono || undefined,
        password: form.password,
      });
      const response = await api.post('/auth/token/', {
        email: form.email,
        password: form.password,
      });
      await saveToken(response.data.token);
      navigate(await getInitialDestination(), { replace: true });
    } catch (err) {
      setError(errorText(err.response?.data) || 'No fue posible crear la cuenta.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <aside className="auth-landscape">
        <div className="auth-landscape-copy">
          <img src="/logo.jpeg" alt="Ganadería" />
          <div>
            <p className="auth-kicker">Primer paso · Cuenta</p>
            <h1>Empieza con tu finca.</h1>
            <p>Registra tu cuenta y crea el espacio donde tu equipo trabajará.</p>
            <div className="auth-roles">
              {roles.map((r) => (
                <div className="auth-role-card" key={r.title}>
                  {r.icon}
                  <div>
                    <strong>{r.title}</strong>
                    <span>{r.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </aside>
      <main className="auth-panel">
        <form className="auth-form auth-form-register auth-card" onSubmit={handleSubmit}>
          <div className="auth-mobile-brand"><img src="/logo.jpeg" alt="Ganadería" /></div>
          <header>
            <h2>Crea tu cuenta</h2>
            <p>Los datos de contacto se usan para las invitaciones de finca.</p>
          </header>
          {error && <p className="form-message is-error" role="alert">{error}</p>}
          <div className="form-grid">
            <label>
              Nombre de usuario
              <input
                name="username"
                required
                autoComplete="username"
                value={form.username}
                onChange={update}
                placeholder="ej. ana_ganadera"
              />
            </label>
            <label>
              Teléfono <span>opcional</span>
              <input
                name="telefono"
                type="tel"
                autoComplete="tel"
                value={form.telefono}
                onChange={update}
                placeholder="+57 300 000 0000"
              />
            </label>
          </div>
          <label>
            Correo electrónico
            <input
              name="email"
              type="email"
              autoComplete="email"
              required
              value={form.email}
              onChange={update}
              placeholder="nombre@correo.com"
            />
          </label>
          <div className="form-grid">
            <label>
              Contraseña
              <span className="auth-input-wrapper">
                <input
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  minLength="8"
                  required
                  value={form.password}
                  onChange={update}
                  placeholder="Mínimo 8 caracteres"
                />
                <button
                  type="button"
                  className="auth-input-eye"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  <EyeIcon open={showPassword} />
                </button>
              </span>
            </label>
            <label>
              Confirmar contraseña
              <span className="auth-input-wrapper">
                <input
                  name="confirmPassword"
                  type={showConfirm ? 'text' : 'password'}
                  autoComplete="new-password"
                  minLength="8"
                  required
                  value={form.confirmPassword}
                  onChange={update}
                  placeholder="Repite la contraseña"
                  aria-invalid={form.confirmPassword && form.password !== form.confirmPassword ? 'true' : undefined}
                />
                <button
                  type="button"
                  className="auth-input-eye"
                  onClick={() => setShowConfirm((v) => !v)}
                  aria-label={showConfirm ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  <EyeIcon open={showConfirm} />
                </button>
              </span>
              {form.confirmPassword && form.password !== form.confirmPassword && (
                <small className="auth-field-warning">Las contraseñas no coinciden.</small>
              )}
            </label>
          </div>
          <button className="button button-primary auth-submit" type="submit" disabled={loading}>
            {loading ? 'Creando cuenta…' : 'Crear cuenta'}
          </button>
          <p className="auth-switch">¿Ya tienes una cuenta? <Link to="/">Iniciar sesión</Link></p>
        </form>
      </main>
    </div>
  );
}
