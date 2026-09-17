# Revisión de fallos y capacidad de testing — 2026-09-15

## Conclusión

La suite actual de CASI pasa. Los cinco fallos de la última medición completa
guardada de desarrollo no demuestran que sus tests sean demasiado difíciles:
dos incumplen requisitos explícitos y tres no entregan un parche evaluable.
Hay además una forma de invocar pytest que recoge indebidamente los ejercicios
de benchmark y produce errores ajenos a la suite del runtime.

El usuario aclaró que se refiere a la calidad de los benchmarks que evalúan al
modelo. El análisis principal compara sus enunciados, verificadores, soluciones
y fallos guardados; la ejecución de pytest sirve como control del evaluador.

## Verificación actual

Desde la raíz del repositorio, con Python 3.12 y el entorno `.venv` existente:

```text
timeout 180 .venv/bin/pytest -ra
391 passed, 2 skipped, 2 warnings in 96.47s
```

Los omitidos son la reparación real con Ollama (requiere `OLLAMA_E2E=1`) y
la rama de Docker no disponible, porque Docker estaba disponible. Los avisos
son de APIs deprecadas en Starlette/httpx y AnyIO; no son fallos de tests.
Esta ejecución no mide la capacidad actual del modelo Ollama.

La suite incluye las doce comprobaciones parametrizadas de
`test_development_task_rejects_baseline_and_accepts_reference`: los ejercicios
iniciales fallan y las soluciones de referencia pasan, incluidos los evaluadores
de tests generados. Estos controles usan `LocalRunner` sobre fixtures conocidos;
la puntuación del benchmark real usa Docker.

### Recoger toda la raíz produce errores distintos

```bash
.venv/bin/python -m pytest --collect-only -q --rootdir . .
```

Resultado reproducido: código de salida 2, **79 errores de colección**.
El argumento posicional `.` hace que se recojan también `benchmarks/graders`,
las soluciones y los pequeños repositorios de ejercicios. Sus imports esperan
ejecutarse dentro de cada repositorio preparado por el evaluador; algunos
módulos faltan deliberadamente en tareas de creación.

Para comprobar CASI, usar `.venv/bin/pytest -ra` o
`.venv/bin/pytest tests -ra`. Para evaluar el modelo, usar `casi benchmark`
con los directorios de tareas y repositorios de la suite correspondiente.
No ejecutar todos los fixtures como una sola suite.

El comando de respaldo de `src/casi/sandbox/pytest_command.py` también añade
explícitamente la raíz. Es un punto a revisar para proyectos con `testpaths`
configurado. En este repositorio, la detección normal encuentra `Makefile` y
selecciona `make test`; no se ha demostrado que la UI tome ese respaldo aquí.

## Qué falló en el benchmark guardado

Fuente: [medición completa del 13/09](2026-09-13-development-tool-schemas.md),
con `qwen3.5:4b`: **7/12** de aceptación independiente, **9/12** de finalización
del agente. Se revisaron `result.json`, propuestas y trazas bajo
`2026-09-13-development-tool-schemas-artifacts/qwen3.5_4b/`.
Son resultados históricos; el runtime tiene cambios posteriores.

| Tarea | Capacidad | Causa observada | Valoración del test |
| --- | --- | --- | --- |
| `dev_005` | Expiración y casos límite | La propuesta usa `ttl <= 0` para lanzar ValueError. El contrato exige aceptar cero y expirar inmediatamente; solo los negativos deben lanzar la excepción. | Comprueba literalmente el requisito, con reloj inyectado y sin esperas reales. |
| `dev_006` | Fusión recursiva e independencia de datos | `propose_file` sin `content`, seguido de explicaciones y cierre sin parche. La aceptación ejecutada después evalúa el fixture original, no una reparación entregada. | La independencia de listas anidadas es explícita. En ejecuciones dirigidas posteriores también hubo propuestas con referencias compartidas. |
| `dev_009` | Escribir tests de reintentos | No se ejecuta ninguna llamada de propuesta. La última respuesta final contiene texto con forma de llamada a `propose_file` y una ruta distinta de la solicitada (`tests/test_retry.py`). | El evaluador falla porque falta el archivo. No llegó a medir la detección de mutaciones de una suite entregada. |
| `dev_010` | Escribir regresiones de normalización | Propone `tests/test_slug.py` en un directorio inexistente, aunque se pidió `test_slug.py`; tras el rechazo, se agotan las respuestas utilizables de Ollama. | Falla antes de puntuar la calidad de los tests. La traza conserva solo un extracto del contenido, insuficiente para evaluarlo completo. |
| `dev_011` | Validación y excepciones | La propuesta inventa `__import__('errors').set_exc_value(...)`; las entradas con letras lanzan ModuleNotFoundError en vez de ValueError. | Comprueba una excepción exigida expresamente, con entradas sencillas como `1.a.3`. |

En `dev_005` y `dev_011` pasan los tests visibles, pero falla la aceptación
independiente. Esto evidencia cobertura insuficiente de los tests visibles para
el contrato completo. Aumentar el presupuesto de pasos por sí solo no corrige
esos dos falsos positivos: el agente ya había dado la tarea por terminada.

## ¿Son demasiado exigentes las pruebas de tests generados?

`dev_009` exige que la suite pase sobre la implementación correcta y detecte
cinco errores deliberados: no reintentar, ocultar la excepción final, hacer un
intento extra, capturar todas las excepciones y omitir la validación de intentos.

`dev_010` comprueba cinco errores: no convertir mayúsculas, reemplazar solo
espacios, conservar guiones en los extremos, no agrupar separadores y perder
dígitos. Todos corresponden a cláusulas del enunciado.

Las referencias pasan estos controles en la ejecución actual. Son ejercicios
acotados, deterministas y realizables con pytest y biblioteca estándar. Las
etiquetas básica/intermedia son orientativas; no calibran dificultad para cada
modelo. No hay evidencia para suavizar las rúbricas por estos fallos.

La puntuación actual es todo o nada y el bucle de mutaciones se detiene al primer
fallo. Para diagnosticar mejor la capacidad sería útil informar por separado:

1. Archivo de tests entregado y recolectable.
2. Tests aprobados sobre la implementación correcta.
3. Mutaciones detectadas, supervivientes y errores de ejecución.
4. Requisitos comprobados y requisitos sin evidencia.

Ese detalle complementaría el criterio de aceptación, sin rebajarlo.

### Huecos de cobertura confirmados

En copias temporales se ejecutaron las suites de referencia de tests generados
contra errores adicionales, sin modificar las cinco mutaciones oficiales:

- `retry`: cambiar el valor por defecto de `attempts=3` a `attempts=2` sigue
  dejando **5 tests aprobados**. La suite de referencia no comprueba que se
  hagan exactamente tres intentos al omitir el argumento y agotar reintentos.
- `slugify`: permitir también `é` en la expresión regular sigue dejando
  **7 tests aprobados**, aunque el contrato admite únicamente letras ASCII
  y dígitos. La referencia no prueba caracteres no ASCII.
- Como control, sustituir la clase ASCII por `\w` sí se detecta: falla
  `a_b → a-b`, porque esa variante conserva el guion bajo.

Estas comprobaciones son una auditoría de cobertura, no una nueva puntuación
del modelo. Las suites de referencia superan el evaluador oficial pero omiten
estos requisitos: aprobar cinco mutaciones no equivale a cubrir todo el contrato.
Esto aconseja añadir casos y mutaciones en una versión futura del benchmark,
preservando la versión actual para comparar mediciones. No invalida los cinco
fallos observados ni justifica rebajar su criterio de aceptación.

## Prioridades que se desprenden de la revisión

1. Recuperar argumentos y rutas de propuestas, y evitar terminar una petición de
   creación con una descripción textual de la llamada.
2. Añadir verificación derivada del contrato del usuario para detectar huecos de
   cobertura antes de declarar éxito; mantener ocultos los graders del benchmark.
3. Para repositorios nuevos, generar pruebas apropiadas a la funcionalidad:
   omitir la verificación por ausencia de tests no evalúa la capacidad solicitada.
4. Repetir las tareas con el runtime actual y conservar artefactos nuevos antes
   de afirmar una mejora del modelo. Las trazas históricas no sustituyen esa medición.

Esta revisión no modifica código, fixtures, soluciones ni rúbricas.
