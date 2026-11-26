import api from './api';

export const getCapturas = (params) => api.get('/vision-captures/', { params });

// La captura va como multipart por el archivo: hay que soltar el
// Content-Type JSON que trae la instancia de axios para que el navegador
// ponga el boundary.
export const createCaptura = ({ bovino, tipoArchivo, archivo }) => {
  const cuerpo = new FormData();
  cuerpo.append('bovino', bovino);
  cuerpo.append('tipo_archivo', tipoArchivo);
  cuerpo.append('archivo', archivo);
  return api.post('/vision-captures/', cuerpo, { headers: { 'Content-Type': undefined } });
};
