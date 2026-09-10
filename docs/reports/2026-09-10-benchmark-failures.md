# Benchmark failures — post-P2 (2026-09-10)

Re-ejecución tras publicar los cambios P2 (`dca1c66` en `main`). Modelo:
`qwen2.5-coder:7b`, una pasada, parches auto-aplicados en copias temporales.

Datos completos:

- [26 tareas — JSON](2026-09-10-qwen2.5-coder-7b.json) · [informe](2026-09-10-qwen2.5-coder-7b.md)
- [10 tareas de desarrollo — JSON](2026-09-10-development-qwen2.5-coder-7b.json) · [informe](2026-09-10-development-qwen2.5-coder-7b.md)

## Resumen

| Suite | Correctas / total | Tasa | Baseline 2026-09-09 |
| --- | ---: | ---: | ---: |
| 26 tareas | 24 / 26 | 92,31 % | 24 / 26 (92,31 %) |
| Desarrollo (10) | 1 / 10 | 10,00 % | (sin baseline previo) |

La tasa global se mantiene, pero **cambian las tareas que fallan**. El trabajo P2
resolvió `task_007` e introdujo una regresión en `task_017`. `task_023` sigue
fallando con un patrón distinto.

## Suite de 26 tareas — fallos

### `task_017` (fix) — regresión nueva

| Campo | Valor |
| --- | --- |
| Repositorio | `sort_app` |
| Pasos / duración | 16 / 19,06 s |
| `correction_attempts` | 0 |
| `patch_valid` | `null` |

**Error:** el agente terminó sin parche válido.

**Contexto:** en la pasada del 2026-09-09 esta tarea **pasaba**. La instrucción
pide manejar listas vacías en `sort_asc` sin romper el orden ascendente del resto.
El modelo no llegó a `propose_file` tras agotar nudges.

**Acción sugerida:** regresión determinista similar a `task_007` (tests visibles
fallan, el agente responde con texto sin parche).

### `task_023` (create) — sigue fallando, distinto modo de error

| Campo | Valor | 2026-09-09 |
| --- | --- | --- |
| Pasos / duración | 38 / 111,13 s | 37 / 104,67 s |
| `correction_attempts` | 0 | 0 (métrica incorrecta entonces) |
| `patch_valid` | `null` | `null` |

**Antes:** parche propuesto pero incorrecto (`A.L` en lugar de `A.L.`); agotó
reintentos de verificación.

**Ahora:** el agente termina **sin parche** (`missing required unified diff`).

Los nudges P2 evitan el falso positivo de parche inválido, pero el modelo no
consigue crear `initials.py`. Hay que reforzar el flujo CREATE (módulo ausente +
tests como contrato).

### Resuelto en esta pasada

| Tarea | Antes | Ahora |
| --- | --- | --- |
| `task_007` (fix email vacío) | fail — sin parche | **pass** |

## Suite de desarrollo — fallos

Solo **`dev_001`** (paginación) pasa la verificación independiente con graders
ocultos. Los nueve restantes fallan por una de estas causas:

| Patrón | Tareas | Detalle |
| --- | --- | --- |
| Agente OK, grader KO | `dev_002`–`dev_008` | Parche válido y aplicado, pero los tests de `_benchmark_checks` fallan |
| Timeout Ollama | `dev_009` | `Ollama request failed: timed out` |
| Sin parche | `dev_010` | Mismo error que `task_017`/`task_023` |

### Detalle por tarea (graders)

| ID | Capacidad | Agente | Causa principal del fallo |
| --- | --- | ---: | --- |
| `dev_002` | input_validation | OK | No lanza `ValueError` en strings inválidos |
| `dev_003` | data_processing | OK | CSV con comillas/CRLF — `line.split(",")` naive |
| `dev_004` | business_rules | OK | Redondeo monetario por línea (`0.01` vs `0.02`) |
| `dev_005` | state_and_time | OK | TTL cero debe aceptarse; implementación lo rechaza |
| `dev_006` | regression | OK | Fusión recursiva comparte objetos mutables |
| `dev_007` | module_creation | OK | Lector JSONL — errores sin `line N` en el mensaje |
| `dev_008` | algorithms | OK | Orden topológico / ciclos / desempates |
| `dev_009` | test_design | KO | Timeout del modelo |
| `dev_010` | regression_tests | KO | Sin parche |

## Prioridad P3 actualizada

1. **`task_023` / flujo CREATE:** el modelo debe crear módulos ausentes de forma
   fiable cuando los tests ya están cargados.
2. **`task_017` / regresión fix:** recuperar fiabilidad en fixes parciales
   (listas vacías u otros casos borde).
3. **Suite de desarrollo:** la brecha agente vs grader indica que el modelo pasa
   tests visibles pero no el contrato completo; usar estos fallos como casos de
   regresión deterministas.
4. **`dev_009`:** revisar timeout de Ollama o reducir carga de la tarea de diseño
   de tests.

## Reproducción

```bash
uv sync --locked --group dev
docker build -t casi-sandbox:latest -f docker/sandbox.Dockerfile .

uv run casi benchmark --model qwen2.5-coder:7b \
  --output docs/reports/2026-09-10-qwen2.5-coder-7b.json --format both

uv run casi benchmark --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --model qwen2.5-coder:7b \
  --output docs/reports/2026-09-10-development-qwen2.5-coder-7b.json --format both
```
