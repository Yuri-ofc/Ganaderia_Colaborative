import React from 'react';

const paths = {
  grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
  farm: <><path d="M3 20h18" /><path d="M5 20v-7l7-5 7 5v7" /><path d="M9 20v-4h6v4" /><path d="M17 6V3" /></>,
  people: <><circle cx="9" cy="8" r="3" /><path d="M3.5 20v-1.5a5.5 5.5 0 0 1 11 0V20" /><path d="M16 5.2a3 3 0 0 1 0 5.6" /><path d="M18.5 20v-1.5a5.5 5.5 0 0 0-3-4.9" /></>,
  mail: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></>,
  logout: <><path d="M10 5H5v14h5" /><path d="m14 8 4 4-4 4" /><path d="M18 12H9" /></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  pin: <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></>,
  arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  search: <><circle cx="11" cy="11" r="6" /><path d="m16 16 4 4" /></>,
  edit: <><path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z" /><path d="m13.5 8.5 3 3" /></>,
  trash: <><path d="M4 7h16M10 11v5m4-5v5M9 7l1-3h4l1 3M6 7l1 14h10l1-14" /></>,
  chevron: <path d="m8 10 4 4 4-4" />,
  cattle: <><path d="M12 3c-2.5 0-4 2-4 4" /><path d="M12 3c2.5 0 4 2 4 4" /><circle cx="12" cy="13" r="7" /><circle cx="9.5" cy="12" r=".6" fill="currentColor" stroke="none" /><circle cx="14.5" cy="12" r=".6" fill="currentColor" stroke="none" /><path d="M10 16h4" /></>,
  shield: <><path d="M12 3 5 6v6c0 5 3 8.5 7 9 4-.5 7-4 7-9V6l-7-3Z" /><path d="m9 12 2 2 4-4" /></>,
  check: <path d="M5 12l4 4 10-10" />,
  dash: <path d="M5 12h14" />,
  alert: <><path d="M12 3 2 20h20L12 3Z" /><path d="M12 10v4" /><circle cx="12" cy="17" r=".6" fill="currentColor" stroke="none" /></>,
};

export default function Icon({ name, className = 'icon', title }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden={!title} role={title ? 'img' : undefined}>
      {title && <title>{title}</title>}
      {paths[name] || paths.grid}
    </svg>
  );
}
