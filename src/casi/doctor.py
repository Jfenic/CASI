"""System diagnostics and health check utilities for CASI."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from casi.config import settings
from casi.terminal.presenter import TerminalPresenter, _detect_git_branch


@dataclass(frozen=True, slots=True)
class DiagnosticCheck:
    """Outcome of a single environment or dependency check."""

    name: str
    passed: bool
    message: str
    hint: str | None = None


def check_python_runtime() -> DiagnosticCheck:
    """Verify that Python runtime is valid."""
    version = platform.python_version()
    major, minor = sys.version_info.major, sys.version_info.minor
    if (major, minor) < (3, 11):
        return DiagnosticCheck(
            name="Python Runtime",
            passed=False,
            message=f"Python {version} is too old (< 3.11)",
            hint="Install Python 3.11 or higher.",
        )
    return DiagnosticCheck(
        name="Python Runtime",
        passed=True,
        message=f"Python {version} (>= 3.11)",
    )


def check_git_workspace(repository: Path) -> DiagnosticCheck:
    """Verify repository folder and git status."""
    resolved = repository.resolve()
    if not resolved.exists():
        return DiagnosticCheck(
            name="Git Repository",
            passed=False,
            message=f"Path does not exist: {resolved}",
            hint="Check the path passed to --repo.",
        )

    branch = _detect_git_branch(resolved)
    if branch:
        # Check dirty state
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(resolved),
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            dirty = bool(res.stdout.strip())
            state = "dirty" if dirty else "clean"
        except Exception:
            state = "ready"

        return DiagnosticCheck(
            name="Git Repository",
            passed=True,
            message=f"{resolved.name} [git: {branch} • {state}]",
        )

    return DiagnosticCheck(
        name="Git Repository",
        passed=True,
        message=f"{resolved.name} (non-git workspace fallback)",
        hint="Run 'git init' in the workspace to enable git worktree isolation.",
    )


def check_ollama(
    base_url: str = settings.ollama_base_url,
    model: str = settings.ollama_model,
) -> list[DiagnosticCheck]:
    """Verify Ollama server reachability and model availability."""
    normalized_url = base_url.rstrip("/")
    tags_url = f"{normalized_url}/api/tags"

    # 1. Connection check
    try:
        req = Request(tags_url, headers={"User-Agent": "CASI-Doctor/1.0"})
        with urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError) as exc:
        return [
            DiagnosticCheck(
                name="Ollama Server",
                passed=False,
                message=f"Cannot reach {normalized_url} ({exc})",
                hint="Start the Ollama server: ollama serve",
            ),
            DiagnosticCheck(
                name="LLM Model",
                passed=False,
                message=f"{model} (server offline)",
                hint=f"Pull model with: ollama pull {model}",
            ),
        ]

    server_check = DiagnosticCheck(
        name="Ollama Server",
        passed=True,
        message=f"Online ({normalized_url})",
    )

    # 2. Model check
    available_models = [m.get("name", "") for m in data.get("models", [])]
    target_clean = model.lower()
    found = any(
        target_clean == m.lower()
        or target_clean == m.lower().split(":")[0]
        or f"{target_clean}:latest" == m.lower()
        for m in available_models
    )

    if found:
        model_check = DiagnosticCheck(
            name="LLM Model",
            passed=True,
            message=f"{model} (available in Ollama)",
        )
    else:
        model_check = DiagnosticCheck(
            name="LLM Model",
            passed=False,
            message=f"Model '{model}' not found in Ollama",
            hint=f"Download the model: ollama pull {model}",
        )

    return [server_check, model_check]


def check_openai(model: str = "gpt-4o") -> DiagnosticCheck:
    """Verify OpenAI API configuration."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return DiagnosticCheck(
            name="OpenAI Provider",
            passed=True,
            message=f"Configured with model {model}",
        )
    return DiagnosticCheck(
        name="OpenAI Provider",
        passed=False,
        message="OPENAI_API_KEY environment variable is not set",
        hint="Export your key: export OPENAI_API_KEY='sk-...'",
    )


def check_docker_sandbox(
    image: str = settings.docker_image,
    use_sandbox: bool = settings.use_docker_sandbox,
) -> list[DiagnosticCheck]:
    """Verify Docker daemon access and sandbox image presence."""
    if not use_sandbox:
        return [
            DiagnosticCheck(
                name="Docker Sandbox",
                passed=True,
                message="Disabled by configuration (LOCALCODE_AGENT_USE_DOCKER=false)",
            )
        ]

    if shutil.which("docker") is None:
        return [
            DiagnosticCheck(
                name="Docker Daemon",
                passed=False,
                message="Docker CLI binary not found in PATH",
                hint="Install Docker: https://docs.docker.com/engine/install/",
            )
        ]

    # Docker running check
    try:
        res = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=3.0,
        )
        docker_ok = res.returncode == 0
    except Exception as exc:
        docker_ok = False
        res = subprocess.CompletedProcess([], 1, stderr=str(exc))

    if not docker_ok:
        return [
            DiagnosticCheck(
                name="Docker Daemon",
                passed=False,
                message="Docker daemon is not running or unreachable",
                hint=(
                    "Start Docker daemon: sudo systemctl start docker "
                    "(or open Docker Desktop)"
                ),
            )
        ]

    daemon_check = DiagnosticCheck(
        name="Docker Daemon",
        passed=True,
        message="Running and accessible",
    )

    # Sandbox image check
    try:
        img_res = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        img_ok = img_res.returncode == 0
    except Exception:
        img_ok = False

    if img_ok:
        image_check = DiagnosticCheck(
            name="Sandbox Image",
            passed=True,
            message=f"{image} found",
        )
    else:
        image_check = DiagnosticCheck(
            name="Sandbox Image",
            passed=False,
            message=f"Image '{image}' is not built",
            hint=f"Build image: docker build -t {image} -f docker/sandbox.Dockerfile .",
        )

    return [daemon_check, image_check]


def collect_diagnostics(
    repository: str | Path = ".",
    *,
    provider: str | None = None,
    model: str | None = None,
) -> list[DiagnosticCheck]:
    """Run all environment health checks and return structured diagnostic list."""
    repo_path = Path(repository)
    active_provider = provider or settings.llm_provider
    active_model = model or (
        settings.ollama_model if active_provider == "ollama" else "gpt-4o"
    )

    checks: list[DiagnosticCheck] = [
        check_python_runtime(),
        check_git_workspace(repo_path),
    ]

    if active_provider == "ollama":
        checks.extend(check_ollama(model=active_model))
    else:
        checks.append(check_openai(model=active_model))

    checks.extend(check_docker_sandbox())
    return checks


def run_doctor(
    repository: str | Path = ".",
    *,
    provider: str | None = None,
    model: str | None = None,
    output_fn: Callable[[str], None] = print,
    presenter: TerminalPresenter | None = None,
) -> bool:
    """Execute diagnostics, render styled results, and return overall success."""
    checks = collect_diagnostics(repository, provider=provider, model=model)
    all_passed = all(c.passed for c in checks)

    p = presenter or TerminalPresenter(output_fn=output_fn)
    t = p.theme

    card_items: dict[str, str] = {}
    for c in checks:
        if c.passed:
            badge = t.success("✔") if t.color_enabled else "[OK]"
            card_items[c.name] = f"{badge}  {c.message}"
        else:
            badge = t.error("✗") if t.color_enabled else "[FAIL]"
            card_items[c.name] = f"{badge}  {c.message}"

    p.status_card(card_items, title="CASI Doctor • Environment Health")

    failed_checks = [c for c in checks if not c.passed and c.hint]
    if failed_checks:
        output_fn("")
        p.warning("One or more requirements need attention:")
        for idx, c in enumerate(failed_checks, 1):
            p.hint(f"{idx}. {t.bold(c.name)}: {c.hint}")
        output_fn("")
    else:
        output_fn("")
        p.success("All checks passed! Your environment is ready.")
        output_fn("")

    return all_passed
