// Matriz de control de acceso por rol (RBAC) del sistema.
//
// Esto NO se lee del backend: es una transcripción manual de las reglas que
// hoy viven repartidas en los `serializers.py` y `views.py` de cada app
// (sobre todo en los `PermissionDenied` y en `fincas_accesibles` /
// `fincas_administradas` de `apps/common/serializers.py`). Si esas reglas
// cambian, esta matriz hay que actualizarla a mano para que siga siendo
// confiable.
//
// Estados posibles por celda:
//   'si'          -> permitido sin condiciones adicionales a su rol.
//   'no'          -> no permitido para ese rol.
//   'condicional' -> permitido, pero bajo una condición que no depende solo
//                    del rol en la finca (p. ej. ser dueño del recurso).
//   'na'          -> este eje de permiso no aplica a esta fila para esta
//                    columna (p. ej. "personal" en reglas que son 100% por
//                    finca).

export const ROLES = [
  { id: 'propietario', nombre: 'Propietario', descripcion: 'Dueño de la finca.' },
  { id: 'administrador', nombre: 'Administrador', descripcion: 'Miembro con rol administrador en la finca.' },
  { id: 'operario', nombre: 'Operario', descripcion: 'Miembro con rol operario en la finca.' },
  {
    id: 'personal',
    nombre: 'Personal (staff)',
    descripcion: 'Bandera global is_staff de Django. No depende de ninguna finca ni membresía: alguien puede ser operario en una finca y además staff a nivel sistema.',
  },
];

export const RECURSOS = [
  {
    id: 'fincas',
    nombre: 'Fincas',
    icon: 'farm',
    acciones: [
      {
        accion: 'Crear una finca nueva',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        detalle: 'Cualquier usuario activo puede crear una finca; al hacerlo se vuelve automáticamente su propietario (no hace falta pertenecer ya a ninguna).',
        referencia: 'farms/serializers.py · SerializerFinca.create',
      },
      {
        accion: 'Ver una finca (listado y detalle)',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        detalle: 'Puede verla cualquiera con una membresía activa, sea cual sea su rol, además del propietario.',
        referencia: 'common/serializers.py · fincas_accesibles',
      },
      {
        accion: 'Editar nombre o ubicación',
        estado: { propietario: 'si', administrador: 'no', operario: 'no', personal: 'na' },
        detalle: 'Exclusivo del propietario, incluso el administrador queda fuera.',
        referencia: 'farms/serializers.py · SerializerFinca.validate',
      },
      {
        accion: 'Eliminar la finca',
        estado: { propietario: 'si', administrador: 'no', operario: 'no', personal: 'na' },
        detalle: 'Solo el propietario puede eliminarla (borrado lógico).',
        referencia: 'farms/views.py · VistaFincas.perform_destroy',
      },
    ],
  },
  {
    id: 'miembros',
    nombre: 'Miembros',
    icon: 'people',
    acciones: [
      {
        accion: 'Ver la lista de miembros',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        detalle: 'El backend lo permite a quien administra la finca (propietario o administrador). La pantalla "Equipo" del frontend hoy solo está habilitada para el propietario, aunque el backend ya soportaría abrirla también al administrador.',
        referencia: 'farms/views.py · VistaMembresias.get_queryset',
      },
      {
        accion: 'Agregar un miembro como operario',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        detalle: 'Administrar miembros requiere administrar la finca; asignar el rol operario no tiene restricción extra.',
        referencia: 'farms/serializers.py · SerializerMembresia.validate',
      },
      {
        accion: 'Agregar o ascender un miembro a administrador',
        estado: { propietario: 'si', administrador: 'no', operario: 'no' },
        detalle: 'Solo el propietario puede otorgar el rol administrador; un administrador no puede crear otros administradores.',
        referencia: 'farms/serializers.py · SerializerMembresia.validate',
      },
      {
        accion: 'Retirar a un miembro operario',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        detalle: 'Cualquiera que administre la finca puede retirar operarios.',
        referencia: 'farms/views.py · VistaMembresias.perform_destroy',
      },
      {
        accion: 'Retirar a un miembro administrador',
        estado: { propietario: 'si', administrador: 'no', operario: 'no' },
        detalle: 'Solo el propietario puede retirar a otro administrador.',
        referencia: 'farms/views.py · VistaMembresias.perform_destroy',
      },
    ],
  },
  {
    id: 'invitaciones',
    nombre: 'Invitaciones',
    icon: 'mail',
    acciones: [
      {
        accion: 'Ver invitaciones de la finca',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'farms/views.py · VistaInvitaciones.get_queryset',
      },
      {
        accion: 'Invitar a alguien como operario',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'farms/serializers.py · SerializerInvitacion.validate',
      },
      {
        accion: 'Invitar a alguien como administrador',
        estado: { propietario: 'si', administrador: 'no', operario: 'no' },
        detalle: 'Igual que al asignar el rol directamente: invitar a un administrador es exclusivo del propietario.',
        referencia: 'farms/serializers.py · SerializerInvitacion.validate',
      },
      {
        accion: 'Cancelar una invitación pendiente de administrador',
        estado: { propietario: 'si', administrador: 'no', operario: 'no' },
        referencia: 'farms/views.py · VistaInvitaciones.perform_destroy',
      },
      {
        accion: 'Aceptar una invitación recibida',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        detalle: 'La acepta quien fue invitado (validado por su teléfono), sin importar qué rol tenga en otras fincas.',
        referencia: 'farms/views.py · VistaInvitaciones.aceptar',
      },
    ],
  },
  {
    id: 'potreros',
    nombre: 'Potreros / lotes',
    icon: 'farm',
    acciones: [
      {
        accion: 'Ver los potreros de la finca',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        referencia: 'cattle/views.py · VistaPotreros.get_queryset',
      },
      {
        accion: 'Crear o editar un potrero',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'cattle/serializers.py · SerializerPotrero.validate',
      },
      {
        accion: 'Eliminar un potrero (sin bovinos activos)',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'cattle/views.py · VistaPotreros.perform_destroy',
      },
    ],
  },
  {
    id: 'bovinos',
    nombre: 'Bovinos',
    icon: 'cattle',
    acciones: [
      {
        accion: 'Ver bovinos de la finca',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        referencia: 'cattle/views.py · VistaBovinos.get_queryset',
      },
      {
        accion: 'Registrar un bovino nuevo',
        estado: { propietario: 'si', administrador: 'si', operario: 'si' },
        detalle: 'RF-06: cualquier miembro de la finca puede dar de alta un bovino.',
        referencia: 'cattle/serializers.py · SerializerBovino.validate',
      },
      {
        accion: 'Editar los datos de un bovino existente',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        detalle: 'RF-09: el operario solo puede crear bovinos, no editarlos una vez guardados.',
        referencia: 'cattle/serializers.py · SerializerBovino.validate',
      },
      {
        accion: 'Aprobar un perfil pendiente',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'cattle/views.py · VistaBovinos.aprobar_perfil',
      },
      {
        accion: 'Dar de baja (vendido / muerto / retirado)',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'cattle/views.py · VistaBovinos.desactivar',
      },
      {
        accion: 'Mover un bovino de potrero (lote)',
        estado: { propietario: 'si', administrador: 'no', operario: 'no' },
        detalle: 'RF-10: la única acción operativa sobre bovinos que es exclusiva del propietario; ni el administrador puede moverlo de potrero.',
        referencia: 'cattle/serializers.py · SerializerMovimientoPotrero.validate',
      },
    ],
  },
  {
    id: 'mediciones',
    nombre: 'Mediciones y pesajes',
    icon: 'cattle',
    acciones: [
      {
        accion: 'Ver mediciones y pesajes',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        referencia: 'measurements/views.py · VistaMediciones / VistaPesajes',
      },
      {
        accion: 'Registrar una medición (IA) o un pesaje',
        estado: { propietario: 'si', administrador: 'si', operario: 'si' },
        referencia: 'measurements/serializers.py · SerializerMedicion / SerializerPesaje',
      },
      {
        accion: 'Editar o eliminar una medición ya guardada',
        estado: { propietario: 'no', administrador: 'no', operario: 'no', personal: 'na' },
        detalle: 'Son registros históricos inmutables para todos los roles, incluido el propietario: para corregir un valor se crea una medición nueva que referencia a la anterior (campo "corrige"), nunca se edita la original.',
        referencia: 'common/serializers.py · SerializerSoloCreacion',
      },
    ],
  },
  {
    id: 'dispositivos',
    nombre: 'Dispositivos',
    icon: 'grid',
    acciones: [
      {
        accion: 'Ver, crear o editar sus propios dispositivos',
        estado: { propietario: 'condicional', administrador: 'condicional', operario: 'condicional', personal: 'na' },
        detalle: 'No depende del rol en ninguna finca: cada usuario solo puede ver y administrar los dispositivos de los que él mismo es propietario (campo "propietario" del dispositivo).',
        referencia: 'measurements/serializers.py · SerializerDispositivo.validate',
      },
    ],
  },
  {
    id: 'sincronizacion',
    nombre: 'Sincronización',
    icon: 'grid',
    acciones: [
      {
        accion: 'Ver o enviar cambios de sincronización',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'na' },
        referencia: 'sync/views.py · VistaCambiosSincronizacion.get_queryset',
      },
      {
        accion: 'Confirmar (acknowledge) un cambio sincronizado',
        estado: { propietario: 'condicional', administrador: 'condicional', operario: 'condicional', personal: 'na' },
        detalle: 'Depende de ser el propietario del dispositivo que generó el cambio, no del rol en la finca: un operario dueño de su dispositivo puede confirmarlo y un propietario de la finca sin ese dispositivo no puede.',
        referencia: 'sync/views.py · VistaCambiosSincronizacion.confirmar',
      },
    ],
  },
  {
    id: 'respaldos',
    nombre: 'Respaldos',
    icon: 'grid',
    acciones: [
      {
        accion: 'Ver los respaldos de una finca',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'backups/views.py · VistaRespaldos.get_queryset',
      },
      {
        accion: 'Crear un respaldo',
        estado: { propietario: 'si', administrador: 'si', operario: 'no' },
        referencia: 'backups/serializers.py · SerializerRespaldo.validate',
      },
    ],
  },
  {
    id: 'catalogos',
    nombre: 'Catálogos (razas, tipos de medida, modelos IA)',
    icon: 'grid',
    acciones: [
      {
        accion: 'Ver el catálogo',
        estado: { propietario: 'si', administrador: 'si', operario: 'si', personal: 'si' },
        detalle: 'La lectura está abierta a cualquier usuario autenticado y activo; no depende de ninguna finca.',
        referencia: 'common/views.py · MixinEscrituraPersonal',
      },
      {
        accion: 'Crear, editar o eliminar un elemento del catálogo',
        estado: { propietario: 'no', administrador: 'no', operario: 'no', personal: 'si' },
        detalle: 'Esto es completamente independiente del rol en cualquier finca: se exige is_staff de Django. Un propietario o administrador que además sea staff sí puede, pero por ser staff, no por su rol en la finca.',
        referencia: 'common/serializers.py · exigir_personal',
      },
    ],
  },
];
