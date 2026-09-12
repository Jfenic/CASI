# CASI - TODO

Lista priorizada de próximos pasos del proyecto.

## Estabilización (2026-09-12)

- [x] Corregir los errores Ruff y normalizar el formato del código y los tests.
- [x] Confirmar la suite completa: 319 passed, 2 skipped; Docker y API incluidos.
- [x] Unificar el contrato JSON de diagnóstico entre parser, política y evaluador.
- [x] Añadir regresiones para diagnóstico, contexto de reparación y parches CREATE.
- [x] Usar el fallo más reciente en los reintentos y recordar el contrato completo.
- [x] Medir diagnóstico con Ollama: 4/5 frente a 0/5; rúbricas sin cambios.
- [ ] Cerrar los fallos residuales de fiabilidad documentados en el [informe](docs/reports/2026-09-12-stabilization.md).
- [ ] Revisar y versionar las correcciones y los nuevos informes.

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

## Estabilización priorizada (2026-09-09)

- [x] **P0:** sincronizar dependencias y lockfile; instalar desarrollo en CI y construir la imagen Docker antes de las pruebas.
- [x] **P0:** verificar la suite completa en Python 3.11 y 3.12, incluida la API.
- [x] **P1:** resolver avisos funcionales y de formato; Ruff sin incidencias.
- [x] **P1:** ejecutar Docker y la reparación real con Ollama, exigiendo un parche que pase los tests.
- [x] **P1:** medir las 26 tareas: 24/26 correctas; [informe y reproducción](docs/reports/2026-09-09-stabilization.md).
- [x] **P2:** corregir `task_023` (punto final en iniciales), `task_007` (finalización sin parche) y pérdida de métricas de reintento, con regresiones deterministas.
- [x] **P2:** completar trazas de estrategia y permisos entre planificador, especialistas y presentador.
- [x] **P3:** revisar y publicar los cambios tras cerrar la estabilización.
- [x] **P3:** convertir fallos documentados en regresiones y mejorar fiabilidad CREATE/fix (`task_017`, `task_023`, suite de desarrollo).
- [ ] **P4:** ampliar ecosistemas y diseñar la interfaz visual.

## Prioridad inmediata

- [x] Sustituir el enrutamiento rígido por selección adaptativa de herramientas dirigida por el modelo.
- [x] Mantener el clasificador de intención como orientación para prompts y planes, no como bloqueo del conjunto de herramientas.
- [x] Permitir que el modelo solicite elevar una tarea de `READ` a `EXECUTE` o `MUTATE` cuando descubra que lo necesita.
- [x] Implementar autorización acumulada por tarea (`READ < EXECUTE < MUTATE`) para no repetir confirmaciones ya cubiertas.
- [x] Mantener `apply_patch` fuera del alcance directo del modelo y exigir validación, tests y aprobación humana.
- [x] Registrar en la traza cada cambio de estrategia, herramienta solicitada, permiso concedido o rechazado y motivo de escalada.
- [x] Añadir pruebas donde una petición inicialmente ambigua termina necesitando tests o una modificación.
- [x] Crear fixtures end-to-end reproducibles para correcciones reales con Ollama.
- [x] Cubrir recuperación ante JSON inválido, herramientas rechazadas, diffs mal formados y parches que no pasan tests.
- [x] Clasificar por separado fallos del código, dependencias, Docker, timeout y formato del modelo.
- [x] Evitar el fallback local silencioso para repositorios no confiables; exigir una decisión explícita.
- [x] Endurecer `sandbox.Dockerfile` con usuario no root y límites adicionales de procesos.
- [x] Detectar el comando de test del proyecto manteniendo Pytest como primera implementación.

## Evaluación de desarrollo y verificación

- [x] Crear una suite separada de 10 tareas con contratos de comportamiento explícitos.
- [x] Añadir pruebas independientes fuera del contexto del agente y limitar archivos editables.
- [x] Evaluar tests generados contra implementaciones correctas y cinco mutaciones por tarea.
- [x] Verificar que cada estado inicial falla y cada solución de referencia pasa.
- [x] Conservar trazas, parches, salida de verificación y resultados por capacidad.

## Calidad y seguridad

- [x] Añadir detección de repeticiones y límites de archivos leídos en el agente.
- [x] Ampliar benchmarks a 20+ tareas reproducibles con repositorios de prueba.
- [x] Corregir `git_diff` para rechazar directorios no-Git situados dentro de otro repositorio.

## CLI y evaluación

- [x] Añadir alias `casi ask` y `casi fix` sobre `casi run`.
- [x] Completar Fase 7: `--verbose`, `--save-patch`, confirmación de parches y códigos de salida.
- [x] Completar Fase 8: API FastAPI, `casi serve`, aprobación/rechazo de parches.
- [x] Generar informes de benchmark en fichero (JSON/Markdown).
- [x] Comparar resultados entre varios modelos locales (`--models`).

## Observabilidad (Fase 9)

- [x] Trazas en vivo y resumen del último intento.
- [x] Exportación JSON con redacción de argumentos sensibles.
- [x] Registrar herramientas rechazadas, pipeline automático y errores exactos de parches.
- [x] Logs estructurados por ejecución (`-v` en CLI, respuesta API con `metrics`).
- [x] Métricas agregadas de pasos, herramientas, tokens y duración.
- [x] Correlacionar una misma traza entre planificador, especialistas y presentador.

## Después de estabilizar el núcleo

- [x] Exponer API FastAPI con aprobación de parches y consulta de estado.
- [ ] Ampliar entornos de proyecto a Node.js y otros ecosistemas.
- [ ] Diseñar interfaz visual sobre la API estable.

## Orquestación multi-agente con presupuesto dinámico (idea — 2026-09-12)

Basado en el benchmark qwen3.5:4b (development 33%): los fallos principales no son
agotar pasos, sino terminar sin parche, respuestas vacías de Ollama y lógica
incorrecta. Aun así, descomponer el trabajo y ampliar pasos solo con progreso
medible podría mejorar tareas multi-archivo y ciclos inspect → fix → verify.

- [ ] **Planner multi-fase:** extender `TaskPlanner.decompose_task()` para tareas
  `fix`/`create` con fases explícitas (inspect → implement → verify → re-fix opcional),
  en lugar de un único paso por intent.
- [ ] **Workers especializados:** agentes separados por fase (Inspector,
  Implementer, Verifier) con contexto limpio por invocación.
- [ ] **Supervisor ligero:** evaluar progreso tras cada fase (tests ejecutados,
  archivos del traceback leídos, parche aplicado, tests mejorados) y decidir
  continuar, replanificar o abortar.
- [ ] **Presupuesto dinámico acotado:** conceder bonus de pasos (+N, máx. 1–2
  extensiones) solo si el supervisor confirma progreso; mantener tope global.
- [ ] **Reglas de cierre en fix:** nudge duro o handoff al Implementer si hay
  tests fallando y no hay `propose_file` tras N decisiones.
- [ ] **Reintentos Ollama:** reintentar cuando el mensaje llega vacío (thinking
  mode / protocolo JSON).
- [ ] **Validación:** probar primero en dev_003 y dev_012 antes de activar en
  todo el loop; comparar development antes/después con qwen3.5:4b.

## Cierre de cada hito

- [x] Ejecutar la suite completa de pruebas (319 passed, 2 skipped; 2026-09-12).
- [x] Ejecutar `python3 -m compileall -q src tests`.
- [x] Ejecutar `git diff --check`.
- [x] Actualizar `README.md`, `planning.md` y `docs/implementation-tracker.md`.
- [ ] Crear commits Git pequeños y descriptivos para este hito tras la revisión.
- [ ] Confirmar que el working tree queda limpio tras revisar y versionar este hito.
