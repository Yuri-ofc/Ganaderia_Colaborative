# Evidencias del ciclo de mantenimiento — v1.1.0

Repositorio: <https://github.com/Yuri-ofc/Ganaderia_Colaborative>
Integrantes (autoría de los commits repartida a partes iguales): **Vicenz111** y **Yuri-ofc**.

## Resumen del entregable

| Requisito | Evidencia |
| --- | --- |
| Cinco deudas técnicas identificadas | 10 deudas (DT-01 a DT-10) en [`docs/DEUDA_TECNICA.md`](DEUDA_TECNICA.md) |
| Tres issues | [#8](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/8) bug, [#9](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/9) mejora, [#10](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/10) bug, [#11](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/11), [#12](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/12) y [#16](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/16) deuda técnica |
| Uso de ramas | `main`, `fix/login-token-vencido`, `fix/invitaciones-zona-horaria`, `feature/modal-reutilizable`, `docs/documentacion-proyecto` |
| Dos cambios reales | Tres implementados: #8, #9 y #10 |
| Commits descriptivos | Convención `tipo: descripción` (ver abajo y `CONTRIBUTING.md`) |
| Pull Requests | #13, #14, #15 (cambios), #17 (documentación) y #7 (línea base) |
| Tag de versión | `v1.1.0` (y `v1.0.0` como línea base) |
| Versión actual | **v1.1.0** |
| README, CONTRIBUTING, CHANGELOG | En la raíz del repositorio |
| Trazabilidad completa de dos cambios | Sección «Trazabilidad» |
| Reflexión final | Sección «Reflexión final» |

## Parte 2 — Issues

| # | Tipo | Título | Prioridad | Responsable | Estado |
| --- | --- | --- | --- | --- | --- |
| [#8](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/8) | Bug | El login devuelve un token vencido | Alta | Vicenz111 | Cerrado por el PR #13 |
| [#9](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/9) | Mejora (DT-01) | Modal reutilizable y accesible | Media | Yuri-ofc | Cerrado por el PR #15 |
| [#10](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/10) | Bug | La expiración por defecto de la invitación queda desplazada por UTC | Media | Yuri-ofc | Cerrado por el PR #14 |
| [#11](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/11) | Deuda técnica (DT-02) | Valores por defecto inseguros en `settings.py` | Crítica | Vicenz111 | Abierto |
| [#12](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/12) | Deuda técnica (DT-03) | El frontend no tiene pruebas ni linter | Alta | Yuri-ofc | Abierto |
| [#16](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/16) | Deuda técnica (DT-09) | Documentación desactualizada y sin guías de contribución | Media | Vicenz111 | Cerrado por el PR #17 |

Cada issue incluye descripción, prioridad, responsable y criterio de cierre.

## Parte 3 y 5 — Ramas y commits

```
*   Merge pull request #15 from feature/modal-reutilizable
|\
| * refactor: reemplazar los modales duplicados por el componente Modal compartido   (Vicenz111)
| * feat: agregar componente Modal accesible y reutilizable                         (Yuri-ofc)
|/
*   Merge pull request #14 from fix/invitaciones-zona-horaria
|\
| * fix: usar hora local en la expiración por defecto de invitaciones               (Vicenz111)
|/
*   Merge pull request #13 from fix/login-token-vencido
|\
| * test: cubrir la renovación de token vencido en el login                         (Yuri-ofc)
| * fix: renovar el token vencido al iniciar sesión                                 (Vicenz111)
|/
*   Merge pull request #7 from sexto-commit            ← línea base v1.0.0
```

Los commits de la línea base (PR #7) se separaron por tema: RBAC (backend y frontend), landing y documentación.

## Parte 7 — Versión

Se define **v1.1.0**.

| Componente | ¿Se incrementa? | Justificación |
| --- | --- | --- |
| MAJOR | No | No hay cambios incompatibles: la API y los datos no cambian de contrato. |
| **MINOR** | **Sí** | Se agregó funcionalidad compatible hacia atrás: el componente `Modal` accesible (cierre con Escape, ARIA, scroll). |
| PATCH | Queda en 0 | Las dos correcciones (#8 y #10) por sí solas habrían sido PATCH, pero al incluir una funcionalidad nueva la versión sube de MINOR y se reinicia PATCH. |

El tag `v1.0.0` marca la línea base previa y `v1.1.0` se crea sobre `main` una vez integrado el PR #17 (documentación).

## Parte 10 — Trazabilidad (dos cambios)

### Cambio 1 — Bug: el login devolvía un token vencido

| Etapa | Evidencia |
| --- | --- |
| **Issue** | [#8](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/8) — «Bug: el login devuelve un token vencido» |
| **Problema** | `VistaInicioSesion` usaba `get_or_create` y devolvía el token viejo pasados los 30 días; la primera petición respondía 401. |
| **Rama** | `fix/login-token-vencido` |
| **Commits** | `75a2928` `fix: renovar el token vencido al iniciar sesión` · `da96cb8` `test: cubrir la renovación de token vencido en el login` |
| **Pull Request** | [#13](https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/13) (`Closes #8`) |
| **Integración** | Merge commit `5877282` en `main`; el issue #8 se cerró automáticamente |
| **Versión** | v1.1.0 (sección «Corregido» del `CHANGELOG.md`) |
| **Evidencia** | Sin el fix, la prueba nueva falla con `AssertionError: '7470619b…' == '7470619b…'` (mismo token). Con el fix: 15 tests OK en `accounts` y 110 OK en la suite completa. |

### Cambio 2 — Mejora: Modal reutilizable y accesible (DT-01)

| Etapa | Evidencia |
| --- | --- |
| **Issue** | [#9](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/9) — «Mejora: modal reutilizable y accesible» |
| **Problema** | El `Modal` estaba copiado 4 veces, sin `role="dialog"`, sin cierre con Escape y sin altura máxima en 3 de las 4 copias. |
| **Rama** | `feature/modal-reutilizable` |
| **Commits** | `663e905` `feat: agregar componente Modal accesible y reutilizable` · `6ba474c` `refactor: reemplazar los modales duplicados por el componente Modal compartido` |
| **Pull Request** | [#15](https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/15) (`Closes #9`) |
| **Integración** | Merge commit `839b8e3` en `main`; el issue #9 se cerró automáticamente |
| **Versión** | v1.1.0 (sección «Agregado» y «Cambiado» del `CHANGELOG.md`) |
| **Evidencia** | `npm run build` correcto; 64 líneas duplicadas eliminadas; prueba del componente en Chromium con el CSS real: 12 de 12 comprobaciones correctas (Escape, clic en el fondo, botón ×, ARIA, scroll con altura máxima 90vh). |

El tercer cambio (#10, PR [#14](https://github.com/Yuri-ofc/Ganaderia_Colaborative/pull/14), commit `c4778e4`) también sigue la cadena completa: a las 22:30 hora de Colombia, la fecha sugerida pasaba de `2026-12-02T03:30` (incorrecta) a `2026-12-01T22:30`.

## Parte 11 — Estado actual del software

**Versión actual:** v1.1.0.

**Funcionalidades principales**
- Gestión de fincas, potreros y bovinos con roles de propietario, administrador y operario.
- Invitaciones a fincas, membresías y control de acceso (RBAC) con etiquetas y opciones de menú editables.
- Mediciones morfométricas y pesajes inmutables; borrado lógico con historial.
- Autenticación por token con caducidad y límites de intentos.
- Landing pública en `/inicio`.

**Principales cambios realizados:** línea base v1.0.0 integrada por temas; renovación de tokens vencidos (#8); Modal accesible único (#9); fecha de expiración en hora local (#10); documentación completa (README, CONTRIBUTING, CHANGELOG, plantillas, `docs/`; #16, PR #17).

**Errores pendientes**
- Cualquier error al cargar el perfil cierra la sesión, incluso un fallo de red transitorio (`AuthContext.jsx:104`).
- Al aceptar una invitación se muestra el UUID interno de la finca en vez de su nombre (`Invitaciones.jsx`, mensaje de aceptación).
- Cuando falla la carga de razas o de fincas, la pantalla queda vacía sin mensaje de error (`Bovinos.jsx:73`, `Fincas.jsx:103`).

**Mejoras pendientes**
- Proteger los roles y recursos del sistema en el panel RBAC y evitar la autoedición de roles (DT-04).
- Envolver en una transacción la reasignación de roles de un usuario (`rbac/views.py`: borra y recrea sin `atomic`).
- Reducir consultas N+1 en el listado de fincas y de usuarios (DT-05).
- Pruebas de `VistaBuscarUsuario` y de integridad de consultas.

**Deudas técnicas identificadas:** 10 (DT-01 a DT-10).
**Deudas técnicas corregidas:** 2 — DT-01 (Modal duplicado) y DT-09 (documentación). Pendientes: DT-02 ([#11](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/11)), DT-03 ([#12](https://github.com/Yuri-ofc/Ganaderia_Colaborative/issues/12)), DT-04, DT-05, DT-06, DT-07, DT-08 y DT-10.

## Parte 12 — Reflexión final

**1. ¿Cuál es actualmente la principal deuda técnica?**
La configuración insegura por defecto (DT-02): si falta el `.env`, el sistema arranca con `DEBUG=True`, una clave de desarrollo conocida y CORS abierto a cualquier origen.

**2. ¿Qué riesgo representa no corregirla?**
Un despliegue con un `.env` ausente o mal copiado quedaría expuesto: trazas de error con datos internos, sesiones y tokens firmados con una clave pública y peticiones desde cualquier origen. Es el riesgo con mayor impacto y por eso tiene prioridad crítica.

**3. ¿Qué tipo de mantenimiento realizaron?**
Correctivo (los dos errores de token y de zona horaria), perfectivo (el Modal accesible) y preventivo (reducción de código duplicado, pruebas de regresión y documentación). No se hizo mantenimiento adaptativo, porque no cambió el entorno.

**4. ¿Qué ventajas encontraron al trabajar con ramas?**
Cada cambio quedó aislado: se probó y se revisó por separado sin mezclar temas, `main` se mantuvo estable y revertir un cambio concreto es posible sin tocar los demás. También permitió repartir el trabajo entre los dos integrantes sin pisarse.

**5. ¿Qué utilidad tuvieron los issues?**
Dejaron por escrito qué se iba a corregir, con prioridad, responsable y criterio de cierre, de modo que se supo cuándo estaba terminado. Los que siguen abiertos (#11 y #12) son la lista de trabajo pendiente, y el `Closes #N` cerró los issues automáticamente al integrar.

**6. ¿Cómo ayudan los commits a comprender la evolución del software?**
Con mensajes como `fix: renovar el token vencido al iniciar sesión` el historial se lee como una bitácora: qué cambió, de qué tipo y por qué. Comparado con mensajes como `sexto-commit` o `quinto commit` de la historia anterior, que no permiten saber qué se modificó sin abrir el diff.

**7. ¿Qué utilidad tienen los tags y las versiones?**
Marcan puntos estables y reproducibles: `v1.0.0` es la línea base y `v1.1.0` incluye las correcciones. Permiten volver a un estado conocido, comunicar qué cambió (el `CHANGELOG.md`) y saber, por el número, si una actualización trae funcionalidad nueva (MINOR), solo arreglos (PATCH) o rupturas (MAJOR).

**8. ¿Qué podría suceder si varios desarrolladores modificaran el proyecto sin control de versiones?**
Se sobrescribirían los cambios de los demás, no habría forma de saber quién cambió qué ni de deshacer un error, y no existiría una versión estable de referencia. En este proyecto ya se vio una versión de ese problema: el trabajo de tres temas acumulado sin commitear en un mismo árbol de trabajo.

**9. ¿Consideran que otro desarrollador podría continuar trabajando fácilmente sobre su proyecto?**
En buena medida sí: el README explica instalación y ejecución, `CONTRIBUTING.md` fija el flujo, hay 110 pruebas de backend, el historial es descriptivo y los issues abiertos indican qué sigue. La limitación es el frontend, que no tiene pruebas ni linter (DT-03) y tiene componentes de más de 400 líneas (DT-08), lo que hace más arriesgado modificarlo.

**10. ¿Qué aspecto debería ser el siguiente en mantenerse o mejorarse?**
Primero DT-02 (configuración segura por defecto, issue #11) por su riesgo, y a continuación DT-03 (pruebas y linter del frontend, issue #12), porque sin ellas cada refactor posterior es más riesgoso.
