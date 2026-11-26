import React from 'react';

// Evolución de una serie en el tiempo (peso de un bovino, por ejemplo).
// Es un SVG a mano a propósito: el proyecto no usa librería de gráficas y no
// vale la pena añadir una dependencia para una línea.
const ANCHO = 560;
const ALTO = 150;
const MARGEN = { arriba: 12, derecha: 10, abajo: 24, izquierda: 44 };

const fecha = (valor) =>
  new Date(valor).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });

export default function TrendChart({ puntos, unidad = 'kg', titulo }) {
  if (!puntos || puntos.length === 0) return null;

  const serie = [...puntos].sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
  const valores = serie.map((punto) => punto.valor);
  const maximo = Math.max(...valores);
  const minimo = Math.min(...valores);
  // Con un solo dato, o todos iguales, se deja aire para que la línea no quede
  // pegada al borde del área.
  const margenValor = maximo === minimo ? Math.max(maximo * 0.1, 1) : 0;
  const techo = maximo + margenValor;
  const piso = Math.max(minimo - margenValor, 0);

  const anchoUtil = ANCHO - MARGEN.izquierda - MARGEN.derecha;
  const altoUtil = ALTO - MARGEN.arriba - MARGEN.abajo;
  const x = (indice) =>
    MARGEN.izquierda + (serie.length === 1 ? anchoUtil / 2 : (anchoUtil * indice) / (serie.length - 1));
  const y = (valor) =>
    MARGEN.arriba + altoUtil - (altoUtil * (valor - piso)) / (techo - piso || 1);

  const coordenadas = serie.map((punto, indice) => [x(indice), y(punto.valor)]);
  const linea = coordenadas.map(([px, py]) => `${px.toFixed(1)},${py.toFixed(1)}`).join(' ');
  const area = `${MARGEN.izquierda},${MARGEN.arriba + altoUtil} ${linea} ${
    coordenadas[coordenadas.length - 1][0]
  },${MARGEN.arriba + altoUtil}`;

  const primero = serie[0];
  const ultimo = serie[serie.length - 1];
  const variacion = ultimo.valor - primero.valor;
  const resumen = `${titulo || 'Evolución'}: de ${primero.valor} a ${ultimo.valor} ${unidad} entre ${fecha(
    primero.fecha,
  )} y ${fecha(ultimo.fecha)}.`;

  return (
    <div>
      <svg
        className="trend-chart"
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        role="img"
        aria-label={resumen}
      >
        <title>{resumen}</title>
        <line
          className="trend-grid"
          x1={MARGEN.izquierda} y1={MARGEN.arriba}
          x2={MARGEN.izquierda} y2={MARGEN.arriba + altoUtil}
        />
        <line
          className="trend-grid"
          x1={MARGEN.izquierda} y1={MARGEN.arriba + altoUtil}
          x2={ANCHO - MARGEN.derecha} y2={MARGEN.arriba + altoUtil}
        />
        <text className="trend-axis" x={MARGEN.izquierda - 6} y={MARGEN.arriba + 4} textAnchor="end">
          {Math.round(techo)}
        </text>
        <text
          className="trend-axis"
          x={MARGEN.izquierda - 6} y={MARGEN.arriba + altoUtil} textAnchor="end"
        >
          {Math.round(piso)}
        </text>
        {serie.length > 1 && <polygon className="trend-area" points={area} />}
        {serie.length > 1 && <polyline className="trend-line" points={linea} />}
        {coordenadas.map(([px, py], indice) => (
          <circle key={serie[indice].id || indice} className="trend-point" cx={px} cy={py} r="3" />
        ))}
        <text className="trend-axis" x={MARGEN.izquierda} y={ALTO - 6}>
          {fecha(primero.fecha)}
        </text>
        {serie.length > 1 && (
          <text className="trend-axis" x={ANCHO - MARGEN.derecha} y={ALTO - 6} textAnchor="end">
            {fecha(ultimo.fecha)}
          </text>
        )}
      </svg>
      <div className="trend-legend">
        <span>Registros <b>{serie.length}</b></span>
        <span>Último <b>{ultimo.valor} {unidad}</b></span>
        {serie.length > 1 && (
          <span>
            Variación <b>{variacion > 0 ? '+' : ''}{variacion.toFixed(1)} {unidad}</b>
          </span>
        )}
      </div>
    </div>
  );
}
