"""Sandbox runners."""

from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner, DockerTestRunner
from casi.sandbox.local_runner import LocalRunner

__all__ = ["DockerRunner", "DockerTestRunner", "LocalRunner", "TestResult"]
