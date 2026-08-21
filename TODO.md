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

## Prioridad inmediata

- [ ] Conectar `DockerRunner` al flujo del agente para `run_tests` en producción.
- [ ] Implementar ciclo de corrección patch → tests → retry (máx. 2 intentos).
- [ ] Exponer API FastAPI con aprobación de parches y consulta de estado.

## Calidad y seguridad

- [ ] Endurecer imagen Docker (`USER` no root en `sandbox.Dockerfile`).
- [ ] Añadir detección de repeticiones y límites de archivos leídos en el agente.
- [ ] Ampliar benchmarks a 20+ tareas reproducibles con repositorios de prueba.

## CLI y evaluación

- [ ] Añadir alias `casi ask` y `casi fix` sobre `casi run`.
- [ ] Generar informes de benchmark en fichero (JSON/Markdown).
- [ ] Comparar resultados entre varios modelos locales.

## Cierre de cada hito

- [ ] Ejecutar la suite completa de pruebas.
- [ ] Ejecutar `python3 -m compileall -q src tests`.
- [ ] Ejecutar `git diff --check`.
- [ ] Actualizar `README.md`, `planning.md` y `docs/implementation-tracker.md`.
- [ ] Crear un commit Git pequeño y descriptivo.
- [ ] Confirmar que el working tree queda limpio.
