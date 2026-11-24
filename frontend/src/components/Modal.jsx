import React, { useEffect, useId } from 'react';

// Modal único de la aplicación (sustituye las copias locales de cada página).
// Accesible: role="dialog", aria-modal, título enlazado con aria-labelledby y
// cierre con la tecla Escape o con un clic en el fondo.
export default function Modal({ open, onClose, title, children }) {
  const tituloId = useId();

  useEffect(() => {
    if (!open) return undefined;
    const alPulsarTecla = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', alPulsarTecla);
    return () => document.removeEventListener('keydown', alPulsarTecla);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        className="relative bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-5">
          <h3 id={tituloId} className="text-lg font-semibold text-campo-900">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            &times;
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
