# CASI - TODO

Lista priorizada de próximos pasos del proyecto.

## Completado recientemente

- [x] Bloquear `apply_patch` desde el agente y el registro de herramientas.
- [x] Implementar permisos de herramientas (`READ`, `EXECUTE`, `MUTATE`).
- [x] Confirmar `run_tests` en modo interactivo.
- [x] Añadir contexto conversacional persistente con `/clear`.
- [x] Ampliar pruebas de parches (crear, eliminar, rechazo sin cambios).
- [x] Implementar `DockerRunner` con copia temporal y red desactivada.
- [x] Añadir comando `casi test`.
- [x] Añadir cargador de benchmarks, métricas e informes básicos.
- [x] Conectar `DockerRunner` al flujo del agente para `run_tests` (fallback a local).
- [x] Implementar ciclo de corrección patch → tests → retry (máx. 2 intentos).
- [x] Mejorar flujo de clarificaciones: búsqueda automática tras aclarar y `/exit` en Q&A.
- [x] Usar directorio temporal local para pytest (`.pytest-tmp/`).
- [x] Preparar imágenes Docker cacheadas para dependencias Python y ejecutar tests posteriores sin red.
- [x] Añadir trazas de depuración exportables con errores de herramientas y validación de parches.

## Prioridad inmediata

- [ ] Exponer API FastAPI con aprobación de parches y consulta de estado.
- [ ] Construir y documentar imagen Docker `casi-sandbox:latest` para sandbox completo.
- [ ] Ampliar entornos de proyecto a Node.js y otros ecosistemas.

## Calidad y seguridad

- [ ] Endurecer imagen Docker (`USER` no root en `sandbox.Dockerfile`).
- [ ] Añadir detección de repeticiones y límites de archivos leídos en el agente.
- [ ] Ampliar benchmarks a 20+ tareas reproducibles con repositorios de prueba.
- [ ] Corregir test de integración `git_diff` en directorios no-git dentro del repo.

## CLI y evaluación

- [ ] Añadir alias `casi ask` y `casi fix` sobre `casi run`.
- [ ] Generar informes de benchmark en fichero (JSON/Markdown).
- [ ] Comparar resultados entre varios modelos locales.

## Observabilidad (Fase 9)

- [ ] Logs estructurados por ejecución.
- [ ] Métricas de pasos, herramientas y duración.
- [ ] Trazas reconstruibles de cada tarea del agente.

## Cierre de cada hito

- [x] Ejecutar la suite completa de pruebas (87 passed, 1 skipped; 2 fallos de integración por entorno).
- [x] Ejecutar `python3 -m compileall -q src tests`.
- [ ] Ejecutar `git diff --check`.
- [x] Actualizar `README.md`, `planning.md` y `docs/implementation-tracker.md`.
- [ ] Crear un commit Git pequeño y descriptivo.
- [ ] Confirmar que el working tree queda limpio.
