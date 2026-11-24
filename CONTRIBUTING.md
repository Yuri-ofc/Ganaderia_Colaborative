# Guía de contribución

Gracias por colaborar. Esta guía fija cómo se trabaja en el repositorio para que cada cambio sea trazable: **issue → rama → commit → Pull Request → integración → versión**.

## Flujo de trabajo

1. **Busque o cree un issue** que describa el problema o la mejora (con prioridad, responsable y criterio de cierre). Hay plantillas en `.github/ISSUE_TEMPLATE/`.
2. **Cree una rama** desde `main` actualizado.
3. **Haga commits pequeños y descriptivos** (ver convención abajo).
4. **Pruebe** su cambio.
5. **Abra un Pull Request** hacia `main` que cierre el issue (`Closes #N`).
6. Tras la revisión, se **integra con merge commit** y se borra la rama.
7. Los cambios acumulados se agrupan en una **versión** con su tag (ver Versionado).

## Nombres de ramas

| Rama | Uso | Ejemplo |
| --- | --- | --- |
| `main` | Código estable e integrado. **No se hace push directo**: solo llega por Pull Request. | — |
| `feature/<tema>` | Funcionalidad nueva o mejora | `feature/modal-reutilizable` |
| `fix/<tema>` | Corrección de un error | `fix/login-token-vencido` |
| `refactor/<tema>` | Reducción de deuda técnica sin cambiar el comportamiento | `refactor/utilidad-errores-api` |
| `docs/<tema>` | Solo documentación | `docs/documentacion-proyecto` |

Reglas: minúsculas, palabras separadas por guiones, nombre corto que describa el cambio y **una rama por issue**.

## Convención de commits

Formato: `tipo: descripción en minúscula y en imperativo` (opcionalmente `tipo(alcance): ...`).

| Tipo | Cuándo |
| --- | --- |
| `feat` | Funcionalidad nueva |
| `fix` | Corrección de un error |
| `refactor` | Cambio interno sin alterar el comportamiento |
| `test` | Agregar o corregir pruebas |
| `docs` | Documentación |
| `chore` | Mantenimiento (dependencias, configuración) |

**Buenos ejemplos**

```
feat: agregar filtro por fecha
fix: renovar el token vencido al iniciar sesión
refactor: reemplazar los modales duplicados por el componente Modal compartido
```

**No se aceptan** mensajes vagos como `cambios`, `final`, `arreglo`, `ahora-si`, `commit` o `sexto-commit`. El mensaje debe explicar *qué* cambió y, en el cuerpo, *por qué*. Referencie el issue con `Refs #N` o `Closes #N`.

## Pull Requests

Cada PR debe incluir (hay plantilla en `.github/PULL_REQUEST_TEMPLATE.md`):

- **Descripción** del problema.
- **Issue relacionado** (`Closes #N`).
- **Explicación del cambio**: qué archivos y por qué.
- **Instrucciones para verificarlo**: comandos o pasos manuales.
- **Evidencia** cuando haga falta: salida de pruebas, capturas o comparaciones antes/después.

Antes de pedir revisión compruebe que:

- `cd backend && python manage.py test` pasa completo.
- `cd frontend && npm run build` compila sin errores.
- No se incluyen secretos, archivos `.env`, bases de datos ni binarios sueltos.
- El PR toca solo lo que el issue pide.

## Reglas básicas

- **Nunca** suba credenciales, tokens ni contraseñas: use variables de entorno (`.env` no se versiona; documente la variable en `.env.example`).
- **No reescriba la historia** de ramas compartidas ni use `git push --force`.
- Todo error corregido debe llevar una **prueba** que falle sin el arreglo.
- Mantenga el código, los modelos y las claves de la API en **español**, como el resto del proyecto.
- Si una migración cambia el esquema, súbala en el mismo PR y verifique `python manage.py makemigrations --check --dry-run`.
- Discuta en el issue los cambios grandes antes de implementarlos.

## Versionado

Se usa [Versionado Semántico](https://semver.org/lang/es/) `MAJOR.MINOR.PATCH`:

- **MAJOR**: cambios incompatibles (por ejemplo, romper la API).
- **MINOR**: funcionalidad nueva compatible hacia atrás.
- **PATCH**: solo correcciones de errores compatibles.

Cada versión se registra en [`CHANGELOG.md`](CHANGELOG.md) y se marca con un tag anotado sobre `main`:

```bash
git tag -a v1.1.0 -m "v1.1.0: descripción breve"
git push origin v1.1.0
```

## Entorno de desarrollo

Las instrucciones de instalación y ejecución están en el [README](README.md).
