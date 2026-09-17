# Desarrollo y verificación de software — suite local v1

Doce tareas deterministas de Python para evaluar CASI junto con un modelo.
Esta suite se ejecuta por separado de las 26 tareas iniciales: sus resultados
no deben mezclarse, porque la evaluación final es más exigente.

| ID | Capacidad | Trabajo | Dificultad orientativa |
| --- | --- | --- | --- |
| dev_001 | Límites e índices | Paginación, entradas inválidas e inmutabilidad | Básica |
| dev_002 | Validación de entradas | Booleanos de configuración, tipos y errores | Básica |
| dev_003 | Procesamiento de datos | CSV con comillas, duplicados, ajustes y CRLF | Intermedia |
| dev_004 | Reglas de negocio | Decimal y redondeo monetario por línea | Intermedia |
| dev_005 | Estado y tiempo | Caché TTL con reloj inyectado y sobrescritura | Intermedia |
| dev_006 | Regresiones | Fusión recursiva sin compartir objetos mutables | Intermedia |
| dev_007 | Creación de módulos | Lector JSONL con errores y números de línea | Intermedia |
| dev_008 | Algoritmos | Orden de dependencias, desempates y ciclos | Avanzada |
| dev_009 | Diseño de tests | Reintentos, llamadas, excepciones y límites | Intermedia |
| dev_010 | Tests de regresión | Normalización de texto y separadores | Básica |
| dev_011 | Validación de entradas | parse_version debe lanzar ValueError | Básica |
| dev_012 | Integración mini-proyecto | Checkout multi-módulo ignora cantidades | Avanzada |

Las dificultades son etiquetas de diseño de esta suite, no una escala externa.
No requiere servicios externos, dependencias de aplicación, red ni tiempos reales
para resolver los ejercicios; pytest y la biblioteca estándar son suficientes.

## Cómo se puntúa

1. El agente recibe el enunciado y una copia de `repositories/<nombre>` con
   código y pruebas visibles. `graders` y `solutions` están fuera de esa copia.
2. El agente propone cambios. Solo se admiten los archivos indicados en
   `allowed_files`; modificar otros archivos invalida el resultado.
3. El evaluador crea otra copia del repositorio original, incorpora únicamente
   los archivos permitidos de la propuesta y añade las pruebas de `graders`.
   De esta forma, las pruebas originales se conservan para la evaluación.
4. La verificación independiente se ejecuta en Docker, sin red y con timeout.
   No hay fallback local para esta puntuación. La tarea pasa si el agente termina
   correctamente y la verificación completa pasa.

En `dev_009` y `dev_010`, las pruebas escritas por el modelo deben pasar sobre
la implementación correcta y fallar al ejecutar los tests sobre **cinco mutaciones**.
Errores de importación/colección, ausencia de tests o una suite que falla siempre
no cuentan como detección válida. Cada ejecución de mutaciones tiene un límite
de 10 segundos. Los casos evalúan comportamiento descrito en el enunciado.

Estas medidas evitan falsos positivos habituales, pero no constituyen una
infraestructura resistente a candidatos deliberadamente adversarios. Las pruebas
independientes no están disponibles durante la generación; sí se ejecutan junto
al candidato durante la puntuación final. No se usa un LLM como juez.

## Ejecutar con un modelo

Desde la raíz del proyecto, con Ollama y la imagen `casi-sandbox:latest` disponibles:

```bash
uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --list

uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/development/tasks \
  --repos-dir benchmarks/development/repositories \
  --model qwen2.5-coder:7b \
  --output /tmp/casi-development.json --format both
```

Para comparar modelos, sustituir `--model` por
`--models qwen2.5-coder:7b,qwen3:8b`. Se mantienen las mismas tareas y criterios.

Los informes incluyen capacidad, dificultad, resultado del agente y verificación
independiente. Junto al informe se crea `<nombre>-artifacts/<modelo>/<tarea>/` con
la traza, respuesta, parche cuando existe, salida de las pruebas independientes
y un `result.json` por tarea para conservar resultados si la ejecución se interrumpe.
El campo `duration_seconds` conserva su significado anterior: mide ejecución del
agente, no toda la preparación y puntuación posterior.

Los máximos de pasos del YAML corresponden al presupuesto de decisiones usado
por el agente; el contador agregado del informe incluye otros eventos y puede
ser mayor. La configuración de reintentos y el modelo también afectan al coste.

## Comprobar la calidad de las tareas sin Ollama

```bash
uv run --no-sync pytest tests/unit/test_development_benchmark.py -ra
```

Cada fixture inicial debe fallar y cada solución de referencia debe pasar la
verificación independiente. También se comprueba el rechazo de modificaciones
en pruebas protegidas y de suites que cubren solo el camino feliz. Las soluciones
son material del evaluador: no se proporcionan como contexto al modelo.

Un resultado sobre esta suite pequeña es una medición exploratoria. No equivale a
SWE-bench ni estima por sí solo fiabilidad general en repositorios grandes.
