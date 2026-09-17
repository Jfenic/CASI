"""Human-readable help text for CASI CLI commands."""

from __future__ import annotations

from textwrap import dedent

TOPICS: dict[str, str] = {
    "overview": dedent(
        "        CASI — Code Agent for Software Inspection\n"
        "\n"
        "        CASI inspecciona repositorios locales, propone "
        "parches, ejecuta tests en\n"
        "        sandbox y pide aprobación humana antes de "
        "modificar archivos.\n"
        "\n"
        "        Comandos principales:\n"
        "\n"
        "          inspect       Lista archivos del repositorio "
        "de forma segura\n"
        "          read          Lee un archivo con números de "
        "línea\n"
        "          search        Busca texto dentro del código\n"
        "          run           Ejecuta una tarea puntual con "
        "el agente\n"
        "          ask           Pregunta sobre el repositorio "
        "(alias orientado a lectura)\n"
        "          fix           Pide una corrección o cambio de "
        "código/tests\n"
        "          interactive   Abre una sesión interactiva con "
        "el agente\n"
        "          test          Ejecuta la suite de tests del "
        "repositorio\n"
        "          serve         Inicia la API HTTP (FastAPI + "
        "Swagger)\n"
        "          ui            Abre la interfaz visual Streamlit\n"
        "          benchmark     Ejecuta tareas reproducibles y "
        "genera informes\n"
        "          env prepare   Prepara un entorno Docker con "
        "dependencias del proyecto\n"
        "          help          Muestra esta ayuda o la de un "
        "comando concreto\n"
        "\n"
        "        Ayuda detallada:\n"
        "\n"
        "          casi help inspect\n"
        "          casi help interactive\n"
        "          casi help env\n"
        "\n"
        "        Variables de entorno útiles:\n"
        "\n"
        "          LOCALCODE_AGENT_OLLAMA_MODEL          Modelo "
        "de Ollama (default: qwen2.5-coder:7b)\n"
        "          LOCALCODE_AGENT_USE_DOCKER            Usar "
        "sandbox Docker para tests (default: true)\n"
        "          LOCALCODE_AGENT_ALLOW_LOCAL_FALLBACK  "
        "Permitir ejecución local si Docker falta o falla (default: false)\n"
        "          LOCALCODE_AGENT_DOCKER_PIDS_LIMIT     Límite "
        "de procesos del contenedor (default: 64)\n"
        "          LOCALCODE_AGENT_MAX_CORRECTION_ATTEMPTS "
        "Reintentos tras fallo de tests (default: 4)\n"
        "          LOCALCODE_AGENT_DOCKER_IMAGE          Imagen "
        "sandbox (default: casi-sandbox:latest)\n"
        "\n"
        "        Más información: README.md, planning.md\n"
        "        "
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
          casi run --repo PATH --task "DESCRIPCION"
                       [--max-steps N] [--routing MODO]
                       [-v] [--save-patch PATH] [--yes]

        Opciones:
          --repo PATH       Ruta al repositorio
          --task TEXTO      Tarea para el agente
          --max-steps N     Máximo de decisiones del modelo por agente
          --routing MODO    Enrutamiento del repo: assist, strict u off
          -v, --verbose     Muestra plan y traza detallada en stderr
          --save-patch PATH Guarda el diff propuesto en un archivo
          --yes             Aprueba herramientas y aplica parches sin preguntar

        Códigos de salida:
          0  Éxito (sin parche, parche aplicado o guardado)
          1  Error del agente, parche inválido o tests fallidos
          2  Parche válido mostrado pero no aplicado ni guardado

        Ejemplo:
          casi run --repo . --task "Explica cómo funciona el bucle del agente"
          casi fix --repo . --task "Corrige los tests" --save-patch /tmp/fix.diff
          casi fix --repo . --task "Corrige los tests" --yes

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
          casi ask --repo PATH --task "DESCRIPCION"
                       [--max-steps N] [--routing MODO]
                       [-v] [--save-patch PATH] [--yes]

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
          casi fix --repo PATH --task "DESCRIPCION"
                       [--max-steps N] [--routing MODO]
                       [-v] [--save-patch PATH] [--yes]

        Ejemplo:
          casi fix --repo . --task "Haz que pasen los tests de validate_email"
          casi fix --repo . --task "Corrige el bug" --save-patch fix.diff
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
    "serve": dedent(
        """\
        casi serve — iniciar la API HTTP de CASI

        Expone el agente como servicio REST con documentación Swagger en /docs.
        Las tareas se ejecutan en segundo plano; los parches válidos quedan en
        `awaiting_approval` hasta que los apruebes o rechaces por API.

        Requisitos:
          pip install -e '.[api]'

        Uso:
          casi serve [--host HOST] [--port PUERTO]

        Opciones:
          --host HOST    Dirección de escucha (default: 127.0.0.1)
          --port PUERTO  Puerto HTTP (default: 8000)

        Endpoints:
          GET  /health
          GET  /tasks
          POST /tasks
          GET  /tasks/{task_id}
          POST /tasks/{task_id}/approve
          POST /tasks/{task_id}/reject

        Ejemplo:
          casi serve --host 127.0.0.1 --port 8000
          curl http://127.0.0.1:8000/health
        """
    ),
    "ui": dedent(
        """\
        casi ui — interfaz visual Streamlit

        Abre una interfaz web para crear tareas, revisar pasos del agente,
        inspeccionar parches y aprobar o rechazar cambios sobre la API HTTP.

        Requisitos:
          pip install -e '.[ui]'
          casi serve   # en otra terminal

        Uso:
          casi ui [--host HOST] [--port PUERTO] [--api-url URL]

        Opciones:
          --host HOST      Dirección de Streamlit (default: 127.0.0.1)
          --port PUERTO    Puerto de Streamlit (default: 8501)
          --api-url URL    URL base de la API CASI (default: http://127.0.0.1:8000)

        Variables de entorno:
          CASI_API_URL            URL base de la API
          CASI_UI_POLL_INTERVAL   Segundos entre actualizaciones (default: 1)
          CASI_UI_POLL_TIMEOUT    Tiempo máximo de espera (default: 600)
          CASI_UI_HISTORY_LIMIT   Tareas listadas en el historial (default: 50)

        Ejemplo:
          casi serve --port 8000
          casi ui --api-url http://127.0.0.1:8000
        """
    ),
    "benchmark": dedent(
        "        casi benchmark — ejecutar la suite de "
        "evaluación\n"
        "\n"
        "        Corre tareas reproducibles contra repositorios "
        "de prueba en `benchmarks/`\n"
        "        y genera métricas agregadas. Cada tarea se "
        "ejecuta en una copia aislada;\n"
        "        las tareas de reparación aplican parches "
        "válidos automáticamente antes\n"
        "        de verificar con pytest.\n"
        "\n"
        "        Uso:\n"
        "          casi benchmark [--tasks-dir PATH] "
        "[--repos-dir PATH]\n"
        "                       [--model MODELO | --models "
        "m1,m2]\n"
        "                       [--output informe] [--format "
        "text|json|markdown|both]\n"
        "                       [-v] [--quiet] [--list]\n"
        "\n"
        "        Progreso:\n"
        "          Por defecto muestra en stderr el avance de "
        "cada tarea (id, repo,\n"
        "          categoría, resultado, duración y pasos). Usa "
        "-v para ver también\n"
        "          los pasos del agente; --quiet para ocultar el "
        "progreso.\n"
        "\n"
        "        Ejemplo:\n"
        "          casi benchmark --list\n"
        "          casi benchmark --model qwen2.5-coder:7b "
        "--output /tmp/benchmark.json\n"
        "          casi benchmark --models "
        "qwen2.5-coder:7b,llama3.2 --format both --output report\n"
        "        "
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
    "serve": "serve",
    "api": "serve",
    "ui": "ui",
    "web": "ui",
    "streamlit": "ui",
    "benchmark": "benchmark",
    "benchmarks": "benchmark",
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
        available = ", ".join(name for name in TOPICS if name != "overview")
        return (
            f"Unknown help topic: {topic}\n\n"
            f"Available topics: overview, {available}\n\n"
            "Try: casi help inspect"
        )
    return text.rstrip() + "\n"
