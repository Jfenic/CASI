# Fundamentos de informática — suite académica

Nueve ejercicios típicos de grados en Ingeniería Informática / Ciencias de la
Computación. Cubren asignaturas clásicas de primer y segundo curso: estructuras
de datos, algoritmos, matemática discreta, árboles, sistemas numéricos y
evaluación de expresiones.

| ID | Asignatura típica | Ejercicio clásico | Capacidad | Dificultad |
| --- | --- | --- | --- | --- |
| fund_001 | Estructuras de datos | Pila LIFO (`push`/`pop`/`peek`) | `data_structures` | Básica |
| fund_002 | Algoritmos | Búsqueda binaria en lista ordenada | `search_algorithms` | Básica |
| fund_003 | Matemática discreta | MCD — algoritmo de Euclides | `discrete_math` | Básica |
| fund_004 | Estructuras de datos | Invertir lista enlazada | `data_structures` | Intermedia |
| fund_005 | Compiladores / Algoritmos | Evaluador postfix (RPN) | `expression_evaluation` | Intermedia |
| fund_006 | Árboles | Búsqueda en árbol binario de búsqueda | `trees` | Intermedia |
| fund_007 | Algoritmos | Merge sort (merge + ordenación) | `sorting_algorithms` | Intermedia |
| fund_008 | Sistemas / Arquitectura | Conversión decimal → binario | `number_systems` | Básica |
| fund_009 | Estructuras de datos | Cola FIFO (`enqueue`/`dequeue`) | `data_structures` | Básica |

Cada tarea incluye código inicial con un fallo representativo de errores habituales
en exámenes (orden LIFO/FIFO invertido, off-by-one, rama incorrecta del árbol,
operandos en orden inverso, restos sin invertir, etc.).

## Puntuación

Igual que la suite de desarrollo: el agente solo puede modificar `allowed_files`;
la verificación independiente en `graders/` decide el resultado final.

## Ejecutar

```bash
uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/fundamentals/tasks \
  --repos-dir benchmarks/fundamentals/repositories \
  --model qwen3.5:4b \
  --output /tmp/fundamentals.json --format both
```

## Validar sin Ollama

```bash
uv run --no-sync pytest tests/unit/test_fundamentals_benchmark.py -ra
```
