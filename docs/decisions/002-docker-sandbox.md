# 002: Docker sandbox

Status: accepted; implementation documented on 2026-09-13.

## Decision

Run tests in Docker by default, on sanitized temporary repository copies with no
network, a non-root user, timeout and resource limits. Never mount the original
repository. Missing Docker, a missing image or infrastructure failure stops tests
unless local fallback was explicitly enabled. Explicit local mode is also available.

Prepare Python dependencies in a separate network-enabled Docker build with user
approval. Cache images by dependency-file content and reuse them for offline tests.

## Rationale and consequences

Repository tests and dependency builds execute code. Separate build and test
phases bound network access and avoid silently executing untrusted tests on the
host. Docker availability and prepared images are operational requirements;
local execution provides neither container network nor process isolation.
Independent development benchmark scoring requires Docker and has no local fallback.
