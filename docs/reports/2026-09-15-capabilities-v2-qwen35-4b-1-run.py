"""Run the three v2 areas sequentially, preserving evidence and source hashes."""
from dataclasses import asdict
from datetime import datetime, UTC
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import urllib.request

from casi.config import settings
from casi.evaluation.benchmark import load_tasks
from casi.evaluation.runner import BenchmarkRunOptions, run_model_benchmark
from casi.evaluation.report import build_report_payload, render_markdown_report, write_report_files
from casi.llm.ollama_client import OllamaClient

root = Path('/home/fenic/top_project/CASI/casi-code-agent')
base = root / 'benchmarks/capabilities_v2'
prefix = root / 'docs/reports/2026-09-15-capabilities-v2-qwen35-4b-1'
model = 'qwen3.5:4b'
manifest_path = prefix.with_name(prefix.name + '-manifest.json')
outputs = {area: prefix.with_name(prefix.name + '-' + area + '.json') for area in ('testing', 'security', 'ml')}
for output in [manifest_path, *outputs.values()]:
    if output.exists() or output.with_suffix('.md').exists():
        raise RuntimeError(f'Refusing to overwrite existing report: {output}')
for output in outputs.values():
    if output.with_name(output.stem + '-artifacts').exists():
        raise RuntimeError('Artifact destination already exists')

with urllib.request.urlopen(settings.ollama_base_url.rstrip('/') + '/api/tags', timeout=10) as response:
    tags = json.load(response)
installed = next((item for item in tags['models'] if item.get('name') == model or item.get('model') == model), None)
if installed is None:
    raise RuntimeError('Requested qwen3.5:4b is not installed; no benchmark was started')
docker_probe = subprocess.run(['docker', 'info', '--format', '{{.ServerVersion}}'], capture_output=True, text=True, check=True, timeout=15)
docker_image = subprocess.run(['docker', 'image', 'inspect', settings.docker_image, '--format', '{{.Id}}'], capture_output=True, text=True, check=True, timeout=15)
if not settings.use_docker_sandbox or settings.allow_local_test_fallback:
    raise RuntimeError('Measurement requires Docker enabled and local fallback disabled')

files = sorted(list((root / 'src/casi').rglob('*.py')) + [p for p in base.rglob('*') if p.is_file() and p.suffix in {'.py', '.json', '.yaml'}])
def hashes():
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

manifest = {
    'started_at': datetime.now(UTC).isoformat(),
    'model': model,
    'model_digest': installed.get('digest'),
    'python': platform.python_version(),
    'docker_version': docker_probe.stdout.strip(),
    'docker_image_id': docker_image.stdout.strip(),
    'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'settings': {k: v for k, v in asdict(settings).items() if k != 'ollama_base_url'},
    'routing': 'assist',
    'sha256_before': hashes(),
    'reports': {},
}
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print('Preflight passed: Ollama model and Docker image available.', flush=True)
try:
    for area, output in outputs.items():
        tasks = load_tasks(base / area / 'tasks')
        assert len(tasks) == 4
        print(f'\nSTART AREA {area}: {len(tasks)} tasks', flush=True)
        run = run_model_benchmark(
            tasks,
            client=OllamaClient(model=model),
            options=BenchmarkRunOptions(
                repositories_root=base / area / 'repositories',
                routing='assist', verbose=True,
                artifacts_dir=output.with_name(output.stem + '-artifacts'),
            ),
        )
        payload = build_report_payload(run.results, model=run.model)
        write_report_files(payload, output, markdown=render_markdown_report(run.results, model=run.model))
        manifest['reports'][area] = str(output.relative_to(root))
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        print(f'FINISHED {area}: {sum(t.task_success for t in run.results)}/4 independent acceptance', flush=True)
finally:
    manifest['finished_at'] = datetime.now(UTC).isoformat()
    manifest['sha256_after'] = hashes()
    manifest['sources_unchanged'] = manifest['sha256_before'] == manifest['sha256_after']
    manifest['complete'] = len(manifest['reports']) == 3
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
