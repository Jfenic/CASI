# Diagnóstico de fallos — suite local v1

Cinco tareas de solo lectura para medir búsqueda, análisis y propuesta acotada
de la causa raíz. El agente no debe parchear; la respuesta final es un JSON con
`file`, `line`, `cause` y `evidence`. La puntuación usa rúbricas ocultas
(`rubrics/`), no un LLM como juez.

| ID | Capacidad | Escenario | Dificultad |
| --- | --- | --- | --- |
| diag_001 | Localización | Contador que no incrementa | Básica |
| diag_002 | Localización | Clamp suma 1 de más en rango | Básica |
| diag_003 | Análisis | Orden ascendente con `reverse=True` | Básica |
| diag_004 | Análisis | Media con resta incorrecta | Intermedia |
| diag_005 | Tests vs código | Email válido solo con punto | Básica |

## Ejecutar con un modelo

```bash
uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/diagnosis/tasks \
  --repos-dir benchmarks/diagnosis/repositories \
  --model qwen2.5-coder:7b \
  --output /tmp/casi-diagnosis.json --format both
```

## Validar sin Ollama

```bash
uv run --no-sync pytest tests/unit/test_diagnosis_benchmark.py -ra
```
