# Bitácora de mejora: landing principal

Fecha: 2026-10-30

## Solicitud en curso

Crear una landing principal responsive para el sistema de gestión ganadera, inspirada estructural y estéticamente en la plantilla gratuita **MNTN Landing Page** de Kryston Schwarze, pero adaptada al producto y al lenguaje visual ya presentes en el proyecto. La landing debe incluir un acceso visible y funcional al login, sin modificar las pantallas de autenticación ni las páginas de contenido existentes.

## Revisión realizada

### Stack y rutas

- El frontend está desarrollado con React 18, Vite, React Router y Tailwind CSS.
- La aplicación inicia actualmente en `frontend/src/App.jsx`, con `/` apuntando a `Login.jsx`.
- El login se encuentra en `/` y el registro en `/registro`.
- Para conservar el login sin cambios, la landing se añadirá como una página nueva y se conectará con una ruta propia (previsiblemente `/inicio`), y el botón principal llevará a `/`.
- No se han realizado cambios de código funcional en las rutas ni componentes durante esta fase de análisis.

### Lenguaje visual existente

Se revisaron `frontend/src/pages/Login.jsx`, `frontend/src/styles/tailwind.css`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/Icon.jsx` y `frontend/tailwind.config.js`.

- Tipografía principal: `DM Sans`.
- Paleta dominante: verdes bosque/campo, con variables como `--forest-950: #102817`, `--forest-800: #285334`, `--forest-100: #e7f0e5`, fondo `--frame: #edf3eb` y texto `--ink: #183020`.
- Estilo: superficies claras, botones verdes sólidos, bordes y radios discretos, iconos lineales, jerarquía tipográfica limpia y módulos de interfaz sobrios.
- Activos disponibles: `frontend/public/fondo-clean.jpg` (paisaje) y `frontend/public/logo.jpeg`.
- El login establece como mensajes de marca «Gestión ganadera de precisión» y «Tu finca, en orden».

### Fuentes de contenido

No se localizaron los dos PDF ni `resumenProyecto.txt` solicitados en el repositorio. Por tanto, se aplicará la alternativa autorizada en el encargo: una landing estándar de producto, con contenido sustentado en los módulos y la documentación existentes.

Fuentes revisadas:

- `README.md`
- `sistema.md`
- Estructura de aplicaciones y páginas del frontend

Información de producto confirmada:

- Gestión de fincas, miembros, invitaciones y roles.
- Registro y consulta de bovinos, potreros y movimientos.
- Mediciones morfométricas y pesajes; el backend contempla estimaciones basadas en visión artificial.
- Uso offline, sincronización por dispositivo, respaldos verificables y permisos por rol.
- Audiencias principales: propietario, administrador y operario.

No se utilizarán cifras comerciales, testimonios, clientes, premios ni promesas no verificadas.

## Referencia MNTN y licencia

El enlace de Figma no pudo abrirse de forma automática por las restricciones de robots de Figma. La búsqueda de referencias confirmó que la plantilla corresponde a **MNTN Landing Page**, creada por **Kryston Schwarze**, disponible como recurso comunitario y referenciada con licencia **CC BY 4.0** en implementaciones derivadas.

La adaptación prevista toma únicamente principios generales de composición de la plantilla: navegación ligera sobre un hero visual, narrativa vertical, bloques editoriales y llamadas a la acción. No se copiarán textos, imágenes, marcas ni recursos propios de MNTN. El crédito a la inspiración y a la autora se añadirá en el comentario inicial del archivo de landing.

## Dirección de diseño elegida

Se generó y seleccionó la dirección «One motif» para respetar el sistema visual existente sin reproducir la plantilla literalmente.

- Idea: el **arete de identificación bovina** se convierte en el motivo de la landing. Aparece como una gran forma geométrica recortada en el hero, como detalle en los controles y como hilo conductor en secciones posteriores.
- Composición: hero de gran escala, navegación contenida, bloques narrativos alternados y secciones con jerarquía visual marcada en lugar de una cuadrícula genérica de tarjetas.
- Colores y tipografía: se mantienen la paleta verde y DM Sans del proyecto.
- Interacción prevista: navegación a secciones, CTA de acceso al login, y controles o elementos que hagan visible el recorrido de gestión de la finca sin simular datos de producción.
- Movimiento previsto: transiciones sutiles de entrada y una apertura de imagen tipo «shutter», siempre con alternativa para `prefers-reduced-motion`.

## Próximos pasos

1. Crear `frontend/src/pages/Landing.jsx` con contenido basado en los módulos reales del sistema.
2. Añadir los estilos de landing en `frontend/src/styles/tailwind.css`, aislados bajo el prefijo `landing-` para no afectar el login ni el dashboard.
3. Añadir la ruta de la landing y mantener el login en su ruta actual.
4. Usar únicamente activos del proyecto y una representación de interfaz en HTML/CSS cuando sea útil; no incorporar dependencias nuevas.
5. Compilar el frontend y comprobar el comportamiento responsive en escritorio, tableta y móvil.

## Estado del repositorio

El árbol de trabajo ya contenía cambios locales en múltiples archivos de backend y frontend antes de iniciar esta tarea. Esos cambios no se tocarán como parte de la landing.

