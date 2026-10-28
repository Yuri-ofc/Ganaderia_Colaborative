import { getFincas } from './farmService';

// Debe coincidir con la clave de AuthContext para que al cargar el perfil
// se recupere exactamente la misma finca que elegimos aquí.
const CLAVE_FINCA_ACTIVA = 'fincaActivaId';

const rutaPorRol = {
  propietario: '/propietario',
  administrador: '/administracion',
  operario: '/operario',
};

function elegirDefault(fincas) {
  if (!fincas || fincas.length === 0) return null;
  return (
    fincas.find((f) => f.mi_rol === 'propietario')
    || fincas.find((f) => f.mi_rol === 'administrador')
    || fincas[0]
  );
}

export async function getInitialDestination() {
  try {
    const response = await getFincas();
    const fincas = response.data.results || response.data || [];
    if (!fincas.length) {
      // Una cuenta nueva llega a /propietario para crear su primera finca.
      localStorage.removeItem(CLAVE_FINCA_ACTIVA);
      return '/propietario';
    }

    // Si había una finca activa guardada y sigue existiendo, respétala;
    // si no, elegimos la de mayor nivel disponible.
    const guardada = localStorage.getItem(CLAVE_FINCA_ACTIVA);
    const activa = fincas.find((f) => f.id === guardada) || elegirDefault(fincas);
    if (activa) {
      localStorage.setItem(CLAVE_FINCA_ACTIVA, activa.id);
      return rutaPorRol[activa.mi_rol] || '/operario';
    }
    return '/propietario';
  } catch {
    return '/propietario';
  }
}
