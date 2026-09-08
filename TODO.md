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

- [x] Sustituir el enrutamiento rígido por selección adaptativa de herramientas dirigida por el modelo.
- [x] Mantener el clasificador de intención como orientación para prompts y planes, no como bloqueo del conjunto de herramientas.
- [x] Permitir que el modelo solicite elevar una tarea de `READ` a `EXECUTE` o `MUTATE` cuando descubra que lo necesita.
- [x] Implementar autorización acumulada por tarea (`READ < EXECUTE < MUTATE`) para no repetir confirmaciones ya cubiertas.
- [x] Mantener `apply_patch` fuera del alcance directo del modelo y exigir validación, tests y aprobación humana.
- [ ] Registrar en la traza cada cambio de estrategia, herramienta solicitada, permiso concedido o rechazado y motivo de escalada.
- [ ] Añadir pruebas donde una petición inicialmente ambigua termina necesitando tests o una modificación.
- [x] Crear fixtures end-to-end reproducibles para correcciones reales con Ollama.
- [ ] Cubrir recuperación ante JSON inválido, herramientas rechazadas, diffs mal formados y parches que no pasan tests.
- [x] Clasificar por separado fallos del código, dependencias, Docker, timeout y formato del modelo.
- [x] Evitar el fallback local silencioso para repositorios no confiables; exigir una decisión explícita.
- [x] Endurecer `sandbox.Dockerfile` con usuario no root y límites adicionales de procesos.
- [x] Detectar el comando de test del proyecto manteniendo Pytest como primera implementación.

## Calidad y seguridad

- [ ] Añadir detección de repeticiones y límites de archivos leídos en el agente.
- [ ] Ampliar benchmarks a 20+ tareas reproducibles con repositorios de prueba.
- [x] Corregir `git_diff` para rechazar directorios no-Git situados dentro de otro repositorio.

## CLI y evaluación

- [x] Añadir alias `casi ask` y `casi fix` sobre `casi run`.
- [x] Completar Fase 7: `--verbose`, `--save-patch`, confirmación de parches y códigos de salida.
- [x] Completar Fase 8: API FastAPI, `casi serve`, aprobación/rechazo de parches.
- [ ] Generar informes de benchmark en fichero (JSON/Markdown).
- [ ] Comparar resultados entre varios modelos locales.

## Observabilidad (Fase 9)

- [x] Trazas en vivo y resumen del último intento.
- [x] Exportación JSON con redacción de argumentos sensibles.
- [x] Registrar herramientas rechazadas, pipeline automático y errores exactos de parches.
- [ ] Logs estructurados por ejecución.
- [ ] Métricas agregadas de pasos, herramientas, reintentos y duración.
- [ ] Correlacionar una misma traza entre planificador, especialistas y presentador.

## Después de estabilizar el núcleo

- [x] Exponer API FastAPI con aprobación de parches y consulta de estado.
- [ ] Ampliar entornos de proyecto a Node.js y otros ecosistemas.
- [ ] Diseñar interfaz visual sobre la API estable.

## Cierre de cada hito

- [x] Ejecutar la suite completa de pruebas (211 passed, 2 skipped).
- [x] Ejecutar `python3 -m compileall -q src tests`.
- [x] Ejecutar `git diff --check`.
- [x] Actualizar `README.md`, `planning.md` y `docs/implementation-tracker.md`.
- [x] Crear commits Git pequeños y descriptivos.
- [x] Confirmar que el working tree queda limpio antes de iniciar el siguiente cambio.
