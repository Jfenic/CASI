# Cierre de evaluación y documentación — 2026-09-13

Se revisó el hito local de aislamiento y fiabilidad sobre `d37ef45`, se completó
la documentación técnica y se completó una medición completa posterior al arreglo
de esquemas de herramientas. El runtime se mantuvo sin cambios durante esa
medición; las rúbricas no se modificaron en esta revisión.

## Cambios y alcance

- Arquitectura y bucle del agente describen el flujo implementado, incluida la
  propuesta, verificación aislada y aprobación de parches.
- Las decisiones de herramientas y Docker dejan de ser plantillas vacías.
- Changelog, planificación y evaluación distinguen estado actual, mediciones
  históricas, éxito del agente y aceptación independiente.
- Dos regresiones deterministas comprueban que el evaluador rechaza parches que
  pasan los tests visibles pero comparten valores mutables de overrides o cuentan
  líneas JSONL después de eliminar las vacías. Los candidatos se reconstruyen en
  copias temporales; no requieren Ollama ni alteran fixtures o rúbricas.
- Se conserva la corrección local del protocolo: esquemas completos en thinking
  mode, reintentos vacíos acotados y fallback local explícito. No se introduce
  orquestación nueva ni se amplían presupuestos de pasos.

Estas regresiones protegen la detección de falsos positivos; no hacen que el modelo
resuelva automáticamente los casos. Los fallos de contenido y de protocolo se
mantienen visibles en la medición real.

## Verificación

Python 3.12.3, entorno `.venv`, Docker y API incluidos:

```text
timeout 180 .venv/bin/pytest -ra
369 passed, 2 skipped, 2 warnings in 96.00s

.venv/bin/ruff check src tests benchmarks/development
All checks passed!

.venv/bin/ruff format --check src tests benchmarks/development
201 files already formatted

.venv/bin/python -m compileall -q src tests
Correcto

git diff --check
Correcto
```

Se omiten el fixture opt-in de reparación Ollama y la rama de Docker ausente
cuando Docker está disponible. Persisten los avisos de terceros Starlette/httpx
y AnyIO. El benchmark separado sí utiliza Ollama real.

## Evaluación de desarrollo

Resultado con `qwen3.5:4b`: **7/12 (58,33 %)**; éxito del agente **9/12 (75 %)**.
Duración media del agente: 43,54 s; 78.752 tokens de entrada y 6.729 de salida
registrados. Los intentos vacíos agotados no conservan todo su consumo en el
contrato de error, por lo que estos tokens no representan necesariamente el coste total.
[Informe completo](2026-09-13-development-tool-schemas.md) y
[JSON](2026-09-13-development-tool-schemas.json).

| Medición | Aceptación independiente | Éxito del agente |
| --- | ---: | ---: |
| 12/09, whitespace fix | 8/12 | Consultar informe histórico |
| 12/09, primer hito | 7/12 | 9/12 |
| 13/09, esquemas completos | 7/12 | 9/12 |

No se demuestra mejora de tasa global. JSONL y orden de dependencias pasan en
esta ejecución, mientras TTL y versiones dejan de pasar respecto al primer hito.
Son ejecuciones individuales con variabilidad del modelo, no una comparación
estadística. No se promedian resultados de suites o configuraciones distintas.

| Fallo residual | Evidencia | Próximo criterio verificable |
| --- | --- | --- |
| `dev_005`, TTL | Rechaza TTL cero, aunque el contrato exige expiración inmediata | Cumplir cero y negativo por separado sin inventar validaciones |
| `dev_006`, fusión | `propose_file` sin `content`, seguido de respuestas sin parche | Recuperar el argumento obligatorio y producir una propuesta verificable |
| `dev_009`, tests de reintentos | Termina sin propuesta | Crear el archivo solicitado y superar las cinco mutaciones |
| `dev_010`, tests de slug | Respuesta vacía tras reintentos | Obtener una decisión utilizable y superar las cinco mutaciones |
| `dev_011`, versiones | Inventa un módulo `errors` al manejar ValueError | Mantener la excepción contractual sin dependencias inventadas |

Pasan `dev_001`, `dev_002`, `dev_003`, `dev_004`, `dev_007`, `dev_008` y `dev_012`.
Dos propuestas aprobadas por el runtime son rechazadas por aceptación independiente
(TTL y versiones). Enviar esquemas completos corrige una omisión de CASI, pero
no garantiza que el modelo respete los argumentos obligatorios.

Prioridad siguiente: recuperación de llamadas incompletas y cierre de tareas de
creación de tests, con regresiones deterministas y posterior medición completa.
Los fallos semánticos deben seguir evaluándose contra el contrato sin modificar
rúbricas ni introducir los verificadores ocultos en el contexto del agente.

La ejecución anterior `2026-09-12-development-tool-schemas-artifacts` contiene
solo seis resultados, sin informe agregado; se conserva como evidencia parcial.
La medición del día 13 usa un destino nuevo y las doce tareas. El
[manifiesto](2026-09-13-development-tool-schemas-manifest.json) registra comando,
commit base y hashes SHA-256 de runtime, tareas, fixtures y verificadores.

## Entrega

Los cambios quedan en el árbol de trabajo, revisables y sin commit ni publicación.
No se declara resuelta la fiabilidad general ni se extrapola una ejecución pequeña
a repositorios grandes. Interfaz visual, nuevos ecosistemas y presupuesto dinámico
siguen fuera de este hito.
