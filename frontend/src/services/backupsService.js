import api from './api';

export const getRespaldos = (fincaId) => api.get('/backups/', { params: { finca: fincaId } });
export const generarRespaldo = (fincaId, cifrado) =>
  api.post('/backups/', { finca: fincaId, cifrado });
// El servidor exige la confirmación explícita; la pantalla ya la pidió al usuario.
export const restaurarRespaldo = (id) => api.post(`/backups/${id}/restore/`, { confirmar: true });

function nombreDeArchivo(cabecera, porOmision) {
  const encontrado = /filename="?([^";]+)"?/i.exec(cabecera || '');
  return encontrado ? encontrado[1] : porOmision;
}

// Las descargas viajan como blob, así que un error llega también como blob y
// hay que leerlo antes de poder mostrarlo.
async function mensajeDelBlob(error) {
  const datos = error?.response?.data;
  if (!(datos instanceof Blob)) return null;
  try {
    const cuerpo = JSON.parse(await datos.text());
    return cuerpo.detail || Object.values(cuerpo).flat().join(' ');
  } catch {
    return null;
  }
}

async function descargar(url, params, porOmision) {
  let respuesta;
  try {
    respuesta = await api.get(url, { params, responseType: 'blob' });
  } catch (error) {
    const mensaje = await mensajeDelBlob(error);
    throw mensaje ? new Error(mensaje) : error;
  }
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(respuesta.data);
  enlace.download = nombreDeArchivo(respuesta.headers['content-disposition'], porOmision);
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(enlace.href);
}

export const descargarRespaldo = (id) =>
  descargar(`/backups/${id}/download/`, undefined, `respaldo-${id}.json`);

export const exportarDatos = (fincaId, formato, incluir) =>
  descargar(
    '/exports/',
    { finca: fincaId, formato, incluir: incluir.join(',') },
    `export.${formato === 'json' ? 'json' : 'csv'}`,
  );
