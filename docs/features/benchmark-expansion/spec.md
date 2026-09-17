# Benchmark expansion — specification

Add twelve deterministic, independently graded Python tasks: four test-writing,
four defensive security, four ML/feature extraction. Ship as a versioned extension
under `benchmarks/capabilities_v2/{testing,security,ml}`; preserve existing suites
and their historical scores. No new dependencies or live services are required.

Every assertion and mutation must follow an explicit task requirement. Test-writing
tasks must distinguish missing delivery, failure on correct code and surviving
mutations. Incorrect collection/imports never count as mutation detection.
Security tests must include legitimate inputs to reject blanket denial fixes.
ML uses tiny fixed datasets and numerical tolerances, without training or GPUs.

Acceptance: twelve baselines rejected; twelve references accepted; weak generated
tests rejected; known coverage gaps (default retry count and ASCII-only slugs)
detected. Validate using the existing grader, including Docker before closure.
No claim about model capability until a separate Ollama measurement is recorded.
