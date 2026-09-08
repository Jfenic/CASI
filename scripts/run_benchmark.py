#!/usr/bin/env python3
"""Run benchmark tasks for CASI."""

from __future__ import annotations

import sys
from pathlib import Path

from casi.cli import main


if __name__ == "__main__":
	raise SystemExit(
		main(
			[
				"benchmark",
				*sys.argv[1:],
			]
		)
	)
