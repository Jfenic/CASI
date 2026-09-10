"""Evaluation and benchmarking utilities."""

from casi.evaluation.benchmark import (
    BenchmarkModelRun,
    BenchmarkTask,
    BenchmarkTaskResult,
    load_tasks,
    run_benchmark,
)
from casi.evaluation.metrics import summarize_model_runs, summarize_results
from casi.evaluation.report import (
    build_comparison_payload,
    build_report_payload,
    render_comparison_report,
    render_markdown_report,
    render_report,
    write_report_files,
)
from casi.evaluation.runner import BenchmarkRunOptions, compare_models, run_task

__all__ = [
    "BenchmarkModelRun",
    "BenchmarkRunOptions",
    "BenchmarkTask",
    "BenchmarkTaskResult",
    "build_comparison_payload",
    "build_report_payload",
    "compare_models",
    "load_tasks",
    "render_comparison_report",
    "render_markdown_report",
    "render_report",
    "run_benchmark",
    "run_task",
    "summarize_model_runs",
    "summarize_results",
    "write_report_files",
]
