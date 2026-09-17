# Ampliación de benchmarks — 2026-09-15

Implementada una [extensión versionada](../../benchmarks/capabilities_v2/README.md)
de doce tareas: cuatro de testing, cuatro de seguridad y cuatro de ML/extracción
de características. Se preservan los materiales de las suites anteriores.

## Entrega

- Cada tarea incluye enunciado, archivos permitidos, fixture visible, verificadores
  independientes y solución de referencia.
- Testing separa entrega, aprobación sobre código correcto y detección de cada
  mutación. Las 25 mutaciones de las cuatro tareas se ejecutan por separado;
  no se interrumpe la evaluación al encontrar la primera superviviente.
- Se cierran los huecos de reintentos por defecto y caracteres no ASCII en
  nuevas versiones de esos ejercicios, sin cambiar sus rúbricas históricas.
- Seguridad incluye controles positivos para impedir soluciones que denieguen
  todo; ML usa datos deterministas y comprueba separación entrenamiento/inferencia.
- Un validador reutilizable guarda resultados y hashes; los comandos por área
  funcionan con el CLI existente. Makefile y CI incluyen la extensión en Ruff;
  CI también valida fixtures y referencias con Docker.
- No se añaden dependencias ni se modifica el runtime del agente.

## Validación

```text
.venv/bin/pytest tests/unit/test_capabilities_v2_benchmark.py -ra
21 passed in 32.48s

.venv/bin/python benchmarks/capabilities_v2/validate.py \
  --output docs/reports/2026-09-15-capabilities-v2-validation.json
24/24 checks correctos en Docker

timeout 180 .venv/bin/pytest -ra
412 passed, 2 skipped, 2 warnings in 118.40s

.venv/bin/ruff check src tests benchmarks/development benchmarks/capabilities_v2
All checks passed!

.venv/bin/ruff format --check src tests benchmarks/development benchmarks/capabilities_v2
300 files already formatted

.venv/bin/python -m compileall -q src tests benchmarks/capabilities_v2
Correcto

git diff --check
Correcto
```

| Área | Bases rechazadas | Referencias aceptadas |
| --- | ---: | ---: |
| Testing | 4/4 | 4/4 |
| Seguridad | 4/4 | 4/4 |
| ML/features | 4/4 | 4/4 |

Los tests de control también rechazan suites siempre verdaderas, siempre falsas,
sin tests, con imports ausentes y las referencias históricas con cobertura
insuficiente. La validación Docker usa los mismos materiales cuyos 82 hashes se
guardan en el [artefacto JSON](2026-09-15-capabilities-v2-validation.json).
Los hashes fueron contrastados con los archivos finales.

El primer intento de validación Docker dentro del entorno restringido no accedió
a la imagen; la repetición autorizada fuera de esa restricción completó los 24
controles. La suite completa usa Python 3.12 y el entorno existente. No se probó
una instalación limpia mediante `uv sync --locked`: continúa la desincronización
previa del lockfile con las dependencias de UI, ajena a esta ampliación.

Los omitidos siguen siendo la reparación opt-in con Ollama y la rama Docker
ausente cuando Docker está disponible. Los avisos de Starlette/httpx y AnyIO
son los mismos de la revisión anterior.

## Alcance de los resultados

Esto valida el diseño ejecutable de los benchmarks; **no es una medición de
capacidad del modelo**. La aceptación del modelo requiere ejecutar los comandos
por área con Ollama y conservar nuevos artefactos. No se declara una mejora
respecto al histórico 7/12 de desarrollo.

La puntuación sigue siendo aceptación completa por tarea; la salida de pytest
desglosa las mutaciones, sin añadir porcentajes nuevos al esquema del runtime.
No se mide detección general de vulnerabilidades, Deep Learning ni precisión
predictiva. Las rúbricas no garantizan cobertura exhaustiva ni resistencia a
candidatos deliberadamente adversarios.
