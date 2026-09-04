# Security

# Security

## Repository boundaries

- Resolve the repository root before handling a request.
- Reject paths that escape the repository, including traversal and symlink escapes.
- Ignore `.git` and sensitive files according to the repository security helpers.
- Enforce file-count, search-result, file-size, and output-size limits.

## Tool permissions

Tools should be grouped by capability:

- Read-only: list files, read files, and search code.
- Execution: run tests or other explicitly allowed commands in a sandbox.
- Mutation: validate and apply a patch only after the patch passes safety checks.

The LLM must never receive an unrestricted shell tool. Each command tool must use an allowlist, a timeout, a working-directory boundary, and a maximum output size.

## Patch rules

Before applying a patch, validate its syntax, target paths, repository boundaries, and allowed file operations. The default behavior should be dry-run or reviewable diff output; applying changes must be an explicit operation.

## Sandbox rules

Docker should be the default for untrusted command execution. Network access, mounted paths, resource limits, and container lifetime must be explicit configuration rather than implicit defaults. The local runner is intended for development only.

Project dependency images are prepared in a separate, explicitly approved
network-enabled build. Dependency installation can execute third-party package
build scripts, so CASI displays the detected strategy, dependency files, and
content-addressed image name before asking for approval. Tests never receive
network access and run against a sanitized temporary copy rather than the
original repository.
