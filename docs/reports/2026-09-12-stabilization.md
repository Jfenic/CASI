# Estabilización de CASI — 2026-09-12

Se corrigieron fallos del contrato de diagnóstico y del contexto de reparación,
y se repitieron las verificaciones de código y las evaluaciones con
`qwen2.5-coder:7b`. Las rúbricas y los tests de aceptación de los benchmarks no se
modificaron. Los resultados miden esta ejecución, no una garantía de éxito en
repositorios nuevos.

## Cambios

- El parser conserva objetos JSON en `content`. Diagnóstico comparte el extractor
  entre ejecución y evaluación, exige `file`, `line`, `cause` y `evidence`, y
  reintenta respuestas inválidas hasta un límite. Una respuesta en prosa no se
  declara un diagnóstico exitoso tras agotar ese límite.
- Las instrucciones de diagnóstico distinguen la causa en la implementación de
  la aserción que muestra el fallo. Este flujo no verifica ni propone parches.
- Los reintentos conservan la verificación del parche y utilizan su salida más
  reciente, en lugar de volver al error inicial de módulo inexistente.
- El contexto de reparación omite rutas externas que no existen en el
  repositorio; los módulos de la biblioteca estándar y de paquetes instalados
  no generan instrucciones para crear archivos locales.
- Los tests descubiertos en la raíz se leen con rutas relativas.
- Las propuestas Python eliminan líneas vacías terminales antes de construir el
  diff, evitando el rechazo observado en `dev_008` por `new blank line at EOF`.
- Las instrucciones de creación y reparación conservan el contrato completo del
  usuario, incluidos casos límite que los tests visibles no comprueban.
- Ruff corrige los seis errores anteriores y el formato pendiente. README,
  TODO, planificación y tracker reflejan el estado verificado.

## Verificación de código

Python 3.12.3, entorno `.venv` existente:

```text
319 passed, 2 skipped, 2 warnings in 73.18s
Ruff: All checks passed
Ruff format: 181 files already formatted
compileall: correcto
git diff --check: correcto
```

La suite incluye API y Docker. Se omiten el fixture opt-in de reparación con
Ollama y la prueba del camino sin Docker cuando el daemon está disponible.
Persisten dos avisos de deprecación de terceros: Starlette/httpx y el alias
`anyio.abc.BlockingPortal`. No se han ocultado mediante filtros de warnings.

Se añadieron 12 casos de regresión para conservar diagnóstico estructurado,
recuperar/rechazar prosa, validar el número de línea, excluir contexto externo,
crear un parche Python aplicable y usar el resultado más reciente al reintentar.

La primera ejecución restringida no terminó. Fuera del sandbox hubo un timeout
inicial de arranque Docker; una comprobación directa y dos suites completas
posteriores pasaron. El timeout inicial no volvió a reproducirse. El acceso a
Docker y Ollama locales requiere permisos del entorno de ejecución.

## Evaluación con el modelo real

Los informes JSON/Markdown y los directorios `*-artifacts` contienen resultados,
trazas, respuestas, diffs y comprobaciones independientes por tarea.

La primera medición tras corregir únicamente el formato de diagnóstico dio
1/5. Con la instrucción de localizar la causa en la implementación, el resultado
fue 4/5; las cinco respuestas cumplieron el formato. Se conserva también el
[informe intermedio](2026-09-12-diagnosis-qwen2.5-coder-7b.md).

El resumen agregado de general, desarrollo y ML no quedó incorporado en este
informe. No debe interpretarse como una medición completa de esas suites.
El resultado de diagnóstico 4/5 está en el
[informe específico](2026-09-12-diagnosis-stabilized.md); los demás resultados
históricos deben consultarse en sus archivos individuales.

## Reproducción

```bash
.venv/bin/pytest -ra
.venv/bin/ruff check src tests benchmarks/development
.venv/bin/ruff format --check src tests benchmarks/development
.venv/bin/python -m compileall -q src tests
git diff --check

.venv/bin/casi benchmark --model qwen2.5-coder:7b \
  --output docs/reports/2026-09-12-general-stabilized.json --format both

# Repetir con SUITE=development, ml o diagnosis:
SUITE=diagnosis
.venv/bin/casi benchmark \
  --tasks-dir "benchmarks/$SUITE/tasks" \
  --repos-dir "benchmarks/$SUITE/repositories" \
  --model qwen2.5-coder:7b \
  --output "docs/reports/2026-09-12-$SUITE-stabilized.json" --format both
```

Las correcciones y los informes quedan en el árbol de trabajo para revisión;
no se ha creado un commit ni publicado cambios.
