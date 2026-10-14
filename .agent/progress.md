# Current Progress

## Direction

Advanced Coding Agent Architecture (CASI v2)
Reference: [docs/features/advanced-agent/spec.md](docs/features/advanced-agent/spec.md) and [docs/features/advanced-agent/plan.md](docs/features/advanced-agent/plan.md).

## State: Features Completed & Validated

### CASI v2 — Phase 2: Isolated Worktree & Multi-File Patching (Completed: 2026-10-14)
- **Worktree Management (`src/casi/workspace/worktree.py`):**
  - Implemented `WorktreeManager` and `WorktreeSession` managing ephemeral git worktrees under `.casi/worktrees/<task_id>`.
  - Non-git fallback and detached HEAD handling with full directory isolation.
  - Multi-file staging, batch mutations, and patch applications without touching the user's working tree.
  - Safe path traversal, task ID validation, and sensitive path filtering (`.env`, `.git`, etc.).
  - Robust crash recovery: automatic pruning and cleanup of stale worktrees and orphan `casi/wt-*` branches.
  - Ephemeral vs. user branch preservation: cleanup never deletes pre-existing user branches.
  - Multi-file unified diff generation against base commits with accurate trailing newline indicators (`\ No newline at end of file`) compatible with `git apply`.
  - Interactive terminal review integration (`[y/N/v/save/?]`) and mandatory approval gate for applying to main repository.
  - Seamless Docker runner integration (`DockerRunner.run_in_worktree` and `DockerTestRunner`).
  - 31 unit tests in `tests/unit/test_worktree.py` including live Docker container execution.

### CASI v2 — Phase 1: Model Provider Abstraction & OpenAI Support (Completed: 2026-10-14)
- Abstract `ModelProvider` protocol (`src/casi/llm/providers/base.py`).
- OpenAI provider (`src/casi/llm/providers/openai.py`) with native `tool_calls`.
- Ollama provider (`src/casi/llm/providers/ollama.py`) preserving structured JSON schema mode for local models.
- Configuration via `casi.toml` and CLI flags (`--provider`, `--model`).
- Comprehensive unit tests in `tests/unit/test_providers.py`, `test_openai_client.py`, `test_config.py`.

### Prior Work: Multi-Agent Orchestration & Error Sanitization (Completed: 2026-09-29)
All 5 phases of the Multi-Agent Orchestration feature and the Error Sanitization / Context Bounding feature have been successfully implemented, linted, formatted, and verified.
 
### Summary of Accomplishments

1. **Error Sanitization, Context Bounding & Permissive JSON (`test_failures.py`, `nudges.py`, `conversation.py`, `ollama_client.py`, `parser.py`):**
   - Configurable error length conditions (`max_error_output_chars: 1500`, `max_message_chars: 6000`).
   - Strategy-based truncation (`tail`, `head_tail`, `head`, `auto`, `summary`) that preserves critical assertion diffs and test summary blocks while removing hundreds of lines of noise.
   - Enabled permissive control characters (`strict=False`) in JSON parser across `parser.py`, `actions.py`, `diagnosis.py`, `ollama_client.py` to allow literal newlines in LLM code proposals.
   - Development benchmark score on `qwen3.5:4b` increased from 5/12 to **11/12 (91.67%)** (`dev_003`, `dev_008`, and `dev_010` recovered).

2. **Anti-Overfitting & Early Test Action Guidance (`pipelines.py`, `profiles.py`):**
   - Palanca 1: Added explicit guidance in FIX pipeline to verify contract types and edge cases beyond visible repo tests.
   - Palanca 3: Added structured test engineering guidance in CREATE pipeline to act early with comprehensive assertions (`dev_002`, `dev_004`, `dev_009` recovered).

3. **Closed Catalog of 7 Personalities (`src/casi/agent/profiles.py`):**
   - Implemented `explain` with mandatory 5-section technical structure (`Propósito General`, `Componentes Clave`, `Dependencias e Interacciones`, `Flujo de Datos y Ejecución`, `Puntos Clave para el Proyecto`).
   - Implemented `test_engineer`, `refactor`, and `security` profiles with strict least-privilege tool boundaries.
   - Added `AgentProfile.with_instructions()` and `with_personality()` for non-destructive dynamic plan injection.
   - Verified via `tests/unit/test_profiles.py`.

4. **Typed Intents & Permissions (`src/casi/agent/intent.py`, `permissions.py`, `pipelines.py`):**
   - Added `TaskIntent.EXPLAIN`, `TEST_ENGINEER`, `REFACTOR`, `SECURITY`.
   - Bounded tool execution per role; read-only roles cannot mutate files or apply patches.

5. **LLM Task Evaluator (`src/casi/agent/evaluator.py`):**
   - Implemented `LLMTaskEvaluator` and `TaskEvaluation` to analyze user tasks against the closed catalog without fragile regex patterns.
   - Added deterministic fallback for test doubles / mock clients.
   - Verified via `tests/unit/test_evaluator.py`.

6. **Factory & Orchestrator Integration (`planner.py`, `factory.py`, `orchestrator.py`):**
   - Wired dynamic plan generation into `TaskPlanner.create_plan` with evaluator.
   - Passed plan instructions and specialized roles to `AgentFactory.create`.
   - Fixed mock signature compatibility in `tests/unit/test_cli.py`.

7. **Terminal UX & Commands (`interactive.py`, `cli.py`, `completion.py`, `cli_help.py`):**
   - Added `/explain <path>` command to interactive session and readline completion.
   - Wired `casi ask` to default to `explain` category.
   - Fixed Ruff formatting, line lengths, and import issues across all touched modules.
   - All linters, formatters, compileall, and 515 unit tests passing cleanly.

## Next Backlog Priority

According to [TASKS.md](TASKS.md): **API & UI Persistence & Hardening** (storage for tasks/traces across restarts, clarification answers over HTTP, end-to-end UI verification).

## Demo LinkedIn preparada — 2026-09-29

- Proyecto independiente creado en `../casi-cart-demo` (FastAPI, HTML y cálculo Python).
- Fallo deliberado de descuento: dos artículos de 50 €, descuento 20 %, total inicial 90 €.
- Verificación local: 3 tests pasan y 1 falla; una copia temporal corregida pasa los 4.
- Guion de grabación y backlog trasladado como hoja de trabajo en `docs/` de la demo.
- Funciones de endpoints y existencia del HTML comprobadas. La comprobación HTTP con
  TestClient no terminó; no se ha validado visualmente en navegador ni ejecutado todavía
  el flujo completo de CASI + Ollama + Docker. No se ha aplicado la solución a la demo.
- Las tareas de persistencia, aclaraciones y orquestación futura siguen pendientes.

## Corrección de reintentos FIX y aislamiento de contexto — 2026-09-30

- El agente orquestado usa el contrato refinado por el evaluador sin concatenar
  peticiones e instrucciones de planes anteriores. El evaluador conserva acceso
  al historial para resolver solicitudes como «Corrige el error».
- Las respuestas a aclaraciones amplían el contrato de la tarea activa.
- Tras una verificación fallida, las correcciones usan `ProposeFileAction` cuando
  el cliente lo admite, con indicaciones para conservar las validaciones existentes.
- Dos decisiones consecutivas con errores del modelo detienen el bucle y conservan
  la última verificación fallida para diagnóstico; una decisión válida reinicia
  ese contador. Ollama mantiene sus reintentos internos existentes.
- Cuatro regresiones deterministas pasan: descuento con rechazo de booleanos,
  errores persistentes del modelo, recuperación e instrucciones antiguas aisladas.
- Validación completa: lint, formato y compilación pasan; `pytest -ra` termina con
  536 tests pasando, 2 omitidos y 2 avisos de dependencias (Starlette/AnyIO).
- Pendiente repetir la demo con Ollama real y Docker; no se ha modificado la demo.

## Diagnóstico general de correcciones fallidas — 2026-09-30

- Los perfiles de mutación ejecutan la preparación y los tests iniciales aunque
  el contrato refinado no contenga palabras reconocidas por los patrones de texto.
- Los reintentos estructurados reciben los archivos originales, la última propuesta
  rechazada, el fallo actual y los errores posteriores de `propose_file`. Las
  propuestas anteriores permanecen en la traza, sin acumularse en el prompt.
- Pytest incluye los valores locales del fallo (`--showlocals`). Los mensajes
  detectan excepciones esperadas que no se produjeron antes de truncar la salida.
- Se retiraron las pistas específicas sobre booleanos y orden de cálculo. El
  experimento de sustitución de texto se descartó por indicación del usuario.
- Validación de la versión general: 538 tests pasan, 2 omitidos y 2 avisos de
  dependencias; lint, formato y compilación correctos.
- La reproducción con `qwen2.5-coder:7b` y Docker sobre una copia temporal sigue
  fallando: el modelo pierde validaciones y campos del resultado tras cuatro
  correcciones. No se considera resuelta la capacidad del modelo en este caso.
- Artefactos de esa reproducción: `/tmp/casi-cart-real-n0s0n9ua/`. La demo original
  conserva su contenido. Se detienen los ajustes específicos a petición del usuario.

## Auditoría de instrucciones generalistas — 2026-09-30

- Informe: [2026-09-30-generalist-audit.md](../docs/reports/2026-09-30-generalist-audit.md).
- Se identificaron recetas de copia, TTL y excepciones en el prompt global,
  convenciones ML, supuestos causales en nudges y ampliación del alcance de fixes.
- Se comprobaron rutas incorrectas del clasificador determinista, lecturas con
  rangos que no se contabilizan y pérdida de argumentos de tests al adaptar a Docker.
- También se revisaron restricciones prematuras de herramientas y supuestos de
  estructura del repositorio. No se ha modificado código de ejecución ni benchmarks.
- Solo se ejecutaron comprobaciones locales de funciones para respaldar el informe;
  no se repitió la suite ni se hicieron ajustes del modelo.

## Corrección de reglas específicas y heurísticas — 2026-09-30

- Se eliminaron las recetas de copia profunda, TTL y excepciones del prompt
  global, y las convenciones numéricas y de mutabilidad impuestas por el perfil ML.
- Los nudges describen evidencia sin atribuir causas no verificadas; respetan el
  alcance solicitado y los permisos de los roles de solo lectura.
- El fallback no asigna ML por palabras ambiguas. La búsqueda sigue disponible
  después de inspeccionar archivos y solo se redirigen consultas idénticas previas.
- Las llamadas ejecutadas conservan argumentos y resultado estructurados para
  contabilizar lecturas con rangos y distinguirlas de llamadas solo descritas.
- La preparación descubre README existentes, tests según configuración de Pytest,
  raíces de código e imports relativos. No ordena crear módulos desconocidos sin
  que la tarea nombre un archivo local ausente.
- Docker conserva argumentos de tests y adapta rutas absolutas del repositorio.
- Regresiones y validación completa: 561 tests pasan, 2 omitidos y 2 avisos de
  Starlette/AnyIO. Ruff, formato, compileall y comprobación del diff correctos.
- Informe actualizado: `docs/reports/2026-09-30-generalist-audit.md`. Sin cambios
  en benchmarks ni nueva medición con Ollama; la capacidad del modelo para la demo
  sigue sin considerarse resuelta.

## Iniciativa CASI v2: Agente de Programación Avanzado — 2026-10-14

- Especificación arquitectónica documentada en [docs/features/advanced-agent/spec.md](docs/features/advanced-agent/spec.md).
- Plan de implementación estructurado en 6 fases registrado en [docs/features/advanced-agent/plan.md](docs/features/advanced-agent/plan.md).
- Backlog actualizado en [TASKS.md](TASKS.md).
- Definición de fases:
  1. Abstracción de proveedores (`ModelProvider`, OpenAI con `tool_calls` nativo + Ollama).
  2. Aislamiento con `git worktree` y soporte de mutación multifichero con diff unificado.
  3. Búsqueda y comprensión semántica de código (`ripgrep` + AST de símbolos).
  4. Terminal de diagnóstico aislada en contenedor Docker efímero con comandos permitidos.
  5. Memoria persistente en SQLite y gestor de contexto (cubre la persistencia pendiente de API/UI).
  6. Ecosistema ampliable (cliente MCP, búsqueda/documentación web y puente VS Code).
- Todo el suite de pruebas actual verificado y pasando limpiamente (561 tests).

## Fase 1 Completada: Abstracción de Proveedores y Soporte OpenAI — 2026-10-14

- Implementación del protocolo `ModelProvider` en `src/casi/llm/providers/base.py` con interfaz unificada para acciones (`complete_action`), decisiones (`complete`), recuperación de tool calls (`complete_tool_call`), métricas de tokens (`prompt_tokens`, `completion_tokens`) y adaptación de roles especializados (`with_role_instructions`).
- Implementación de `OpenAIClient` y `OpenAIProvider` en `src/casi/llm/providers/openai.py`:
  - Soporte nativo para `tool_calls` de OpenAI (transformación de `ToolDefinition` al esquema JSON de funciones).
  - Manejo de `tool_choice` requerido para `complete_tool_call` y `complete_action` (esquema `ProposeFileAction`).
  - Historial de conversación con asignación de identificadores de llamadas (`call_id`, `tool_call_id`).
  - Cliente HTTP estándar con `urllib.request` sin dependencias externas adicionales.
- Adaptador `OllamaProvider` en `src/casi/llm/providers/ollama.py` manteniendo el comportamiento y compatibilidad de `OllamaClient`.
- Factoría desacoplada `create_llm_client` en `src/casi/llm/providers/factory.py`.
- Integración en configuración (`src/casi/config.py`) con soporte para archivo `casi.toml` y variables de entorno (`CASI_LLM_PROVIDER`, `OPENAI_API_KEY`, etc.).
- Soporte CLI en `casi run`, `casi interactive` y `casi benchmark` con parámetros `--provider` y `--model`.
- Verificación completa: `ruff check`, `ruff format --check`, `python -m compileall` y `pytest -ra` pasando al 100% (586 tests pasando, 2 omitidos, 0 errores).

## Fase 2 Completada: Aislamiento con Git Worktree y Mutación Multifichero — 2026-10-14

- Implementación de `WorktreeManager` y `WorktreeSession` en `src/casi/workspace/worktree.py`:
  - Creación, seguimiento y eliminación limpia de worktrees efímeros en `.casi/worktrees/<task_id>`.
  - Soporte para repositorios git en HEAD desasociado (detached HEAD) y modo de rama temporal (`casi/wt-<task_id>`).
  - Fallback automático para repositorios que no son git o repositorios vacíos sin commits mediante copias aisladas en directorio.
  - Exclusión automática en `.git/info/exclude` para garantizar que `.casi/` no ensucie el estado del repositorio principal del usuario.
- Mutación multifichero aislada:
  - Operaciones sobre el worktree (`write_file`, `delete_file`, `stage_file`, `stage_files`, `apply_patch`, `reset`).
  - Garantía de aislamiento: el árbol de trabajo y la rama activa del usuario permanecen intactos durante toda la sesión.
- Integración con Docker runner:
  - Adaptación de `DockerRunner` y alias `DockerTestRunner` con el método `run_in_worktree` para ejecutar suites de tests directamente contra la ruta del worktree sin copias intermedias redundantes.
- Extracción de diff multifichero y revisión humana:
  - Generación de diff unificado (`get_diff`) y métricas de cambios por fichero (`get_diff_stats`) contra el commit base.
  - Flujo de revisión interactiva con selector `[y/N/v/save/?]` (`session.review()`).
  - Invariante de seguridad: `apply_to_main_repo()` exige `approved=True` para aplicar cambios sobre el repositorio principal.
- Poda y limpieza segura:
  - Limpieza de directorios, poda de metadatos de worktrees (`git worktree prune`) y eliminación de ramas efímeras (`git branch -D`).
- Suite de pruebas unitarias exhaustiva añadida en `tests/unit/test_worktree.py` (21 tests específicos).
- Verificación completa: `ruff check`, `ruff format --check`, `python -m compileall` y `pytest -ra` validados al 100%.

