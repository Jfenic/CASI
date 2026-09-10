# Estabilización P0/P1 — 2026-09-09

P0 y P1 quedan verificados localmente. La configuración de CI está actualizada;
la ejecución remota de GitHub Actions queda pendiente de publicar los cambios.
P2 conserva los fallos reales encontrados, sin considerarlos resueltos.

## Cambios

- Sincronización de `uv.lock` con las dependencias de desarrollo y API.
- CI instala con `uv sync --locked --group dev`, usa uv 0.12.4, comprueba Ruff
  y formato, construye la imagen Docker y ejecuta pruebas y compilación.
- Corrección del import de `LLMClient` en el orquestador; dependencias FastAPI
  expresadas con `Annotated`; tratamiento explícito del error de respuesta vacía.
- Adopción de `StrEnum` conservando valores, `str`, formato y representación
  anteriores; limpieza de imports y formato de `src` y `tests`.
- Los textos de ayuda y el prompt del modelo conservan exactamente su contenido.
- La prueba E2E ahora exige éxito del agente, un parche y verificación satisfactoria.
- `TestResult` deja de provocar avisos de colección de pytest.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `uv sync --locked --group dev` | Correcto; lockfile sin cambios adicionales |
| `ruff check src tests` | Sin incidencias (antes: 382) |
| `ruff format --check src tests` | 130 archivos conformes |
| Suite completa, Python 3.12.3 | 243 passed, 2 skipped; 27.19 s |
| Suite completa, Python 3.11.15 aislado | 243 passed, 2 skipped; 32.52 s |
| Docker real | Prueba de integración satisfactoria; daemon 29.7.2 |
| Ollama E2E, `qwen2.5-coder:7b` | 1 passed; 33.08 s |
| Compilación Python y `git diff --check` | Correctos |

Las omisiones en la suite completa son Ollama (opt-in, ejecutado aparte) y la
prueba del caso «Docker no disponible» porque el daemon sí está disponible.
Quedan dos avisos de deprecación de las dependencias Starlette/AnyIO en la última
suite; no son errores de CASI. Las comprobaciones con servicios y la API se
realizaron fuera del sandbox del agente: sus restricciones impiden acceder a
los servicios y bloquearon la primera ejecución de TestClient.

## Benchmark real

Una pasada de las 26 tareas con `qwen2.5-coder:7b`, Q4_K_M, contexto declarado
32768. Identificador del modelo:
`dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.

| Categoría | Correctas / total |
| --- | ---: |
| Inspección | 3 / 3 |
| Lectura | 5 / 5 |
| Búsqueda | 3 / 3 |
| Corrección | 11 / 12 |
| Creación | 2 / 3 |
| **Total** | **24 / 26 (92,31 %)** |

Duración acumulada medida dentro del agente: 324,90 s; media: 12,50 s por tarea.
Estos tiempos no incluyen toda la preparación de repositorios ni los comandos
posteriores de comprobación. Tokens reportados: 161402 de entrada y 4279 de salida.

Datos completos: [JSON](2026-09-09-qwen2.5-coder-7b.json) e
[informe generado](2026-09-09-qwen2.5-coder-7b.md).

## P2, ordenado por evidencia

1. **Recuperación de parches que fallan tests — `task_023`.** La creación de
   `initials.py` agotó reintentos (104,67 s). Los tests exigían `A.L.` y `G.`,
   pero la implementación verificada devolvía `A.L` y `G`. Añadir una regresión
   determinista que compruebe que los errores de aserción llegan al siguiente
   intento y que un fallo final no pierde la evidencia de verificación.
2. **Finalización sin parche — `task_007`.** El agente terminó sin un parche
   válido (25,79 s), con tests todavía fallidos. La fixture ya rechaza cadenas
   vacías; el test que falla trata la ausencia de `@`. Cubrir la distinción entre
   una condición solicitada que ya se cumple y otros tests que siguen fallando.
3. **Fidelidad de métricas y trazas.** `task_023` informa agotamiento de reintentos,
   pero el JSON registra `correction_attempts: 0` y `patch_valid: null`. Preservar
   los datos del último intento fallido y correlacionarlos entre especialistas.
4. **Ampliar validación.** Repetir los casos fallidos después de corregirlos y
   después la suite de 26 tareas; fortalecer comprobaciones específicas de cada
   objetivo y comparar varias pasadas antes de estimar fiabilidad general.

El 92,31 % corresponde a una sola pasada y al criterio actual del benchmark.
Las tareas de lectura se puntúan por finalización del agente, sin revisión
semántica independiente; sus fixtures pueden contener tests fallidos a propósito.
El 100 % de validez de parches del informe solo considera resultados con
`patch_valid` informado: no incluye las tareas que terminaron sin parche válido.

## Reproducción

```bash
uv sync --locked --group dev
uv run --no-sync ruff check src tests
uv run --no-sync ruff format --check src tests
docker build -t casi-sandbox:latest -f docker/sandbox.Dockerfile .
uv run --no-sync pytest -ra
uv run --isolated --python 3.11 --locked --group dev pytest -ra
OLLAMA_E2E=1 uv run --no-sync pytest tests/integration/test_ollama_repair.py -ra
uv run --no-sync casi benchmark --model qwen2.5-coder:7b \
  --output /tmp/casi-benchmark.json --format both
```

Requiere Docker y Ollama disponibles y el modelo instalado. Los parches del
benchmark se aplican a copias temporales de las fixtures.

## Referencia del código

Commit de partida: `6b944d520ed4fdab46a00df2e5b458232650873c` más los cambios locales
de estabilización. SHA-256 agregado de los archivos versionados bajo `src`,
`tests`, `pyproject.toml` y `uv.lock` (ruta + NUL + contenido + NUL, rutas ordenadas):

`1fc201a329cab4ef19ae41c3359877f7dce906873c1f4c548e33a62a5271a804`
