"""Base tool abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from casi_code_agent.tools.result import ToolResult


@dataclass(frozen=True)
class ToolArgumentSpec:
	"""Declarative description of a tool argument."""

	name: str
	type: type | tuple[type, ...]
	required: bool = True
	default: Any = field(default=None)
	minimum: int | None = None


class Tool(ABC):
	"""Base class for structured tools."""

	name: str
	description: str

	@property
	@abstractmethod
	def argument_schema(self) -> dict[str, ToolArgumentSpec]:
		"""Return the tool argument schema."""

	def validate_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
		"""Validate and normalize the tool arguments."""

		validated: dict[str, Any] = {}
		schema = self.argument_schema

		for argument_name, spec in schema.items():
			if argument_name not in arguments:
				if spec.required:
					raise ValueError(f"Missing required argument: {argument_name}")
				validated[argument_name] = spec.default
				continue

			value = arguments[argument_name]
			if not isinstance(value, spec.type):
				raise TypeError(f"Argument '{argument_name}' must be of type {self._type_name(spec.type)}.")

			if spec.minimum is not None and isinstance(value, int) and value < spec.minimum:
				raise ValueError(f"Argument '{argument_name}' must be greater than or equal to {spec.minimum}.")

			validated[argument_name] = value

		unexpected = sorted(set(arguments) - set(schema))
		if unexpected:
			raise ValueError(f"Unexpected arguments: {', '.join(unexpected)}")

		return validated

	@staticmethod
	def _type_name(expected_type: type | tuple[type, ...]) -> str:
		if isinstance(expected_type, tuple):
			return ", ".join(type_.__name__ for type_ in expected_type)
		return expected_type.__name__

	@abstractmethod
	def run(self, arguments: dict[str, Any]) -> ToolResult:
		"""Execute the tool after validation."""

	def execute(self, arguments: dict[str, Any]) -> ToolResult:
		"""Validate arguments and execute the tool."""

		validated_arguments = self.validate_arguments(arguments)
		return self.run(validated_arguments)


def path_argument(path_value: str | Path) -> Path:
	"""Normalize path-like arguments."""

	return Path(path_value)
