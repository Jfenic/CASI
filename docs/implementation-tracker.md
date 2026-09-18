# Implementation Tracker

> **Trabajo activo:** [TASKS.md](../TASKS.md)  
> **Arquitectura:** [ARCHITECTURE.md](../ARCHITECTURE.md)  
> **Hoja de ruta:** [planning.md](../planning.md)

Estado rápido de los componentes y capacidades implementadas en CASI.

---

## Capacidades Implementadas

### Seguridad e Inspección
- [x] Resolución segura de repositorio y validación de rutas (`safe_path`).
- [x] Bloqueo de rutas sensibles (`.git`, `.env`, `.ssh`, claves privadas, credenciales).
- [x] Prevención de escapes vía enlaces simbólicos y path traversal (`../`).
- [x] Explorador con exclusión automática de carpetas virtuales y cachés.
- [x] Lector de archivos de texto acotado en tamaño con rangos de líneas.
- [x] Búsqueda estructurada de texto en código con rutas y números de línea.

### Herramientas y Bucle del Agente
- [x] Registro estructurado de herramientas con validación tipada y permisos (`READ`, `EXECUTE`, `MUTATE`).
- [x] `apply_patch` bloqueado de forma estricta contra llamadas directas del modelo.
- [x] Bucle de agente (`AgentLoop`) acotado en pasos y caracteres, con prevención de bucles.
- [x] Protocolo de decisiones estructuradas en JSON con cliente Ollama configurable.
- [x] Máquina de estados de fases (`AgentPhase`) que prohíbe respuestas de texto `final` sin acción mutativa.
- [x] Modo forzado `ProposeFileAction` para mutaciones de creación (`CREATE`).
- [x] Parser de recuperación tolerante ante llamadas a herramientas embebidas en respuestas `final`.

### Parches y Sandbox
- [x] Propuestas de cambio mediante diffs unificados generados con `propose_file`.
- [x] Validación estricta de parches antes de ejecución (Git check, límites de ficheros).
- [x] Ejecución de tests en sandbox Docker (`DockerRunner`) sin red sobre copias temporales aisladas.
- [x] Fallback local explícito (desactivado por defecto para repositorios no confiables).
- [x] Ciclo automático de reparación (propuesta → test en sandbox → reintento hasta 4 veces).
- [x] Aprobación humana interactiva o vía API obligatoria antes de aplicar parches reales.

### Terminal Interactiva y UX
- [x] Memento de parches (`PatchMementoStack`) con comando `/undo` para rollback seguro de cambios.
- [x] Métricas de sesión en vivo (`/stats`, `/metrics`) y resumen automático al cerrar.
- [x] Presenter con paleta semántica, árbol de pasos (`├─`, `└─`), diffs colapsables y spinner.
- [x] Resumen parseado de fallos de Pytest con trazas aisladas.
- [x] Autocompletado Readline para comandos `/` y rutas de archivo `@` con historial persistente (`~/.casi_history`).

### Interfaces y Observabilidad
- [x] CLI profesional (`casi inspect`, `run`, `ask`, `fix`, `test`, `interactive`, `serve`, `ui`).
- [x] API FastAPI (`src/casi/api/`) con ciclo de vida completo de tareas y endpoints de aprobación.
- [x] Interfaz visual Streamlit (`casi ui`) modular conectada a la API.
- [x] Trazas estructuradas de ejecución JSON v2, métricas de tokens y tiempos por paso.
- [x] Suites de benchmarks reproducibles con evaluadores independientes y pruebas de mutación.

---

## Estado Actual

- **Etapa:** Alpha avanzada (`0.1.0`), funcional para trabajo supervisado en repositorios locales.
- **Suite de pruebas:** 448 pruebas aprobadas (unitarias, integración, Docker y API).
- **Benchmark de desarrollo:** 9/12 (75%) tareas completadas de forma autónoma con `qwen3.5:4b` ([informe](reports/2026-09-17-development-phase12.md)).
- **Validación de código:** Lint y formato con Ruff sin incidencias, compilación de bytecode verificada.

---

## Próximos Pasos

Consultar [TASKS.md](../TASKS.md) para el backlog activo (persistencia de historial API/UI, respuestas a clarificaciones sobre HTTP y orquestación multi-fase futura).
