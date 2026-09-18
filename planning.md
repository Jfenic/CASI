# Fases del proyecto CASI

> **Trabajo activo:** [TASKS.md](TASKS.md)  
> **Arquitectura:** [ARCHITECTURE.md](ARCHITECTURE.md)  
> **Instrucciones para agentes:** [AGENTS.md](AGENTS.md)

Este documento resume la evolución por fases del proyecto CASI, el estado de cada una y las líneas de trabajo futuras.

---

## Resumen de fases

| Fase | Objetivo principal | Estado | Resultado clave |
| ---: | ------------------ | :---: | --------------- |
| 0 | Preparación profesional | ✅ Completada | Estructura base, CI, Ruff, Pytest, config |
| 1 | Acceso seguro al repositorio | ✅ Completada | Explorador, reader y buscador seguros (`safe_path`, bloqueo de rutas sensibles) |
| 2 | Sistema de herramientas | ✅ Completada | Tool registry estructurado, validación de argumentos y permisos |
| 3 | Integración con modelo local | ✅ Completada | Cliente Ollama, protocolos JSON estructurados y parser tolerante |
| 4 | Bucle del agente | ✅ Completada | `AgentLoop` acotado, políticas de ejecución, trazas y finalización explícita |
| 5 | Parches y modificaciones | ✅ Completada | `propose_file`, diffs unificados, validación Git y aprobación humana obligatoria |
| 6 | Sandbox de ejecución de tests | ✅ Completada | `DockerRunner` sin red sobre copia temporal aislada, ciclo patch → test → retry |
| 7 | CLI profesional | ✅ Completada | Comandos `inspect`, `run`, `ask`, `fix`, `test`, `interactive`, `--save-patch`, `--yes` |
| 8 | API con FastAPI | ✅ Completada | Ciclo de vida de tareas, endpoints de aprobación/rechazo y `casi serve` |
| 9 | Observabilidad | ✅ Completada | Trazas de ejecución JSON v2, métricas agregadas y tiempos por paso |
| 10 | Evaluación y benchmarks | ✅ Completada | Suites reproducibles (general, dev, ml, diagnosis, fundamentals, security) |
| 11 | Interfaz visual | ✅ Completada | UI Streamlit (`casi ui`) modular sobre la API con historial, trazas y aprobación |
| 12 | Fiabilidad y protocol enforcement | ✅ Completada | Máquina de estados (`AgentPhase`), esquema `ProposeFileAction`, fallback parser; 9/12 en dev benchmark |

---

## Hito MVP (Fases 0 a 7)

El MVP de CASI quedó consolidado con las siguientes garantías:
1. Inspección y búsqueda segura sin escapar del repositorio ni leer secretos.
2. Generación estructurada de acciones mediante modelos LLM locales (Ollama).
3. Modificaciones exclusivamente en formato diff unificado vía `propose_file` (`apply_patch` nunca está al alcance del modelo).
4. Ejecución de tests en contenedor Docker sin red sobre una copia temporal aislada.
5. Confirmación humana explícita previa a cualquier modificación sobre el repositorio de trabajo.

---

## Extensiones Recientes (Fases 8 a 12)

- **API y UI (Fases 8 y 11):** Servidor FastAPI con ciclo de vida completo de tareas y frontend Streamlit para flujos visuales interactivos.
- **Observabilidad y Benchmarks (Fases 9 y 10):** Trazas estructuradas y suite de benchmarks de desarrollo independiente con evaluación por mutaciones.
- **Fiabilidad y Protocol Enforcement (Fase 12):** State machine que rechaza terminaciones textuales (`final`) sin acción requerida, esquema JSON forzado para creación de archivos y parser de recuperación de herramientas embebidas.
- **Terminal UX Overhaul:** Memento para rollback de parches con `/undo`, métricas de sesión (`/stats`), árbol de pasos visual (`├─`, `└─`) y autocompletado avanzado.

---

## Líneas de Trabajo Futuras

1. **Persistencia del almacén de tareas:** Almacenamiento durable (SQLite o JSON) para el historial de API y UI entre reinicios.
2. **Orquestación multi-fase (Supervisor Graph):** Descomposición de tareas complejas en fases explícitas (Inspector → Implementer → Verifier) con presupuesto dinámico de pasos.
3. **Ecosistemas adicionales:** Extensión del soporte de entornos más allá de Python/Pytest (ej. Node.js/npm).
4. **Transportes avanzados de inferencia:** Evaluación de endpoints vLLM con `tool_choice=required` y modos nativos de tool-calling.
