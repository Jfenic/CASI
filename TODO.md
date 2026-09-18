# CASI - Histórico de Hitos

> **Trabajo activo:** Ver [TASKS.md](TASKS.md) para el backlog y prioridades actuales.  
> **Hoja de ruta:** Ver [planning.md](planning.md) para la visión de fases.  
> **Registro de cambios:** Ver [CHANGELOG.md](CHANGELOG.md).

Este archivo conserva el registro cronológico de los hitos completados en el proyecto.

---

## Hitos Completados

### Hito 6: Fiabilidad y Protocol Enforcement (Fase 12 — 2026-09-17)
- Máquina de estados `AgentPhase` para bloquear respuestas `final` sin acción mutativa en `ACTION_REQUIRED`.
- Generación de esquemas forzados `ProposeFileAction` para mutaciones CREATE.
- Fallback parser de normalización para llamadas a herramientas embebidas.
- Verificación tolerante en repositorios vacíos y contratos afinados.
- **Resultado:** 9/12 (75%) en el benchmark independiente de desarrollo con `qwen3.5:4b` ([informe](docs/reports/2026-09-17-development-phase12.md)).

### Hito 5: Rediseño de Terminal Interactiva (Terminal UX Overhaul — 2026-09-17)
- Memento de parches (`PatchMementoStack`) con comando `/undo` para rollback seguro.
- Métricas de sesión en vivo y al salir (`/stats`, `/metrics`).
- Árbol visual de pasos del agente (`├─`, `└─`), diffs colapsables y spinner.
- Resumen de fallos de Pytest y autocompletado avanzado Readline (`/comandos`, `@rutas`).

### Hito 4: Interfaz Visual y API (Fases 8 y 11 — 2026-09-14)
- API FastAPI con ciclo de vida de tareas y aprobación de parches (`casi serve`).
- Interfaz Streamlit modular (`casi ui`) con historial, trazas y revisión de diffs.

### Hito 3: Aislamiento Docker y Resiliencia (Fases 5 y 6 — 2026-09-12)
- Sandbox `DockerRunner` sin red sobre copias temporales aisladas.
- Fallback local desactivado por defecto (requiere opt-in explícito).
- Ciclo automático de corrección: propuesta → test en sandbox → retry (hasta 4 intentos).

### Hito 2: Bucle del Agente y Observabilidad (Fases 3, 4 y 9 — 2026-09-11)
- Integración con Ollama vía protocolo estructurado JSON.
- `AgentLoop` acotado con detección de repeticiones y límites de pasos.
- Trazas estructuradas v2 y métricas de ejecución agregadas.

### Hito 1: Cimientos y Acceso Seguro (Fases 0, 1 y 2 — 2026-09-08)
- Estructura del repositorio, configuración CI, Ruff y suite Pytest.
- Acceso seguro a rutas (`safe_path`, exclusión de `.git`, `.env`, secretos).
- Registro tipado de herramientas (`list_files`, `read_file`, `search_code`).
