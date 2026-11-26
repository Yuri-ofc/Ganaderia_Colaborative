// Traduce la respuesta de error de DRF a una frase legible.
// El backend responde o `{"detail": "..."}` o `{"campo": ["..."]}`; sin esto
// cada pantalla acaba repitiendo el mismo recorrido del objeto.
export function mensajeDeError(err, respaldo = 'No se pudo completar la operación.') {
  const datos = err?.response?.data;
  if (!datos) return respaldo;
  if (typeof datos === 'string') return datos;
  if (datos.detail) return datos.detail;
  const partes = Object.values(datos)
    .flat()
    .filter((valor) => typeof valor === 'string');
  return partes.length ? partes.join(' ') : respaldo;
}

// Lista paginada o lista simple: las vistas del API usan ambas formas.
export function filasDe(respuesta) {
  return respuesta?.data?.results || respuesta?.data || [];
}
