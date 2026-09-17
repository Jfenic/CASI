# Extensión de capacidades v2

Doce tareas nuevas y separadas: cuatro de escritura de tests, cuatro de seguridad
y cuatro de ML/extracción de características. Python 3.11+, pytest y biblioteca
estándar; datos pequeños, sin GPU, descargas ni entrenamiento.

Las suites anteriores siguen intactas. `test_001` y `test_002` son versiones
ampliadas de los ejercicios de reintentos y slug, con IDs y rúbricas nuevas.
Los resultados de esta extensión no se deben mezclar con los históricos de
`development`, `security` o `ml`.

## Tareas

| Área | ID | Capacidad y criterio principal |
| --- | --- | --- |
| Testing | `test_001` | Reintentos: escribir tests de límites, tres intentos por defecto y excepciones; detectar 8 mutaciones. |
| Testing | `test_002` | Slug ASCII: escribir regresiones de separadores, dígitos y caracteres no ASCII; detectar 6 mutaciones. |
| Testing | `test_003` | Descuentos: reproducir errores de umbral y validar negativos; detectar 5 mutaciones. |
| Testing | `test_004` | Integración de pedidos/inventario: cantidades, agotamiento y atomicidad de errores; detectar 6 mutaciones. |
| Seguridad | `sec_v2_001` | Autorizar por tenant y propietario/publicación; impedir acceso cruzado y alias mutables. |
| Seguridad | `sec_v2_002` | Validar destinos de archivos, traversal y escapes por symlinks; aceptar nombres legítimos. |
| Seguridad | `sec_v2_003` | Consultas SQLite parametrizadas con usuarios activos, comillas y texto SQL literal legítimo. |
| Seguridad | `sec_v2_004` | Redactar secretos en estructuras anidadas sin borrar datos inocuos ni mutar la entrada. |
| ML | `ml_v2_001` | Imputar y centrar con medias aprendidas solo del entrenamiento, manteniendo estado entre transformaciones. |
| ML | `ml_v2_002` | Extraer categorías con vocabulario estable y manejar valores desconocidos sin aprenderlos. |
| ML | `ml_v2_003` | Ventanas temporales completas y causales: media, mínimo y máximo. |
| ML | `ml_v2_004` | Estadísticas de señales: media, RMS, varianza poblacional y cruces de cero. |

Los enunciados YAML contienen el contrato completo, las rutas editables y el
presupuesto. Las dificultades son orientativas, no una calibración universal.

## Ejecutar y conservar resultados por área

Con Ollama y la imagen `casi-sandbox:latest` disponibles, desde la raíz:

```bash
.venv/bin/casi benchmark \
  --tasks-dir benchmarks/capabilities_v2/testing/tasks \
  --repos-dir benchmarks/capabilities_v2/testing/repositories \
  --model qwen3.5:4b --output /tmp/casi-v2-testing.json --format both

.venv/bin/casi benchmark \
  --tasks-dir benchmarks/capabilities_v2/security/tasks \
  --repos-dir benchmarks/capabilities_v2/security/repositories \
  --model qwen3.5:4b --output /tmp/casi-v2-security.json --format both

.venv/bin/casi benchmark \
  --tasks-dir benchmarks/capabilities_v2/ml/tasks \
  --repos-dir benchmarks/capabilities_v2/ml/repositories \
  --model qwen3.5:4b --output /tmp/casi-v2-ml.json --format both
```

Usar destinos nuevos para cada repetición. Añadir `--list` permite inspeccionar
las cuatro tareas de un área sin ejecutar el modelo.

## Qué significa aprobar

El evaluador existente conserva tests originales, permite modificar únicamente
`allowed_files` y agrega los verificadores ocultos después de la ejecución del
agente. `graders/` y `solutions/` nunca forman parte del repositorio del agente.
La puntuación independiente requiere Docker y no permite fallback local.

En testing se distinguen mediante checks nombrados y `verification_output`:

1. **Entrega:** existe el archivo solicitado (`test_delivery`).
2. **Código correcto:** la suite recolecta tests y pasa con la implementación
   correcta (`test_correct_implementation`). Si falla, no se puntúan mutaciones.
3. **Errores detectados:** cada mutación tiene un caso separado
   (`test_detects_mutation[nombre]`). Debe producir salida pytest 1; salida 0
   significa que sobrevivió, mientras 2/3/4/5 indican errores o ausencia de tests.

Las mutaciones se prueban en copias independientes, con timeout de 10 segundos
por ejecución. Se comprueban todas aunque sobreviva una anterior. Los casos
representan código antes de una corrección; el control correcto representa el
código después. Un error de colección en el archivo entregado puede interrumpir
el evaluador antes de los checks de calidad y nunca cuenta como detección.

Los informes mantienen separados `agent_success`, `patch_valid`, `task_success`
y la salida de aceptación. Una llamada sin contenido o una ruta equivocada es
un fallo de entrega; no demuestra incapacidad para diseñar buenas pruebas.
No se añade una métrica numérica global de mutaciones al esquema del runtime.

En seguridad se exigen tanto rechazos de entradas no autorizadas como aceptación
de entradas legítimas. Esto detecta reparaciones que bloquean todo, pero no mide
una tasa general de falsas alarmas de un analizador de vulnerabilidades.

En ML se comprueban valores, formas, casos límite, inmutabilidad y estabilidad
entre entrenamiento e inferencia. No se evalúa precisión predictiva ni Deep Learning.

## Validar los propios benchmarks

```bash
.venv/bin/pytest tests/unit/test_capabilities_v2_benchmark.py -ra
.venv/bin/ruff check benchmarks/capabilities_v2 tests/unit/test_capabilities_v2_benchmark.py
.venv/bin/ruff format --check benchmarks/capabilities_v2 tests/unit/test_capabilities_v2_benchmark.py
```

Para repetir la validación de bases/referencias en Docker y guardar resultados
y hashes de los materiales (sin usar Ollama):

```bash
.venv/bin/python benchmarks/capabilities_v2/validate.py \
  --output /tmp/casi-v2-fixture-validation.json
```

`--runner local` permite validar los fixtures conocidos sin Docker. El benchmark
con el modelo conserva su requisito de puntuación en Docker.

Estas pruebas usan el mismo `grade_task` con `LocalRunner` sobre fixtures conocidos.
Exigen rechazo de las doce bases y aceptación de las doce referencias; además,
rechazan tests vacíos, siempre verdaderos, siempre falsos y las antiguas suites
que no cubrían el número de reintentos por defecto o los caracteres no ASCII.
Pasar estas comprobaciones valida los materiales, no la capacidad de Ollama.

Las pruebas de mutación no son una barrera contra candidatos deliberadamente
adversarios y no prueban cobertura exhaustiva. Ante nuevas exigencias, publicar
otra versión y conservar estos contratos para comparaciones reproducibles.
