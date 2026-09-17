from __future__ import annotations

import time

from casi.terminal.spinner import Spinner, status
from casi.terminal.theme import Theme


def test_spinner_lifecycle_in_non_tty() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    spinner = Spinner("Loading...", theme=theme)

    spinner.start()
    assert spinner.message == "Loading..."
    spinner.update("Still loading...")
    assert spinner.message == "Still loading..."
    spinner.stop()


def test_spinner_context_manager() -> None:
    theme = Theme(use_color=False, use_unicode=True)
    with status("Working...", theme=theme) as sp:
        assert sp.message == "Working..."
        time.sleep(0.01)
