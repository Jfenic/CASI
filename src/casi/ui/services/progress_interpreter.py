"""Human-readable progress interpretation for live task updates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from casi.ui.client.models import TaskSnapshot

_STEP_PATTERN = re.compile(r"decision (\d+)/(\d+)")


@dataclass(frozen=True)
class ProgressView:
    headline: str
    detail: str
    next_step: str
    elapsed_seconds: float
    step_label: str | None
    recent_events: tuple[str, ...]


def interpret_progress(
    task: TaskSnapshot,
    *,
    now: datetime | None = None,
) -> ProgressView:
    """Derive user-facing progress text from task status and trace tail."""

    current = now or datetime.now(tz=UTC)
    elapsed = max((current - task.created_at).total_seconds(), 0.0)
    recent = tuple(task.trace[-6:])
    last_event = task.trace[-1] if task.trace else ""

    if task.status == "pending":
        return ProgressView(
            headline="En cola",
            detail="La tarea está registrada y espera turno de ejecución.",
            next_step="El agente arrancará en el repositorio indicado.",
            elapsed_seconds=elapsed,
            step_label=None,
            recent_events=recent,
        )

    if task.status == "running":
        headline, detail, next_step, step_label = _interpret_running_event(
            last_event,
            repository=task.repository,
            task_text=task.task,
        )
        return ProgressView(
            headline=headline,
            detail=detail,
            next_step=next_step,
            elapsed_seconds=elapsed,
            step_label=step_label,
            recent_events=recent,
        )

    if task.status == "awaiting_approval":
        return ProgressView(
            headline="Esperando tu revisión",
            detail="El agente terminó y propone un parche verificado.",
            next_step="Revisa el diff y aprueba o rechaza el cambio.",
            elapsed_seconds=elapsed,
            step_label=None,
            recent_events=recent,
        )

    if task.status == "completed":
        return ProgressView(
            headline="Completada",
            detail="La tarea finalizó sin parche pendiente.",
            next_step="Consulta la respuesta del agente.",
            elapsed_seconds=elapsed,
            step_label=None,
            recent_events=recent,
        )

    if task.status == "failed":
        return ProgressView(
            headline="Fallida",
            detail=task.error or "La tarea terminó con un error.",
            next_step="Revisa la respuesta y la traza para más detalle.",
            elapsed_seconds=elapsed,
            step_label=None,
            recent_events=recent,
        )

    return ProgressView(
        headline=task.status,
        detail="Estado actualizado.",
        next_step="Consulta las pestañas de detalle.",
        elapsed_seconds=elapsed,
        step_label=None,
        recent_events=recent,
    )


def _interpret_running_event(
    last_event: str,
    *,
    repository: str,
    task_text: str,
) -> tuple[str, str, str, str | None]:
    step_label = _extract_step_label(last_event)
    lowered = last_event.lower()

    if not last_event:
        return (
            "Iniciando",
            f"Ejecutando en `{repository}`.",
            "El agente analizará el repositorio según tu instrucción.",
            step_label,
        )

    if "preparando agente" in lowered:
        return (
            "Arrancando",
            f"Conectando con el modelo para trabajar en `{repository}`.",
            "Explorar el repositorio o buscar código relevante.",
            step_label,
        )

    if "tool read_file" in lowered:
        return (
            "Leyendo código",
            last_event,
            "Analizar el contenido leído o buscar más contexto.",
            step_label,
        )

    if "tool search_code" in lowered:
        return (
            "Buscando en el código",
            last_event,
            "Leer los archivos encontrados o refinar la búsqueda.",
            step_label,
        )

    if "tool list_files" in lowered:
        return (
            "Explorando archivos",
            last_event,
            "Seleccionar archivos relevantes para leer o modificar.",
            step_label,
        )

    if "tool run_tests" in lowered:
        return (
            "Ejecutando tests",
            last_event,
            "Verificar resultados y proponer correcciones si fallan.",
            step_label,
        )

    if "tool git_diff" in lowered:
        return (
            "Revisando cambios",
            last_event,
            "Preparar o ajustar una propuesta de parche.",
            step_label,
        )

    if "propose_file" in lowered or "patch" in lowered:
        return (
            "Preparando parche",
            last_event,
            "Validar el diff y ejecutar tests en sandbox.",
            step_label,
        )

    if "decision" in lowered and "final" in lowered:
        return (
            "Redactando respuesta",
            last_event,
            "Completar la respuesta o proponer cambios finales.",
            step_label,
        )

    if "decision" in lowered:
        return (
            "Decidiendo siguiente paso",
            last_event,
            "Elegir la herramienta adecuada para avanzar con la tarea.",
            step_label,
        )

    if "nudge" in lowered:
        return (
            "Corrigiendo estrategia",
            last_event,
            "Reintentar con una acción más concreta.",
            step_label,
        )

    return (
        "Trabajando",
        f"Instrucción: {task_text}",
        last_event or "Continuar con la siguiente acción del agente.",
        step_label,
    )


def _extract_step_label(event: str) -> str | None:
    match = _STEP_PATTERN.search(event)
    if match is None:
        return None
    return f"Paso {match.group(1)} de {match.group(2)}"
