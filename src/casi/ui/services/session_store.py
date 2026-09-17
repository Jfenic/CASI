"""Session state adapter for Streamlit."""

from __future__ import annotations

from typing import Any


class SessionStore:
    """Facade over a mutable mapping used as UI session state."""

    def __init__(self, state: dict[str, Any]) -> None:
        self._state = state

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def pop(self, key: str, default: Any = None) -> Any:
        return self._state.pop(key, default)

    @property
    def selected_task_id(self) -> str | None:
        value = self.get("selected_task_id")
        return str(value) if value else None

    @selected_task_id.setter
    def selected_task_id(self, task_id: str | None) -> None:
        if task_id is None:
            self.pop("selected_task_id", None)
        else:
            self.set("selected_task_id", task_id)

    @property
    def auto_refresh(self) -> bool:
        return bool(self.get("auto_refresh", True))

    @auto_refresh.setter
    def auto_refresh(self, enabled: bool) -> None:
        self.set("auto_refresh", enabled)
