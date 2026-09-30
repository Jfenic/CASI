# Auditoría de instrucciones y heurísticas generalistas

Fecha: 2026-09-30. Alcance: prompts, nudges, perfiles, clasificación,
preparación de contexto y ejecución de tests. Los hallazgos y ubicaciones siguientes
describen la versión auditada antes de las correcciones. La resolución posterior,
autorizada por el usuario, se documenta al final.

Las prioridades siguientes son propuestas de revisión, no cambios aplicados.
Se distinguen recetas de implementación, inferencias sin evidencia suficiente
y límites legítimos del protocolo.

## Prioridad alta: instrucciones que condicionan la solución

| Hallazgo | Ubicación | Riesgo | Alternativa general |
| --- | --- | --- | --- |
| Receta de copia profunda | [prompts.py:109](../../src/casi/llm/prompts.py#L109) | Prescribe `copy.deepcopy` para valores conservados y sustituidos y detalla listas y claves presentes en un solo argumento. Está condicionada a un contrato de copia independiente, pero fija la técnica dentro del prompt global. | Exigir las condiciones de mutabilidad y propiedad de datos del contrato, dejando la técnica al modelo. |
| Ejemplo específico de TTL | [prompts.py:121](../../src/casi/llm/prompts.py#L121) | Introduce «cero expira inmediatamente; negativo lanza ValueError» en todas las tareas. Está condicionado a lo que diga el contrato, pero representa una semántica particular de caché. | Pedir que respete los valores límite definidos por cada tarea, sin ejemplos de otro dominio. |
| Imports y excepciones | [prompts.py:124](../../src/casi/llm/prompts.py#L124) | Recomienda `raise ... from None` y restringe imports a «standard Python built-ins and existing repository modules». Puede desalentar dependencias válidas o cambiar el contexto de excepciones que deba conservarse. | Verificar imports contra el proyecto y su entorno declarado; derivar el comportamiento de excepciones del contrato. |
| Convenciones ML | [profiles.py:259](../../src/casi/agent/profiles.py#L259) | El checklist sugiere `ddof=1`; además, prohíbe siempre mutar entradas, incluso si la API opera sobre ellas por diseño. | Comprobar definiciones estadísticas y condiciones de mutabilidad del proyecto. |
| Causa asumida para `DID NOT RAISE` | [nudges.py:248](../../src/casi/agent/nudges.py#L248) | Afirma que se aceptó una entrada inválida y recomienda restaurar validaciones. También puede faltar propagación de una excepción sin entrada inválida. Esta suposición está en el cambio reciente de diagnóstico general. | Informar de la excepción esperada que no se produjo y aportar el test, valores locales y propuesta rechazada. |
| Ampliación del alcance | [nudges.py:112](../../src/casi/agent/nudges.py#L112) | «Fix every remaining failure» puede arrastrar fallos previos ajenos a la petición o contradecir límites explícitos. | Comparar resultados iniciales y posteriores, corregir regresiones introducidas y respetar el alcance autorizado. |

La receta de copia coincide con el contrato de
[dev_006](../../benchmarks/development/tasks/dev_006.yaml#L7); el ejemplo de TTL,
con [dev_005](../../benchmarks/development/tasks/dev_005.yaml#L7).
Esto demuestra correspondencias concretas, no que el agente consulte los graders
durante la ejecución.

La pista del punto final en [nudges.py:258](../../src/casi/agent/nudges.py#L258)
también trata un caso particular, aunque deriva el valor esperado de la salida
real. Tiene menor riesgo y puede simplificarse a una comparación general de valores.

## Prioridad media: supuestos del flujo de trabajo

### Clasificación por palabras ambiguas

[intent.py:49](../../src/casi/agent/intent.py#L49),
[intent.py:87](../../src/casi/agent/intent.py#L87) e
[intent.py:116](../../src/casi/agent/intent.py#L116) contienen catálogos de palabras:
`model` puede activar metainformación y `feature` o `split` pueden activar ML
sin que la tarea pertenezca a ese dominio.

Resultados locales de `resolve_task_intent`:

| Petición | Resultado |
| --- | --- |
| `Correct the calculation in totals.py` | `unknown` |
| `Fix model.py` | `meta` |
| `Fix feature flags parsing` | `ml` |
| `Fix checkout.py` | `fix` |

El evaluador usa normalmente el LLM cuando está disponible. Estas limitaciones
afectan a rutas deterministas y al fallback de
[evaluator.py:174](../../src/casi/agent/evaluator.py#L174), no prueban que todas las
peticiones se clasifiquen así durante el flujo normal. Conviene respetar categorías
explícitas y elegir una ruta conservadora sin evidencia suficiente del dominio.

### Una lectura se considera contexto suficiente

[loop.py:252](../../src/casi/agent/loop.py#L252) retira herramientas de búsqueda
tras ejecutar tests y leer cualquier archivo: diagnóstico conserva `read_file`;
reparación conserva `read_file` y `propose_file`. Una lectura no acredita conocer
los archivos y dependencias relevantes. Conviene controlar repeticiones y
presupuesto sin retirar la búsqueda únicamente por haber leído un archivo.

### Estructura de repositorio presupuesta

[pipelines.py:200](../../src/casi/agent/pipelines.py#L200) intenta leer siempre
`README.md`. La inferencia de módulos en
[pipelines.py:21](../../src/casi/agent/pipelines.py#L21) busca nombres en la raíz
y consulta paquetes instalados en el proceso anfitrión; puede confundir un paquete
bajo `src/` o una dependencia no instalada allí con un módulo local que crear.

Parte de [pipelines.py:269](../../src/casi/agent/pipelines.py#L269) exige `test_*.py`
y busca en la raíz, mientras
[create_workflow.py:16](../../src/casi/agent/create_workflow.py#L16) también reconoce
`*_test.py`. Conviene descubrir archivos y módulos según la estructura y la
configuración del proyecto, diferenciando dependencias externas de archivos ausentes.

### Historial de herramientas interpretado como texto fijo

[guardrails.py:7](../../src/casi/agent/guardrails.py#L7) y
[conversation.py:51](../../src/casi/agent/conversation.py#L51) solo reconocen una
llamada con el formato exacto `{'path': '...'}`. Se comprobó:

| Argumentos registrados | Lecturas contabilizadas |
| --- | --- |
| `{'path': 'app.py'}` | `{'app.py': 1}` |
| `{'path': 'app.py', 'start_line': 1, 'end_line': 10}` | `{}` |

Conviene usar eventos estructurados de ejecución y sus argumentos, en lugar del
formato textual mostrado al usuario.

### Adaptación a Docker descarta argumentos de tests

[test_command.py:12](../../src/casi/sandbox/test_command.py#L12) sustituye comandos
`python3 -m pytest` por el predeterminado. Se comprobó que el override
`python3 -m pytest -q tests/unit` pasa a ejecutar `/workspace`, perdiendo `tests/unit`.
La comparación `command[:2] == ["pytest"]` tampoco reconoce `pytest -q`.
Conviene adaptar ejecutables y rutas conservando los argumentos configurados.

## Reglas que conviene conservar

- Aprobación humana antes de aplicar cambios y ausencia de `apply_patch` entre las
  herramientas expuestas al modelo.
- Esquemas de acciones, permisos por rol y protección de rutas sensibles.
- Presupuestos y límites configurables, aunque pueda mejorarse cuándo se usan.
- No debilitar tests para ocultar una implementación incorrecta.
- Adaptadores de Python, Pytest y Ollama cuando representan el alcance soportado,
  sin convertirlos en instrucciones sobre la solución del usuario.

## Verificación de la auditoría inicial

Se inspeccionaron fuentes y contratos relevantes y se ejecutaron comprobaciones
locales de clasificación, contabilización de lecturas, mensajes de excepción y
adaptación del comando de tests. No requieren Ollama ni Docker.

No se modificó código de ejecución, tests ni benchmarks, ni se repitió la suite
completa. Esta auditoría no afirma que retirar las recetas mejore la capacidad
del modelo; esa capacidad debe evaluarse por separado.

## Resolución posterior

- Se eliminaron las recetas de copia profunda, TTL y contexto de excepciones del
  prompt global. Imports, mutabilidad y convenciones numéricas se derivan del
  contrato y del repositorio.
- Los nudges informan de excepciones esperadas y diferencias entre valores sin
  atribuir causas no demostradas. Los mensajes de imports y timeouts piden
  investigar el código y el entorno antes de proponer una corrección.
- Se retiró la instrucción de corregir todos los fallos fuera del alcance pedido.
  El agente sigue verificando las propuestas y no debilita tests ni rubricas.
- El fallback deja de asignar ML por palabras del dominio. Las preguntas sobre el
  agente requieren formulaciones explícitas; los nombres de archivos ya no activan
  metainformación solo por contener `model`. Se preservan rutas con guiones bajos.
- La búsqueda y los tests permanecen disponibles después de leer archivos. Se
  redirigen búsquedas idénticas ya ejecutadas, sin impedir consultas distintas.
  Los nudges de diagnóstico respetan su rol de solo lectura.
- Las ejecuciones registran argumentos y resultado en datos estructurados. Los
  rangos de lectura se contabilizan; las llamadas descritas por el modelo y las
  lecturas fallidas no acreditan haber cargado un archivo.
- La vista general elige un README existente. La preparación comparte detección
  de tests con nombres y directorios configurados, resuelve imports relativos y
  raíces declaradas por Pytest, setuptools o Hatch, además de raíces existentes
  habituales. Un import desconocido no se convierte en una orden de crear código;
  esa indicación exige un archivo local nombrado en la tarea.
- Docker conserva opciones, selección de tests y node IDs del comando configurado;
  adapta el intérprete y las rutas absolutas dentro del repositorio.

Se conservan los permisos por rol, aprobación humana, validación de parches y
presupuestos. El alcance soportado sigue siendo Python y Pytest. No se modificaron
los benchmarks ni se ejecutó una nueva medición con Ollama; retirar las recetas
no demuestra que el modelo sea capaz de resolver la demo.

Validación final: `uv run --no-sync pytest -ra` termina con **561 tests pasando,
2 omitidos y 2 avisos de dependencias** (Starlette/AnyIO). Ruff, comprobación de
formato y `compileall` pasan. Las regresiones son deterministas y no requieren
un servidor Ollama.
