Reproducible mini repositories used by `casi benchmark`.

Each directory is copied into an isolated temporary workspace before a task
runs, then initialized as a git repository when needed for patch validation.

Fixtures intentionally include small, deterministic bugs for repair tasks,
missing modules for file-creation tasks, and one healthy library for read-only
inspection tasks.

Creation tasks (`stats_app`, `palindrome_app`, `initials_app`) ship tests that
import modules which do not exist yet. The agent must call `propose_file` to
create the missing file with complete content.

Focused fix tasks (`clamp_app`, `repeat_app`, `strip_app`) mirror common repair
failures: one-line logic bugs and whitespace handling.

The separate [development suite](../development/README.md) adds ten richer tasks
with independent acceptance checks, reference solutions and mutation scoring for
test-writing tasks. Run it with its own `--tasks-dir` and `--repos-dir`.
