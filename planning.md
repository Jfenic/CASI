# Fases del proyecto CASI

## Estado actual

- Fase 0: completada en lo esencial; el proyecto tiene empaquetado, CI, tests y documentación.
- Fase 1: completada en lo esencial; el acceso seguro al repositorio está implementado y cubierto por tests.
- Fase 2: completada para las herramientas de lectura y búsqueda.
- Fase 3: completada para Ollama y respuestas estructuradas.
- Fase 4: completada para el loop básico de solo lectura y el comando `casi run`.
- CLI interactiva: primera versión completada con comandos de sesión y tareas acotadas.
- Próximo bloque: herramientas de tests, Git y validación de parches.
- `validate_patch` ya está implementado; la aplicación de cambios sigue pendiente de aprobación humana.
- `apply_patch` ya está implementado con `dry_run` por defecto; falta conectarlo a una confirmación de la CLI interactiva.

El proyecto se desarrollará de forma incremental. Cada fase debe dejar una parte **funcional, probada y documentada** antes de avanzar.

La regla será:

> No pasar a la fase siguiente hasta que la actual tenga tests y un criterio de finalización verificable.

---

# Fase 0 — Preparación profesional del proyecto

## Objetivo

Preparar el repositorio, las herramientas de desarrollo y la estructura base.

## Debe incluir

```text
pyproject.toml
README.md
LICENSE
.gitignore
.env.example
Makefile
.github/workflows/ci.yml
src/casi/
tests/
docs/
```

## Configuración necesaria

* Python 3.12 o superior.
* Entorno virtual.
* Pytest.
* Ruff.
* Comprobación de tipos con mypy o Pyright.
* Git.
* Integración continua con GitHub Actions.

## Archivos principales

```text
src/casi/
├── __init__.py
├── config.py
└── exceptions.py
```

## Resultado esperado

Deben funcionar:

```bash
pytest
ruff check .
ruff format --check .
```

## Criterio de finalización

* El paquete se puede importar.
* Los tests se ejecutan.
* Git ignora archivos temporales.
* GitHub Actions está configurado.
* El README describe el objetivo de CASI.

---

# Fase 1 — Acceso seguro al repositorio

## Objetivo

Permitir que CASI examine un repositorio sin acceder a rutas externas ni archivos sensibles.

Esta es la fase en la que estás ahora.

## Carpeta

```text
src/casi/repository/
├── __init__.py
├── security.py
├── explorer.py
├── reader.py
└── search.py
```

## `security.py`

Debe implementar:

```python
resolve_repository()
safe_path()
is_sensitive_path()
```

Debe bloquear:

```text
../
.git/
.env
.ssh/
*.pem
*.key
credentials.json
secrets.json
```

También debe detectar enlaces simbólicos que apunten fuera del repositorio.

## `explorer.py`

Debe implementar:

```python
list_files()
```

Debe:

* Recorrer el repositorio.
* Devolver rutas relativas.
* Ignorar directorios innecesarios.
* Omitir archivos sensibles.
* Limitar el número de resultados.

Directorios ignorados:

```text
.git
.venv
node_modules
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
dist
build
```

## `reader.py`

Debe implementar:

```python
read_file()
```

Debe:

* Validar la ruta con `safe_path()`.
* Leer únicamente archivos de texto.
* Limitar el tamaño.
* Permitir seleccionar un rango de líneas.
* Incluir números de línea.

## `search.py`

Debe implementar:

```python
search_code()
```

Debe devolver:

```python
@dataclass(frozen=True)
class SearchResult:
    path: str
    line_number: int
    line: str
```

## Tests necesarios

```text
test_repository_does_not_exist
test_repository_is_not_directory
test_path_traversal_is_blocked
test_sensitive_file_is_blocked
test_symbolic_link_outside_repository_is_blocked
test_git_directory_is_ignored
test_file_limit_is_respected
test_reader_adds_line_numbers
test_binary_file_is_rejected
test_search_returns_path_and_line
```

## Resultado esperado

CASI debe poder:

```bash
casi inspect --repo .
casi read --repo . --file README.md
casi search --repo . --query safe_path
```

## Criterio de finalización

* Puede listar archivos.
* Puede buscar código.
* Puede leer rangos de líneas.
* No puede salir del repositorio.
* No muestra archivos sensibles.
* Todos los tests pasan.

---

# Fase 2 — Sistema de herramientas

## Objetivo

Convertir las funciones anteriores en herramientas estructuradas que posteriormente podrá utilizar el LLM.

## Carpeta

```text
src/casi/tools/
├── __init__.py
├── base.py
├── registry.py
├── file_tools.py
├── search_tools.py
└── result.py
```

## Herramientas iniciales

```text
list_files
read_file
search_code
```

Posteriormente se añadirán:

```text
run_tests
git_diff
validate_patch
apply_patch
```

## Modelo base

Cada herramienta tendrá:

* Nombre.
* Descripción.
* Esquema de argumentos.
* Método de ejecución.
* Resultado estructurado.

Ejemplo:

```python
class ToolResult:
    success: bool
    output: str
    error: str | None
    metadata: dict[str, object]
```

## Registro de herramientas

El registro será el único lugar desde el que se podrán ejecutar herramientas:

```python
tool_registry.execute(
    name="read_file",
    arguments={
        "path": "src/app.py",
        "start_line": 1,
        "end_line": 100,
    },
)
```

El agente no podrá ejecutar funciones que no estén registradas.

## Criterio de finalización

* Las tres herramientas funcionan sin LLM.
* Los argumentos se validan.
* Las herramientas desconocidas se rechazan.
* Los errores se devuelven de manera estructurada.
* Cada herramienta tiene tests unitarios.

---

# Fase 3 — Integración con el modelo local

## Objetivo

Conectar CASI con un LLM local mediante Ollama.

## Carpeta

```text
src/casi/llm/
├── __init__.py
├── base.py
├── models.py
├── ollama_client.py
├── prompts.py
└── parser.py
```

## `base.py`

Define una interfaz independiente de Ollama:

```python
class LLMClient(Protocol):
    def generate_action(
        self,
        messages: list[Message],
    ) -> AgentAction:
        ...
```

## `ollama_client.py`

Debe encargarse de:

* Enviar peticiones HTTP.
* Seleccionar el modelo.
* Configurar la temperatura.
* Gestionar timeouts.
* Detectar errores de conexión.
* Solicitar una salida JSON estructurada.

## Acción esperada

```json
{
  "summary": "I need to locate the validation function.",
  "action": "search_code",
  "arguments": {
    "query": "validate_email"
  }
}
```

## `parser.py`

Debe comprobar:

* Que la respuesta es JSON válido.
* Que la acción está permitida.
* Que los argumentos son correctos.
* Que no faltan campos obligatorios.

## Tests necesarios

Los tests no deben requerir Ollama. Utiliza un cliente falso o respuestas simuladas.

```text
test_valid_action_is_parsed
test_invalid_json_is_rejected
test_unknown_tool_is_rejected
test_missing_arguments_are_rejected
test_ollama_timeout_is_handled
```

## Criterio de finalización

* CASI puede enviar una petición a Ollama.
* El modelo devuelve una acción estructurada.
* Las respuestas inválidas se rechazan.
* El proveedor puede sustituirse por un cliente falso.
* Los tests no dependen de un modelo real.

---

# Fase 4 — Bucle del agente

## Objetivo

Permitir que el modelo utilice varias herramientas consecutivamente para resolver una tarea.

## Carpeta

```text
src/casi/agent/
├── __init__.py
├── state.py
├── loop.py
├── executor.py
└── policies.py
```

## Flujo

```text
User task
   ↓
Model selects an action
   ↓
CASI validates the action
   ↓
CASI executes the tool
   ↓
Tool result is returned to the model
   ↓
The model selects the next action
```

## Estado del agente

Debe guardar:

```python
class AgentState:
    task: str
    repository: Path
    current_step: int
    files_read: set[str]
    actions: list[ActionRecord]
    test_results: list[TestResult]
    proposed_patch: str | None
```

## Políticas iniciales

* Máximo de pasos.
* Máximo de archivos leídos.
* Máximo de caracteres por herramienta.
* Bloqueo de acciones desconocidas.
* Detección de repeticiones.
* Timeout global.
* Finalización explícita.

## Primera capacidad del agente

La primera tarea debe ser exclusivamente de lectura:

> Explain where user email validation is implemented.

CASI deberá:

1. Listar o buscar archivos.
2. Encontrar la función.
3. Leer el código.
4. Dar una respuesta basada en información real.

## Criterio de finalización

* Puede completar tareas de análisis sin modificar código.
* Registra todos los pasos.
* Respeta el límite máximo de acciones.
* No inventa resultados de herramientas.
* Puede ejecutarse con un cliente LLM falso en tests.

---

# Fase 5 — Parches y modificaciones de código

## Objetivo

Permitir que CASI proponga cambios revisables sin sobrescribir directamente los archivos.

## Carpeta

```text
src/casi/patching/
├── __init__.py
├── models.py
├── parser.py
├── validator.py
└── applier.py
```

## Formato de cambio

El modelo debe generar un diff unificado:

```diff
--- a/src/users.py
+++ b/src/users.py
@@ -10,4 +10,7 @@
 def validate_email(email: str) -> bool:
-    return bool(email)
+    if "@" not in email:
+        return False
+    return True
```

## Validaciones necesarias

* El diff tiene formato válido.
* No utiliza rutas absolutas.
* No modifica archivos sensibles.
* No modifica demasiados archivos.
* No sale del repositorio.
* Los archivos afectados existen o se crean de forma permitida.
* Git puede aplicar el parche.

Validación:

```bash
git apply --check patch.diff
```

## Human-in-the-loop

El flujo será:

```text
CASI proposes patch
       ↓
Patch is validated
       ↓
User sees the diff
       ↓
User approves or rejects
       ↓
Patch is applied
```

CASI no debe aplicar automáticamente el parche por defecto.

## Criterio de finalización

* Genera un diff válido.
* Rechaza parches peligrosos.
* Muestra los archivos modificados.
* Permite aprobar o rechazar.
* Puede revertir el cambio.
* No realiza commits automáticamente.

---

# Fase 6 — Ejecución de tests

## Objetivo

Verificar automáticamente que los cambios funcionan.

Esta fase se divide en dos partes.

## Fase 6A — Ejecutor local

### Carpeta

```text
src/casi/sandbox/
├── __init__.py
├── base.py
└── local_runner.py
```

### Debe permitir

```text
python -m pytest -q
```

Con:

* `shell=False`.
* Timeout.
* Directorio de trabajo controlado.
* Captura de salida.
* Límite del tamaño de salida.
* Lista de comandos permitidos.

### Resultado estructurado

```python
class TestResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
```

## Fase 6B — Sandbox Docker

### Archivos

```text
src/casi/sandbox/docker_runner.py
docker/sandbox.Dockerfile
docker/entrypoint.sh
```

### Restricciones

* Contenedor temporal.
* Sin red.
* Usuario no root.
* CPU limitada.
* Memoria limitada.
* Timeout.
* Repositorio copiado a un entorno aislado.
* Sin acceso al directorio personal.
* Eliminación del contenedor al terminar.

## Ciclo de corrección

```text
Generate patch
    ↓
Apply it to a temporary copy
    ↓
Run tests
    ↓
Tests fail
    ↓
Return the failure to the model
    ↓
Generate a corrected patch
```

Inicialmente, permite un máximo de dos intentos de corrección.

## Criterio de finalización

* Ejecuta Pytest con timeout.
* Los resultados se almacenan.
* Los tests se ejecutan sobre una copia.
* Un fallo no daña el proyecto original.
* Docker funciona sin red y con recursos limitados.

---

# Fase 7 — CLI profesional

## Objetivo

Permitir utilizar todas las funciones de CASI desde la terminal.

## Archivo

```text
src/casi/cli.py
```

## Comandos recomendados

```bash
casi inspect --repo ./project

casi read \
  --repo ./project \
  --file src/users.py

casi search \
  --repo ./project \
  --query validate_email

casi ask \
  --repo ./project \
  --task "Explain the user validation flow"

casi fix \
  --repo ./project \
  --task "Reject invalid email addresses and add tests"

casi test --repo ./project
```

## Debe incluir

* Ayuda con `--help`.
* Mensajes de error claros.
* Códigos de salida correctos.
* Modo verbose.
* Confirmación antes de aplicar cambios.
* Posibilidad de guardar el patch.

## Criterio de finalización

Una persona puede instalar CASI y utilizar el flujo completo sin editar código Python manualmente.

---

# Fase 8 — API con FastAPI

## Objetivo

Exponer CASI como un servicio que pueda consumir una interfaz web o una extensión.

## Carpeta

```text
src/casi/api/
├── __init__.py
├── app.py
├── routes.py
├── schemas.py
└── dependencies.py
```

## Endpoints iniciales

```text
GET  /health
POST /tasks
GET  /tasks/{task_id}
POST /tasks/{task_id}/approve
POST /tasks/{task_id}/reject
```

## Estado de una tarea

```text
pending
running
patch_proposed
awaiting_approval
completed
failed
cancelled
```

## No incluir todavía

* Autenticación completa.
* Varios usuarios.
* Facturación.
* Kubernetes.
* Microservicios.
* Frontend complejo.

## Criterio de finalización

* Swagger permite ejecutar una tarea.
* Puede consultar el estado.
* Puede aprobar o rechazar un parche.
* Los errores HTTP son coherentes.
* La API no contiene lógica interna del agente.

---

# Fase 9 — Observabilidad

## Objetivo

Comprender qué hace el agente y detectar por qué falla.

## Carpeta

```text
src/casi/observability/
├── __init__.py
├── logging.py
├── metrics.py
└── tracing.py
```

## Información que debe registrarse

* ID de ejecución.
* Modelo utilizado.
* Acción seleccionada.
* Herramienta ejecutada.
* Duración por paso.
* Archivos leídos.
* Parches generados.
* Resultado de tests.
* Errores.
* Número total de pasos.
* Uso de tokens, cuando esté disponible.

## No registrar

* Contenido de `.env`.
* Claves.
* Tokens.
* Credenciales.
* Código completo si no es necesario.

## Criterio de finalización

Puedes reconstruir una ejecución y saber:

* Qué decidió el modelo.
* Qué herramienta utilizó.
* Qué resultado recibió.
* En qué paso falló.
* Cuánto tardó.

---

# Fase 10 — Evaluación y benchmark

## Objetivo

Demostrar de manera objetiva que CASI funciona.

## Carpetas

```text
benchmarks/
├── tasks/
├── repositories/
└── expected_results/

src/casi/evaluation/
├── __init__.py
├── runner.py
├── metrics.py
└── report.py
```

## Cada tarea debe definir

```yaml
id: task_001
name: invalid_email_validation
repository: invalid_email_app
instruction: >
  Reject email addresses without an @ character and add tests.
success_command:
  - python
  - -m
  - pytest
  - -q
max_steps: 12
```

## Métricas

* Task success rate.
* Patch validity rate.
* Test pass rate.
* Tiempo medio.
* Número medio de pasos.
* Archivos leídos.
* Intentos de corrección.
* Acciones bloqueadas.
* Errores de formato.
* Consumo de memoria.

## Comparación

Ejecuta las mismas tareas con varios modelos locales.

```text
Model A
Model B
Model C
```

## Criterio de finalización

CASI dispone de al menos 20 tareas reproducibles y genera un informe automático con resultados reales.

---

# Fase 11 — Interfaz visual

## Objetivo

Facilitar la revisión de pasos, cambios y resultados.

## Funciones recomendadas

* Seleccionar un repositorio.
* Escribir una tarea.
* Ver los pasos del agente.
* Mostrar los archivos leídos.
* Visualizar el diff.
* Mostrar los tests.
* Aprobar o rechazar cambios.
* Consultar ejecuciones anteriores.

Puedes empezar con Streamlit y, si el proyecto lo necesita, migrar después a React o Next.js.

## Criterio de finalización

Una persona no técnica puede ejecutar una tarea, revisar el cambio y aprobarlo sin utilizar la terminal.

---

# Resumen de fases

| Fase | Objetivo principal               | Resultado                  |
| ---: | -------------------------------- | -------------------------- |
|    0 | Preparar el proyecto             | Repositorio profesional    |
|    1 | Acceder al código con seguridad  | Explorador de repositorios |
|    2 | Crear herramientas estructuradas | Tool registry              |
|    3 | Conectar el modelo local         | Cliente Ollama             |
|    4 | Coordinar decisiones             | Agente de solo lectura     |
|    5 | Proponer modificaciones          | Parches verificables       |
|    6 | Comprobar cambios                | Tests en sandbox           |
|    7 | Usar CASI desde terminal         | CLI completa               |
|    8 | Exponer el sistema               | API FastAPI                |
|    9 | Observar ejecuciones             | Logs, métricas y trazas    |
|   10 | Medir calidad                    | Benchmark profesional      |
|   11 | Mejorar experiencia              | Interfaz visual            |

# MVP que deberías presentar

El MVP puede darse por terminado al completar las fases **0 a 7**.

Debe ser capaz de:

```text
1. Open a Python repository.
2. Inspect and search its source code.
3. Ask a local LLM for structured actions.
4. Execute only approved tools.
5. Generate a unified diff.
6. Validate the patch.
7. Run Pytest in an isolated copy.
8. Show the patch and test result.
9. Ask for approval before modifying the repository.
```

El siguiente bloque de implementación debe concentrarse en las herramientas de desarrollo y parches, después de haber completado la cobertura de la **Fase 1**:

```text
security.py
test_security.py
explorer.py
test_explorer.py
reader.py
test_reader.py
search.py
test_search.py
```
