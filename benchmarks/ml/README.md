# Machine learning — suite local v1

Cinco tareas deterministas de Python (solo biblioteca estándar) para evaluar la
capacidad de CASI en fundamentos de ML: métricas, splits, preprocesado, batching
y codificación. Se ejecuta por separado de las 26 tareas generales y de la suite
de desarrollo.

| ID | Capacidad | Trabajo | Dificultad |
| --- | --- | --- | --- |
| ml_001 | Métricas de evaluación | Accuracy, precision, recall y F1 binarios | Básica |
| ml_002 | Partición de datos | Train/test split con semilla y sin fugas | Básica |
| ml_003 | Preprocesado | Estandarización por columna (ddof=1) | Intermedia |
| ml_004 | Batching | Mini-batches con último lote parcial | Básica |
| ml_005 | Codificación | One-hot con número correcto de clases | Básica |
| ml_006 | Pérdida | MSE (no RMSE) y validación de longitud | Básica |

Las tareas usan `category: ml` para enrutar al perfil especializado del agente.

## Ejecutar con un modelo

```bash
uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/ml/tasks \
  --repos-dir benchmarks/ml/repositories \
  --list

uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/ml/tasks \
  --repos-dir benchmarks/ml/repositories \
  --model qwen2.5-coder:7b \
  --output /tmp/casi-ml.json --format both
```

## Validar sin Ollama

```bash
uv run --no-sync pytest tests/unit/test_ml_benchmark.py -ra
```
