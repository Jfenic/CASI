# Capacidades evaluables en CASI

Mapa de habilidades que las suites miden de forma reproducible (sin LLM como juez).

## Desarrollo (`benchmarks/development`)

| Capacidad | Qué mide | Tareas |
| --- | --- | --- |
| `boundary_conditions` | Límites, paginación, entradas inválidas | dev_001 |
| `input_validation` | Tipos, errores explícitos, contratos de entrada | dev_002, dev_011 |
| `data_processing` | CSV, quoting, ajustes | dev_003 |
| `business_rules` | Reglas de negocio, decimales | dev_004 |
| `state_and_time` | Estado, TTL, reloj inyectado | dev_005 |
| `regression_and_mutability` | Fusión recursiva sin alias | dev_006 |
| `module_creation` | Crear módulo nuevo desde especificación | dev_007 |
| `algorithm_and_validation` | Grafos, orden topológico | dev_008 |
| `test_design` | Escribir tests con mutaciones | dev_009 |
| `regression_test_design` | Tests de regresión sobre API existente | dev_010 |
| `mini_project_integration` | Mini-proyecto multi-módulo (checkout); localizar bug de integración | dev_012 |

## Diagnóstico (`benchmarks/diagnosis`)

| Capacidad | Qué mide | Tareas |
| --- | --- | --- |
| `bug_localization` | Localizar línea y causa en un módulo | diag_001, diag_002 |
| `failure_analysis` | Analizar lógica incorrecta (orden, media) | diag_003, diag_004 |
| `test_expectation_analysis` | Contradicción test vs implementación | diag_005 |
| `call_stack_diagnosis` | Fallo en cadena de llamadas (varios archivos) | diag_006 |
| `requirement_mismatch_diagnosis` | Límites y condiciones del contrato | diag_007 |
| `mini_project_integration` | Diagnóstico en mini-proyecto multi-módulo (checkout) | diag_008 |

## Fundamentos académicos (`benchmarks/fundamentals`)

| Capacidad | Qué mide | Tareas |
| --- | --- | --- |
| `data_structures` | Pilas LIFO, colas FIFO, listas enlazadas | fund_001, fund_004, fund_009 |
| `search_algorithms` | Búsqueda binaria | fund_002 |
| `discrete_math` | MCD (Euclides) | fund_003 |
| `expression_evaluation` | Evaluación postfix / RPN | fund_005 |
| `trees` | Búsqueda en ABB | fund_006 |
| `sorting_algorithms` | Merge sort | fund_007 |
| `number_systems` | Decimal a binario | fund_008 |

## Ciberseguridad (`benchmarks/security`)

| Capacidad | Qué mide | Tareas |
| --- | --- | --- |
| `path_traversal_prevention` | Evitar escape de directorio base (LFI) | sec_001 |
| `timing_attack_mitigation` | Comparación constante de secretos | sec_002 |
| `injection_prevention` | Consultas SQL parametrizadas | sec_003 |

## Machine learning (`benchmarks/ml`)

| Capacidad | Qué mide | Tareas |
| --- | --- | --- |
| `evaluation_metrics` | Accuracy, precision, recall, F1 | ml_001 |
| `data_splitting` | Train/test split reproducible | ml_002 |
| `preprocessing` | Estandarización | ml_003 |
| `batching` | Mini-batches | ml_004 |
| `encoding` | One-hot | ml_005 |
| `loss_computation` | Funciones de pérdida (MSE) | ml_006 |

## Cómo ejecutar por suite

```bash
casi benchmark --tasks-dir benchmarks/diagnosis/tasks \
  --repos-dir benchmarks/diagnosis/repositories \
  --model qwen3.5:4b --output /tmp/diagnosis.json --format both
```

Sustituir `diagnosis` por `development`, `fundamentals`, `security` o `ml`. Los informes agrupan resultados por `capability`.
