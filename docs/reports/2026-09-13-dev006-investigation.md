# Investigación de dev_006 — 2026-09-13

## Dos modos de fallo

La ejecución de la suite completa terminó sin parche: la herramienta recibió
`propose_file` con `path='settings.py'`, pero sin `content`. Después del rechazo,
el modelo produjo cuatro respuestas explicativas y agotó los recordatorios.
La traza conserva la llamada interpretada y su rechazo, no el cuerpo HTTP bruto;
no permite afirmar si el contenido estaba ausente o mal ubicado en el JSON original.

El prompt global decía que, tras recibir resultados de herramientas, debía resumir
en una respuesta final. Eso entra en conflicto con las instrucciones de reparación,
que requieren proponer contenido. Es una contradicción real del prompt y una
hipótesis de contribución al fallo, no una causalidad demostrada por la traza.

La primera intervención corrigió esa contradicción y añadió al recordatorio de
error la forma JSON completa, conservando la ruta. Tres ejecuciones dieron **0/3**:
una sin propuesta y dos con propuestas que no cumplían la independencia de objetos.

En esas propuestas, el modelo confundió fusión recursiva con copia profunda.
Devolvía directamente valores de las entradas en ramas de reemplazo o claves
presentes solo en una entrada. Eso puede pasar los tests visibles y, aun así,
modificar las entradas cuando alguien muta una lista anidada del resultado.

## Corrección

- El prompt diferencia terminar una consulta de lectura de completar una reparación.
- Un rechazo de `propose_file` pide corregir los argumentos y muestra una llamada
  JSON con `path` y `content` dentro de `arguments`.
- Se añade un ejemplo general de propuesta de archivo completo.
- El contrato de copia independiente explica que no mutar durante la llamada no
  basta: también deben ser independientes las ramas retenidas y reemplazadas.
  La guía indica `copy.deepcopy` para esos valores, incluidas claves de una sola
  entrada y listas anidadas.

La guía es condicional al contrato del usuario; no cambia la semántica de tareas
que permiten compartir referencias. No se modifica el fixture `settings.py`, el
enunciado, los verificadores, los límites de pasos ni las soluciones de referencia.
No se proporciona al modelo el código de los verificadores ocultos.

## Validación

Una regresión simula `propose_file` sin `content`, comprueba el recordatorio,
continúa con una propuesta válida y exige tests aprobados sobre la copia aislada.
Comprueba además que el archivo original permanece intacto. La regresión anterior
de aceptación independiente sigue detectando alias en valores de overrides.

- Suite completa tras el cambio del loop y la primera corrección del prompt:
  **370 passed, 2 skipped, 2 warnings**, 93,23 s; Docker y API incluidos.
- Tras ampliar las instrucciones y el ejemplo: cliente Ollama **13 passed**;
  Ruff, formato (201 archivos), compilación y `git diff --check` correctos.
- Los avisos son de Starlette/httpx y AnyIO; los omitidos son el fixture opt-in
  Ollama y la rama de Docker ausente.
- Los intentos iniciales dentro del entorno restringido no accedieron a Docker/
  Ollama; se repitieron con acceso a ambos servicios. No se contabilizan como
  fallos del modelo.

<!-- final-measurement -->

## Evidencia y reproducción

Primera intervención: informes `2026-09-13-dev006-recovery-{1,2,3}.json/.md` y
sus artefactos. Segunda intervención: `2026-09-13-dev006-copy-contract-{1,2,3}`.
Los manifiestos correspondientes guardan hashes de runtime y materiales de la suite.
Son tres ejecuciones independientes de la misma tarea con `qwen3.5:4b`, sin cambios
entre repeticiones; el evaluador conserva respuestas, parches y aceptación por caso.

Para repetir desde la raíz usando el entorno `.venv`, ejecutar este código Python
con Docker y Ollama disponibles. Usar un nombre nuevo para conservar los informes:

```python
from pathlib import Path
from casi.evaluation.benchmark import load_tasks
from casi.evaluation.runner import BenchmarkRunOptions, run_model_benchmark
from casi.evaluation.report import (
    build_report_payload, render_markdown_report, write_report_files,
)
from casi.llm.ollama_client import OllamaClient

tasks = [t for t in load_tasks(Path("benchmarks/development/tasks"))
         if t.task_id == "dev_006"]
for attempt in range(1, 4):
    output = Path(f"/tmp/dev006-repeat-{attempt}.json")
    run = run_model_benchmark(
        tasks, client=OllamaClient(model="qwen3.5:4b"),
        options=BenchmarkRunOptions(
            repositories_root=Path("benchmarks/development/repositories"),
            artifacts_dir=output.with_suffix("").with_name(output.stem + "-artifacts"),
        ),
    )
    write_report_files(
        build_report_payload(run.results, model=run.model), output,
        markdown=render_markdown_report(run.results, model=run.model),
    )
```

Los resultados dirigidos no sustituyen una nueva ejecución de las doce tareas.
El benchmark general de desarrollo anterior sigue siendo 7/12 para aquel estado
del runtime. Cambios locales, sin commit ni publicación.
