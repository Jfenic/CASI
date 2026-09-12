# Ciberseguridad — suite académica

Tres ejercicios típicos de asignaturas de seguridad informática, auditoría de
código y desarrollo seguro. Cada uno reproduce un fallo clásico que se enseña en
OWASP Top 10 y exámenes de grado.

| ID | Tema OWASP / curso | Ejercicio | Capacidad |
| --- | --- | --- | --- |
| sec_001 | A01 Broken Access Control / LFI | Evitar directory traversal en `safe_join` | `path_traversal_prevention` |
| sec_002 | A02 Cryptographic Failures / side channels | Comparación constante de tokens | `timing_attack_mitigation` |
| sec_003 | A03 Injection | Consultas SQL parametrizadas | `injection_prevention` |

Los fallos iniciales son representativos de código vulnerable real: concatenación
de rutas sin validar, `==` sobre secretos, e interpolación de SQL con f-strings.

## Ejecutar

```bash
uv run --no-sync casi benchmark \
  --tasks-dir benchmarks/security/tasks \
  --repos-dir benchmarks/security/repositories \
  --model qwen3.5:4b \
  --output /tmp/security.json --format both
```

## Validar sin Ollama

```bash
uv run --no-sync pytest tests/unit/test_security_benchmark.py -ra
```
