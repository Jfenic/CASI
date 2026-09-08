Reproducible mini repositories used by `casi benchmark`.

Each directory is copied into an isolated temporary workspace before a task
runs, then initialized as a git repository when needed for patch validation.

Fixtures intentionally include small, deterministic bugs for repair tasks and
one healthy library for read-only inspection tasks.
