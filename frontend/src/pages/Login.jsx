import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { getInitialDestination } from '../services/navigationService';

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

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { saveToken } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const identifier = email.trim();
      const credentials = identifier.includes('@') ? { email: identifier, password } : { username: identifier, password };
      const response = await api.post('/auth/token/', credentials);
      await saveToken(response.data.token);
      navigate(await getInitialDestination(), { replace: true });
    } catch (err) {
      const data = err.response?.data;
      const pick = (v) => (Array.isArray(v) ? v[0] : v);
      const message =
        pick(data?.detail) ||
        pick(data?.non_field_errors) ||
        pick(data?.email) ||
        pick(data?.password) ||
        'No fue posible iniciar sesión. Verifica tus datos e inténtalo de nuevo.';
      setError(String(message));
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
            <p className="auth-kicker">Gestión ganadera de precisión</p>
            <h1>Tu finca, en orden.</h1>
            <p>Organiza tu equipo y las fincas a tu cargo desde un mismo lugar.</p>
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
        <form className="auth-form auth-card" onSubmit={handleSubmit}>
          <div className="auth-mobile-brand"><img src="/logo.jpeg" alt="Ganadería" /></div>
          <header>
            <h2>Bienvenido de nuevo</h2>
            <p>Ingresa para continuar a tu espacio de trabajo.</p>
          </header>
          {error && <p className="form-message is-error" role="alert">{error}</p>}
          <label>
            Correo electrónico o usuario
            <input
              type="text"
              autoComplete="username"
              required
              placeholder="nombre@correo.com o usuario"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Contraseña
            <span className="auth-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                placeholder="Tu contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
          <label className="auth-checkbox-row">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
            />
            Recordarme en este equipo
          </label>
          <button className="button button-primary auth-submit" type="submit" disabled={loading}>
            {loading ? 'Ingresando…' : 'Ingresar'}
          </button>
          <p className="auth-switch">¿No tienes cuenta? <Link to="/registro">Crear cuenta</Link></p>
        </form>
      </main>
    </div>
  );
}
