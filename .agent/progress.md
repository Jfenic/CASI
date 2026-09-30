# Current Progress

## Direction

Multi-Agent Orchestration & Closed Catalog of Specialized Personalities (Software Engineering Roles).
Reference: [docs/features/orchestration/](docs/features/orchestration/).

## State: Features Completed & Validated
 
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
