/*
 * Landing de Ganadería de Precisión.
 *
 * Estructura inspirada en la plantilla gratuita "Namari" de ShapingRain
 * (https://onepagelove.com/namari): cabecera pegajosa sobre un hero con
 * parallax, bloque de iconos, galería con lightbox, banda parallax, bloque de
 * "testimonios", rejilla de confianza y tres bloques de contratación.
 * No se copian textos, imágenes, código ni marca de la plantilla: todo el
 * contenido sale de los módulos y la documentación reales del sistema.
 *
 * Regla del proyecto: sin cifras comerciales, clientes, testimonios, premios
 * ni precios inventados.
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getInitialDestination } from '../services/navigationService';
import '../styles/landing.css';

/* ---------- Iconos lineales (mismo trazo que el resto de la app) ---------- */
const Svg = ({ children, size = 26 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {children}
  </svg>
);

const IconFinca = () => (
  <Svg>
    <path d="M3 11.5 12 4l9 7.5" />
    <path d="M5 10v10h14V10" />
    <path d="M10 20v-5h4v5" />
  </Svg>
);
const IconHato = () => (
  <Svg>
    <path d="M4 9.5c0-1.4 1.1-2.5 2.5-2.5h9c1.9 0 3.5 1.6 3.5 3.5V15" />
    <path d="M4 9.5V16" />
    <path d="M7 16v4M17 15v5M4 16h16" />
    <path d="M20 10.5 22 9" />
    <path d="M9 7 8 4M13 7l1-3" />
  </Svg>
);
const IconMedida = () => (
  <Svg>
    <path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" />
    <circle cx="12" cy="12" r="3.2" />
  </Svg>
);
const IconOffline = () => (
  <Svg>
    <path d="M12 3v11" />
    <path d="m8 10 4 4 4-4" />
    <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
  </Svg>
);
const IconHistorial = () => (
  <Svg>
    <path d="M3 12a9 9 0 1 0 3-6.7" />
    <path d="M3 4v4h4" />
    <path d="M12 8v4l3 2" />
  </Svg>
);
const IconInmutable = () => (
  <Svg>
    <rect x="5" y="11" width="14" height="9" rx="2" />
    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
  </Svg>
);
const IconFinca2 = () => (
  <Svg>
    <path d="M12 3 4 6v6c0 4.5 3.2 7.8 8 9 4.8-1.2 8-4.5 8-9V6l-8-3Z" />
    <path d="m9 12 2 2 4-4" />
  </Svg>
);
const IconCheck = () => (
  <Svg size={16}>
    <path d="m5 12.5 4.5 4.5L19 7.5" />
  </Svg>
);
const IconArrow = () => (
  <Svg size={16}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Svg>
);

/* ---------- Contenido ---------- */
const NAV = [
  { href: '#inicio', label: 'Inicio' },
  { href: '#producto', label: 'Producto' },
  { href: '#galeria', label: 'Galería' },
  { href: '#roles', label: 'Roles' },
  { href: '#seguridad', label: 'Seguridad' },
  { href: '#acceso', label: 'Acceso' },
];

const FUNCIONES = [
  {
    icon: <IconFinca />,
    title: 'Fincas y equipo',
    text: 'Crea tus fincas, invita a administradores y operarios y define qué puede hacer cada persona.',
  },
  {
    icon: <IconHato />,
    title: 'Hato y potreros',
    text: 'Registra cada bovino con su arete, raza, sexo y categoría, y sigue sus movimientos entre potreros.',
  },
  {
    icon: <IconMedida />,
    title: 'Mediciones y pesajes',
    text: 'Guarda el peso estimado por visión artificial con su intervalo de confianza y compáralo con la báscula.',
    estado: 'Módulo en preparación',
  },
  {
    icon: <IconOffline />,
    title: 'Offline y respaldos',
    text: 'Trabaja sin señal en el potrero: los cambios se sincronizan por dispositivo y los respaldos se verifican.',
    estado: 'Módulo en preparación',
  },
];

/*
 * Galería: recortes de la ilustración propia del proyecto (fondo-clean.jpg,
 * 1376×768). Cada tile muestra una zona distinta del paisaje.
 * cx, cy = centro del recorte (0–1); z = zoom.
 */
const IMG_RATIO = 768 / 1376;
const TILE_RATIO = 3 / 4; // alto / ancho de cada tile
const clamp = (n) => Math.min(100, Math.max(0, n));
const recorte = ({ cx, cy, z }) => {
  const zr = z * IMG_RATIO;
  const px = clamp(((cx * z - 0.5) / (z - 1)) * 100);
  const py = clamp(((cy * zr - TILE_RATIO / 2) / (zr - TILE_RATIO)) * 100);
  return {
    backgroundImage: 'url(/fondo-clean.jpg)',
    backgroundSize: `${z * 100}% auto`,
    backgroundPosition: `${px}% ${py}%`,
  };
};

const GALERIA = [
  { title: 'Ganado en pastoreo', caption: 'Cada animal, identificado en su potrero', cx: 0.22, cy: 0.8, z: 2.5 },
  { title: 'El casco de la finca', caption: 'Donde empieza y termina la jornada', cx: 0.7, cy: 0.5, z: 3.4 },
  { title: 'El camino al potrero', caption: 'Los movimientos del hato, registrados', cx: 0.6, cy: 0.62, z: 2.4 },
  { title: 'La arboleda', caption: 'Sombra, descanso y lotes bien definidos', cx: 0.1, cy: 0.42, z: 3 },
  { title: 'Potrero de pasto seco', caption: 'Pesajes y mediciones por lote', cx: 0.84, cy: 0.76, z: 2.5 },
  { title: 'Amanecer en el campo', caption: 'Tu finca, en orden desde temprano', cx: 0.5, cy: 0.36, z: 1.6 },
];

const ROLES = [
  {
    id: 'propietario',
    name: 'Propietario',
    lema: 'Quien crea la finca y decide quién entra.',
    puede: [
      'Crear, renombrar y eliminar sus fincas',
      'Asignar o retirar administradores',
      'Invitar a su equipo y ver todo el hato',
      'Consultar respaldos y mediciones',
    ],
  },
  {
    id: 'administrador',
    name: 'Administrador',
    lema: 'Quien mantiene el campo funcionando día a día.',
    puede: [
      'Gestionar potreros y operarios de su finca',
      'Revisar el hato y los movimientos',
      'Administrar los respaldos de la finca',
      'Ver el panel de administración',
    ],
  },
  {
    id: 'operario',
    name: 'Operario',
    lema: 'Quien está en el potrero con el celular en la mano.',
    puede: [
      'Consultar la finca asignada',
      'Registrar bovinos y movimientos',
      'Capturar mediciones y pesajes',
      'Enviar cambios desde el dispositivo',
    ],
  },
];

const GARANTIAS = [
  {
    icon: <IconOffline />,
    title: 'Sin señal, sin problema',
    text: 'Los cambios hechos en el campo se guardan en el dispositivo y se sincronizan al volver la conexión.',
  },
  {
    icon: <IconHistorial />,
    title: 'Historial que se conserva',
    text: 'Fincas, potreros, bovinos y miembros se desactivan sin perder su historia: nada se borra de verdad.',
  },
  {
    icon: <IconInmutable />,
    title: 'Mediciones inalterables',
    text: 'Una medición no se edita: si hay un error, se registra una corrección nueva que apunta a la anterior.',
  },
  {
    icon: <IconFinca2 />,
    title: 'Cada finca, solo para los suyos',
    text: 'Cada persona ve únicamente las fincas a las que pertenece, según el rol que tiene en cada una.',
  },
];

/* ---------- Hooks de comportamiento ---------- */
function useScrollEffects(heroRef, bandRef) {
  const [solid, setSolid] = useState(false);
  const [active, setActive] = useState('#inicio');

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let raf = 0;

    const tick = () => {
      raf = 0;
      const y = window.scrollY;
      setSolid(y > 40);
      if (reduce) return;
      if (heroRef.current && y < window.innerHeight * 1.2) {
        heroRef.current.style.transform = `translate3d(0, ${Math.round(y * 0.3)}px, 0)`;
      }
      const band = bandRef.current;
      if (band && band.parentElement) {
        const r = band.parentElement.getBoundingClientRect();
        if (r.bottom > 0 && r.top < window.innerHeight) {
          const offset = (r.top + r.height / 2 - window.innerHeight / 2) * -0.18;
          band.style.transform = `translate3d(0, ${Math.round(offset)}px, 0)`;
        }
      }
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(tick);
    };
    tick();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);

    // Enlace activo en la navegación
    const ids = NAV.map((n) => n.href.slice(1));
    const secciones = ids.map((id) => document.getElementById(id)).filter(Boolean);
    const spy = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(`#${e.target.id}`);
        });
      },
      { rootMargin: '-45% 0px -50% 0px' }
    );
    secciones.forEach((s) => spy.observe(s));

    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (raf) cancelAnimationFrame(raf);
      spy.disconnect();
    };
  }, [heroRef, bandRef]);

  return { solid, active };
}

// Entrada de cada bloque al llegar a pantalla. Sin JS el contenido ya es visible.
function useReveal(rootRef) {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return undefined;
    const items = root.querySelectorAll('[data-reveal]');
    if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      items.forEach((el) => el.classList.add('is-in'));
      return undefined;
    }
    root.classList.add('landing-anim');
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('is-in');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -6% 0px' }
    );
    items.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [rootRef]);
}

/* ---------- Lightbox ---------- */
function Lightbox({ index, onClose, onMove }) {
  const closeRef = useRef(null);

  useEffect(() => {
    const prev = document.activeElement;
    closeRef.current?.focus();
    document.body.style.overflow = 'hidden';
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') onMove(1);
      if (e.key === 'ArrowLeft') onMove(-1);
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
      prev?.focus?.();
    };
  }, [onClose, onMove]);

  const item = GALERIA[index];
  return (
    <div className="landing-lightbox" role="dialog" aria-modal="true" aria-label={item.title} onClick={onClose}>
      <figure onClick={(e) => e.stopPropagation()}>
        <div className="landing-lightbox-img" style={recorte(item)} role="img" aria-label={item.title} />
        <figcaption>
          <strong>{item.title}</strong>
          <span>{item.caption}</span>
        </figcaption>
      </figure>
      <button type="button" className="landing-lb-btn landing-lb-prev" onClick={(e) => { e.stopPropagation(); onMove(-1); }} aria-label="Imagen anterior">‹</button>
      <button type="button" className="landing-lb-btn landing-lb-next" onClick={(e) => { e.stopPropagation(); onMove(1); }} aria-label="Imagen siguiente">›</button>
      <button ref={closeRef} type="button" className="landing-lb-btn landing-lb-close" onClick={onClose} aria-label="Cerrar">×</button>
    </div>
  );
}

/* ---------- Página ---------- */
export default function Landing() {
  const rootRef = useRef(null);
  const heroRef = useRef(null);
  const bandRef = useRef(null);
  const { solid, active } = useScrollEffects(heroRef, bandRef);
  useReveal(rootRef);

  const [menuOpen, setMenuOpen] = useState(false);
  const [lightbox, setLightbox] = useState(null);
  const [rolActivo, setRolActivo] = useState(ROLES[0].id);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const anterior = document.title;
    document.title = 'Ganadería de Precisión · Gestión ganadera para tu finca';
    return () => { document.title = anterior; };
  }, []);

  const irAlPanel = useCallback(async (e) => {
    e.preventDefault();
    navigate(await getInitialDestination(), { replace: false });
  }, [navigate]);

  const moverLightbox = useCallback((d) => {
    setLightbox((i) => (i === null ? i : (i + d + GALERIA.length) % GALERIA.length));
  }, []);
  const cerrarLightbox = useCallback(() => setLightbox(null), []);

  const rol = ROLES.find((r) => r.id === rolActivo);

  // CTA principal: si ya hay sesión lleva al panel, si no al login (ruta "/").
  const cta = isAuthenticated
    ? { to: '/', label: 'Entrar a mi panel', onClick: irAlPanel }
    : { to: '/', label: 'Iniciar sesión' };

  return (
    <div className="landing" ref={rootRef}>
      <div className="landing-frame" aria-hidden="true" />

      <header className={`landing-header${solid ? ' is-solid' : ''}${menuOpen ? ' is-open' : ''}`}>
        <div className="landing-header-inner">
          <a href="#inicio" className="landing-brand" aria-label="Ganadería de Precisión, inicio">
            <img src="/logo.jpeg" alt="" />
            <span>Ganadería<small>de precisión</small></span>
          </a>
          <nav id="landing-nav" aria-label="Secciones" className="landing-nav">
            <ul>
              {NAV.map((n) => (
                <li key={n.href}>
                  <a href={n.href} className={active === n.href ? 'is-active' : ''} aria-current={active === n.href ? 'true' : undefined} onClick={() => setMenuOpen(false)}>
                    {n.label}
                  </a>
                </li>
              ))}
            </ul>
            <Link to={cta.to} onClick={cta.onClick} className="landing-btn landing-btn-small landing-nav-cta">{cta.label}</Link>
          </nav>
          <button
            type="button"
            className="landing-burger"
            aria-expanded={menuOpen}
            aria-controls="landing-nav"
            aria-label={menuOpen ? 'Cerrar menú' : 'Abrir menú'}
            onClick={() => setMenuOpen((o) => !o)}
          >
            <span />
          </button>
        </div>
      </header>

      <main>
        {/* ---- Banner / hero ---- */}
        <section id="inicio" className="landing-hero">
          <div className="landing-hero-bg" ref={heroRef} aria-hidden="true" />
          <div className="landing-hero-content">
            <h1 className="landing-rise" style={{ '--d': '80ms' }}>Gestión ganadera de precisión</h1>
            <p className="landing-lead landing-rise" style={{ '--d': '180ms' }}>
              Registra tu hato, organiza tu equipo y lleva el peso de cada animal, incluso en el potrero sin señal.
            </p>
            <div className="landing-actions landing-rise" style={{ '--d': '280ms' }}>
              <Link to={cta.to} onClick={cta.onClick} className="landing-btn">{cta.label}</Link>
              <Link to="/registro" className="landing-btn landing-btn-ghost">Crear una cuenta</Link>
            </div>
          </div>
        </section>

        {/* ---- Producto (Namari: "About" con cuatro bloques de icono) ---- */}
        <section id="producto" className="landing-section">
          <div className="landing-row">
            <div className="landing-col-third" data-reveal>
              <div className="landing-heading">
                <h2>Tu hato, bajo control</h2>
                <p className="landing-sub">
                  Para tu finca: todo lo que ocurre en el potrero queda registrado, quién es cada animal, dónde está y cuánto pesa.
                </p>
              </div>
            </div>
            <div className="landing-col-twothirds landing-blocks">
              {FUNCIONES.map((f, i) => (
                <article className="landing-block" key={f.title} data-reveal style={{ '--d': `${i * 90}ms` }}>
                  <div className="landing-icon">{f.icon}</div>
                  <div>
                    <h3>{f.title}</h3>
                    <p>{f.text}</p>
                    {f.estado && <span className="landing-tag">{f.estado}</span>}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ---- Galería con lightbox ---- */}
        <section id="galeria" className="landing-section landing-section-tint">
          <div className="landing-row">
            <div className="landing-heading landing-heading-center" data-reveal>
              <h2>El campo que gestionas</h2>
            </div>
          </div>
          <div className="landing-row">
            <ul className="landing-gallery">
              {GALERIA.map((g, i) => (
                <li key={g.title} data-reveal style={{ '--d': `${(i % 3) * 80}ms` }}>
                  <button type="button" onClick={() => setLightbox(i)} aria-label={`Ampliar: ${g.title}`}>
                    <span className="landing-tile" style={recorte(g)} />
                    <span className="landing-tile-cap">
                      <strong>{g.title}</strong>
                      <span>{g.caption}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* ---- Banda parallax (Namari: "Believing" + vídeo) ---- */}
        <section className="landing-band" aria-labelledby="landing-band-title">
          <div className="landing-band-bg" ref={bandRef} aria-hidden="true" />
          <div className="landing-row landing-band-row">
            <div className="landing-band-copy" data-reveal>
              <h2 id="landing-band-title">Del arete al historial completo</h2>
              <p>
                Cada animal, identificado. Cada pesaje, guardado. Los movimientos entre potreros, las mediciones
                morfométricas y los pesajes quedan ligados al mismo bovino, para decidir con datos y no de memoria.
              </p>
              <a href="#roles" className="landing-btn landing-btn-gold">Ver quién hace qué <IconArrow /></a>
            </div>
            <img className="landing-band-logo" src="/logo.jpeg" alt="Logotipo de Ganadería: tres cabezas de ganado bajo un sombrero" data-reveal style={{ '--d': '120ms' }} />
          </div>
        </section>

        {/* ---- Roles (Namari: "Testimonials") ---- */}
        <section id="roles" className="landing-section landing-section-tint">
          <div className="landing-row">
            <div className="landing-col-third" data-reveal>
              <div className="landing-heading">
                <h2>Un permiso para cada rol</h2>
                <p className="landing-sub">
                  El sistema separa lo que puede hacer el propietario, el administrador y el operario en cada finca.
                </p>
              </div>
            </div>
            <div className="landing-col-twothirds" data-reveal style={{ '--d': '100ms' }}>
              <div className="landing-roles">
                <div className="landing-roles-tabs" role="tablist" aria-label="Roles de la finca">
                  {ROLES.map((r) => (
                    <button
                      key={r.id}
                      role="tab"
                      type="button"
                      id={`tab-${r.id}`}
                      aria-selected={rolActivo === r.id}
                      aria-controls={`panel-${r.id}`}
                      tabIndex={rolActivo === r.id ? 0 : -1}
                      className={rolActivo === r.id ? 'is-on' : ''}
                      onClick={() => setRolActivo(r.id)}
                      onKeyDown={(e) => {
                        const i = ROLES.findIndex((x) => x.id === rolActivo);
                        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); const n = ROLES[(i + 1) % ROLES.length].id; setRolActivo(n); document.getElementById(`tab-${n}`)?.focus(); }
                        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); const n = ROLES[(i - 1 + ROLES.length) % ROLES.length].id; setRolActivo(n); document.getElementById(`tab-${n}`)?.focus(); }
                      }}
                    >
                      {r.name}
                    </button>
                  ))}
                </div>
                <div className="landing-roles-panel" role="tabpanel" id={`panel-${rol.id}`} aria-labelledby={`tab-${rol.id}`} key={rol.id}>
                  <p className="landing-quote">{rol.lema}</p>
                  <ul>
                    {rol.puede.map((p) => (
                      <li key={p}><IconCheck /> {p}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ---- Seguridad (Namari: "Clients") ---- */}
        <section id="seguridad" className="landing-section">
          <div className="landing-row">
            <div className="landing-col-third" data-reveal>
              <div className="landing-heading">
                <h2>Datos seguros, con o sin señal</h2>
              </div>
            </div>
            <div className="landing-col-twothirds landing-trust">
              {GARANTIAS.map((g, i) => (
                <article key={g.title} data-reveal style={{ '--d': `${i * 80}ms` }}>
                  <div className="landing-icon landing-icon-sm">{g.icon}</div>
                  <h3>{g.title}</h3>
                  <p>{g.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ---- Acceso (Namari: "Pricing") ---- */}
        <section id="acceso" className="landing-section landing-access">
          <div className="landing-row">
            <div className="landing-heading landing-heading-center" data-reveal>
              <h2>Entra por la puerta que te corresponde</h2>
            </div>
          </div>
          <div className="landing-row">
            <div className="landing-paths">
              <article className="landing-path" data-reveal>
                <h3>Ya tengo cuenta</h3>
                <p className="landing-path-sub">Vuelve a tu espacio de trabajo</p>
                <p>Retoma tus fincas, tu hato y tus registros donde los dejaste.</p>
                <Link to={cta.to} onClick={cta.onClick} className="landing-btn landing-btn-outline">{cta.label}</Link>
              </article>
              <article className="landing-path is-featured" data-reveal style={{ '--d': '90ms' }}>
                <h3>Soy propietario</h3>
                <p className="landing-path-sub">Crea tu cuenta y tu primera finca</p>
                <p>Registra tus potreros y tu hato, e invita a tu equipo cuando estés listo.</p>
                <Link to="/registro" className="landing-btn landing-btn-gold">Crear mi cuenta <IconArrow /></Link>
              </article>
              <article className="landing-path" data-reveal style={{ '--d': '180ms' }}>
                <h3>Me invitaron</h3>
                <p className="landing-path-sub">Únete a la finca de tu equipo</p>
                <p>Crea tu cuenta, abre Invitaciones y canjea el código que te enviaron.</p>
                <Link to="/registro" className="landing-btn landing-btn-outline">Crear cuenta</Link>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="landing-row landing-footer-row">
          <a href="#inicio" className="landing-brand landing-brand-foot" aria-label="Volver al inicio">
            <img src="/logo.jpeg" alt="" />
            <span>Ganadería<small>de precisión</small></span>
          </a>
          <ul className="landing-footer-nav">
            {NAV.slice(1).map((n) => (
              <li key={n.href}><a href={n.href}>{n.label}</a></li>
            ))}
            <li><Link to="/">Iniciar sesión</Link></li>
            <li><Link to="/registro">Crear cuenta</Link></li>
          </ul>
        </div>
        <p className="landing-footer-copy">
          © 2026 Ganadería de Precisión. Estructura de página inspirada en la plantilla gratuita Namari (ShapingRain).
        </p>
      </footer>

      {lightbox !== null && <Lightbox index={lightbox} onClose={cerrarLightbox} onMove={moverLightbox} />}
    </div>
  );
}
