"""Human-readable help text for CASI CLI commands."""

from __future__ import annotations

from textwrap import dedent

TOPICS: dict[str, str] = {
	"overview": dedent(
		"""\
		CASI — Code Agent for Software Inspection

		CASI inspecciona repositorios locales, propone parches, ejecuta tests en
		sandbox y pide aprobación humana antes de modificar archivos.

		Comandos principales:

		  inspect       Lista archivos del repositorio de forma segura
		  read          Lee un archivo con números de línea
		  search        Busca texto dentro del código
		  run           Ejecuta una tarea puntual con el agente
		  ask           Pregunta sobre el repositorio (alias orientado a lectura)
		  fix           Pide una corrección o cambio de código/tests
		  interactive   Abre una sesión interactiva con el agente
		  test          Ejecuta la suite de tests del repositorio
		  env prepare   Prepara un entorno Docker con dependencias del proyecto
		  help          Muestra esta ayuda o la de un comando concreto

		Ayuda detallada:

		  casi help inspect
		  casi help interactive
		  casi help env

		Variables de entorno útiles:

		  LOCALCODE_AGENT_OLLAMA_MODEL          Modelo de Ollama (default: qwen2.5-coder:7b)
		  LOCALCODE_AGENT_USE_DOCKER            Usar sandbox Docker para tests (default: true)
		  LOCALCODE_AGENT_ALLOW_LOCAL_FALLBACK  Permitir fallback local si Docker falla (default: true)
		  LOCALCODE_AGENT_DOCKER_PIDS_LIMIT     Límite de procesos del contenedor (default: 64)
		  LOCALCODE_AGENT_MAX_CORRECTION_ATTEMPTS Reintentos tras fallo de tests (default: 2)
		  LOCALCODE_AGENT_DOCKER_IMAGE          Imagen sandbox (default: casi-sandbox:latest)

		Más información: README.md, planning.md
		"""
	),
	"inspect": dedent(
		"""\
		casi inspect — listar archivos del repositorio

		Recorre el repositorio y muestra rutas relativas, omitiendo directorios
		innecesarios (.git, .venv, __pycache__, etc.) y archivos sensibles.

		Uso:
		  casi inspect --repo PATH

		Opciones:
		  --repo PATH    Ruta al repositorio a inspeccionar

		Ejemplo:
		  casi inspect --repo .
		"""
	),
	"read": dedent(
		"""\
		casi read — leer un archivo del repositorio

		Lee un archivo de texto de forma segura, con números de línea y límites
		de tamaño. Rechaza rutas fuera del repo y archivos binarios.

		Uso:
		  casi read --repo PATH --file RUTA [--start-line N] [--end-line N]

		Opciones:
		  --repo PATH         Ruta al repositorio
		  --file RUTA         Archivo relativo dentro del repositorio
		  --start-line N      Primera línea a leer (default: 1)
		  --end-line N        Última línea a leer (default: 300)

		Ejemplo:
		  casi read --repo . --file README.md
		  casi read --repo . --file src/casi/cli.py --start-line 1 --end-line 80
		"""
	),
	"search": dedent(
		"""\
		casi search — buscar texto en el repositorio

		Busca una cadena en los archivos de texto del repositorio y muestra
		ruta, número de línea y contenido de cada coincidencia.

		Uso:
		  casi search --repo PATH --query TEXTO [--limit N]

		Opciones:
		  --repo PATH    Ruta al repositorio
		  --query TEXTO  Texto a buscar
		  --limit N      Máximo de resultados (default: configuración del proyecto)

		Ejemplo:
		  casi search --repo . --query "propose_file"
		"""
	),
	"run": dedent(
		"""\
		casi run — ejecutar una tarea con el agente

		Envía una tarea al agente local (Ollama), que puede usar herramientas
		de lectura y ejecución controlada. Si propone cambios, genera un diff,
		valida el parche, ejecuta tests en una copia aislada y pide tu
		aprobación antes de escribir en disco.

		Uso:
		  casi run --repo PATH --task "DESCRIPCION" [--max-steps N] [--routing MODO]

		Opciones:
		  --repo PATH       Ruta al repositorio
		  --task TEXTO      Tarea para el agente
		  --max-steps N     Máximo de decisiones del modelo por agente
		  --routing MODO    Enrutamiento del repo: assist, strict u off

		Ejemplo:
		  casi run --repo . --task "Explica cómo funciona el bucle del agente"
		  casi run --repo ./app --task "Corrige los tests que fallan"

		Nota:
		  Para varias tareas seguidas con contexto conversacional, usa
		  `casi interactive`.
		"""
	),
	"ask": dedent(
		"""\
		casi ask — preguntar sobre el repositorio

		Alias de `casi run` orientado a inspección y explicación. Usa las mismas
		opciones y el mismo agente; confirma `run_tests` solo si el modelo lo pide.

		Uso:
		  casi ask --repo PATH --task "DESCRIPCION" [--max-steps N] [--routing MODO]

		Ejemplo:
		  casi ask --repo . --task "Explica el flujo de validación de email"
		"""
	),
	"fix": dedent(
		"""\
		casi fix — corregir código o tests

		Alias de `casi run` orientado a reparaciones. El agente puede inspeccionar,
		ejecutar tests (con confirmación) y proponer parches con `propose_file`.

		Uso:
		  casi fix --repo PATH --task "DESCRIPCION" [--max-steps N] [--routing MODO]

		Ejemplo:
		  casi fix --repo . --task "Haz que pasen los tests de validate_email"
		"""
	),
	"interactive": dedent(
		"""\
		casi interactive — sesión interactiva con el agente

		Abre un bucle REPL donde puedes hacer varias peticiones conservando
		contexto hasta que uses /clear.

		Uso:
		  casi interactive --repo PATH [--max-steps N] [--routing MODO]

		Opciones:
		  --repo PATH       Ruta al repositorio
		  --max-steps N     Máximo de decisiones del modelo por agente
		  --routing MODO    Enrutamiento del repo: assist, strict u off

		Alias compatible:
		  casi run interactive --repo PATH

		Ejemplo:
		  casi interactive --repo .

		Comandos dentro de la sesión:

		  /help            Lista comandos de la sesión
		  /history         Muestra tareas de esta sesión
		  /context         Muestra el hilo enviado al modelo
		  /compact [texto] Resume contexto antiguo
		  /clear           Borra historial y contexto conversacional
		  /trace [on|off]  Activa trazas en vivo del agente
		  /last-trace      Muestra la traza del último intento
		  /save-trace PATH Exporta la última traza como JSON
		  /plan            Muestra el plan actual o el último generado
		  /cancel          Cancela una tarea pendiente de clarificación
		  /exit            Sale del modo interactivo

		Flujo típico de corrección:
		  CASI> /trace on
		  CASI> corrige los tests que fallan
		  CASI> /last-trace

		Si el agente pide aclaración, responde en el prompt Answer>.
		Usa /plan para revisar el plan o /cancel para descartarlo.
		"""
	),
	"test": dedent(
		"""\
		casi test — ejecutar tests del repositorio

		Ejecuta pytest sobre el repositorio con timeout y captura de salida.
		Preferirá Docker (entorno del proyecto o casi-sandbox:latest) y hará
		fallback a ejecución local si Docker no está disponible.

		Uso:
		  casi test --repo PATH [--timeout SEGUNDOS]

		Opciones:
		  --repo PATH          Ruta al repositorio
		  --timeout SEGUNDOS   Tiempo máximo de ejecución (default: configuración)

		Ejemplo:
		  casi test --repo .

		Proyectos con dependencias externas:
		  casi env prepare --repo PATH
		  casi test --repo PATH
		"""
	),
	"env": dedent(
		"""\
		casi env — gestionar entornos de test del proyecto

		Subcomandos:

		  prepare   Construye una imagen Docker cacheada con las dependencias
		            del proyecto para ejecutar tests sin red posteriormente.

		Uso:
		  casi env prepare --repo PATH [--yes]

		Opciones de prepare:
		  --repo PATH    Ruta al repositorio
		  --yes          Aprobar la descarga de dependencias sin preguntar

		Detecta: uv.lock, poetry.lock, requirements.txt, requirements-dev.txt
		y pyproject.toml. El nombre de la imagen incluye un hash de esos ficheros.

		Ejemplo:
		  casi env prepare --repo ./mi-proyecto
		  casi test --repo ./mi-proyecto
		"""
	),
}

TOPIC_ALIASES: dict[str, str] = {
	"overview": "overview",
	"commands": "overview",
	"all": "overview",
	"inspect": "inspect",
	"read": "read",
	"search": "search",
	"run": "run",
	"ask": "ask",
	"fix": "fix",
	"interactive": "interactive",
	"repl": "interactive",
	"test": "test",
	"tests": "test",
	"env": "env",
	"environment": "env",
	"prepare": "env",
}


def resolve_topic(topic: str | None) -> str:
	"""Return the canonical topic key for a user-provided name."""

	if topic is None or not topic.strip():
		return "overview"
	normalized = topic.strip().lower()
	return TOPIC_ALIASES.get(normalized, normalized)


def format_help(topic: str | None = None) -> str:
	"""Return formatted help text for a topic or the command overview."""

	key = resolve_topic(topic)
	text = TOPICS.get(key)
	if text is None:
		available = ", ".join(
			name for name in TOPICS if name != "overview"
		)
		return (
			f"Unknown help topic: {topic}\n\n"
			f"Available topics: overview, {available}\n\n"
			"Try: casi help inspect"
		)
	return text.rstrip() + "\n"
