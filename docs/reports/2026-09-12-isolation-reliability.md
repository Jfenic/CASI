# Hito de aislamiento y fiabilidad — 2026-09-12

## Problema y cambios

El selector de tests elegía ejecución local cuando faltaban Docker o su imagen,
incluso con `LOCALCODE_AGENT_ALLOW_LOCAL_FALLBACK=false`. Ahora rechaza esos casos
con un error de infraestructura. El fallback pasa a estar desactivado por
defecto; un repositorio confiable puede usar el opt-in o seleccionar modo local
explícitamente. La autorización de herramientas y la aprobación de parches
siguen siendo controles separados.

Ruff vuelve a pasar. Makefile utiliza los mismos comandos de lint y formato
que CI. Se ordenan imports y se conserva el bug intencional de cantidades en
checkout mediante una excepción B007 limitada a ese archivo. No se cambian
enunciados ni aserciones de aceptación.

La traza anterior de `dev_009` mostraba un recordatorio que decía que los tests
fallaban cuando la salida era `1 passed`. El mensaje comprueba ahora que hay
fallos antes de afirmarlo, y conserva el contrato completo, incluida la ruta
del archivo solicitado. Las instrucciones de creación incluyen explícitamente
la escritura de tests aunque los tests existentes pasen. Se refuerzan también
las instrucciones sobre tipos y ausencia de referencias mutables compartidas.

El cliente Ollama reintenta como máximo dos veces una decisión vacía o sin
contenido utilizable, con un recordatorio del protocolo. No reintenta errores
de transporte, envelopes inválidos ni llamadas de herramienta mal formadas.
Cuando se recupera, suma los tokens informados por todos los intentos. Cada
petición mantiene su timeout: tres intentos pueden consumir hasta tres veces
el timeout de una petición. No hay ampliación del número de pasos del agente.
Si se agotan los reintentos, se propaga el error; el contrato actual de errores
no transporta el consumo de tokens de esos intentos fallidos.

La primera evaluación del hito seguía mostrando llamadas `propose_file` sin
`content`. Al revisar el payload se detectó que el protocolo JSON de modelos
thinking omitía las herramientas nativas, pero solo enviaba sus nombres en el
prompt. Ahora incluye las mismas descripciones, tipos y argumentos requeridos
del protocolo nativo. Una prueba comprueba el esquema enviado realmente para
`propose_file`, incluido `content` obligatorio. Se conserva la primera medición
y se repite desarrollo con este arreglo adicional.

## Verificación

Python 3.12.3, entorno `.venv`:

```text
366 passed, 2 skipped, 2 warnings in 71.70s
Ruff: All checks passed
Ruff format: 201 files already formatted
compileall: correcto
git diff --check: correcto
```

La ejecución completa se realizó fuera del sandbox del asistente para acceder
a Docker y a la API. Se omiten el fixture opt-in de Ollama y la rama Docker
ausente cuando Docker está disponible. Persisten los dos avisos de terceros
Starlette/httpx y AnyIO. Diez nuevos casos cubren fallback y modo local,
recordatorios de creación y recuperación/límite de respuestas vacías.

## Evaluación de desarrollo

La primera medición completa dio [7/12](2026-09-12-development-milestone.md).
La repetición del día 12 tras añadir esquemas quedó parcial, con seis resultados.
El 13 de septiembre se completó una nueva ejecución: [7/12](2026-09-13-development-tool-schemas.md),
sin cambios de rúbrica durante esa revisión. Véase el
[cierre](2026-09-13-milestone-closure.md) para verificación y fallos residuales.
Baseline guardado: [8/12](2026-09-12-development-qwen3.5-4b-whitespace-fix.md).

```bash
.venv/bin/casi benchmark --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories --model qwen3.5:4b \
  --output docs/reports/2026-09-12-development-milestone.json --format both
```

## Estado de entrega

Cambios locales para revisión, sin commit ni publicación de este hito.
