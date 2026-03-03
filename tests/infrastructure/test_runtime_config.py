import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _service_block(compose_text: str, service_name: str) -> str:
    pattern = rf"(?ms)^  {service_name}:\n.*?(?=^  [a-zA-Z0-9_-]+:\n|\Z)"
    match = re.search(pattern, compose_text)
    if match is None:
        raise AssertionError(f"service block not found: {service_name}")
    return match.group(0)


def test_single_doppler_wrapping_in_prod_runtime_config():
    compose_text = (PROJECT_ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    dockerfile_text = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    web_block = _service_block(compose_text, "web")
    worker_block = _service_block(compose_text, "worker")

    assert "ENTRYPOINT [\"doppler\", \"run\", \"--\"]" not in dockerfile_text
    assert web_block.count('"doppler"') == 1
    assert worker_block.count('"doppler"') == 1
    assert '"python", "-m", "app.worker_main"' in worker_block
    assert "doppler\", \"run\", \"--\", \"doppler\"" not in compose_text


def test_compose_init_and_stop_policy():
    compose_text = (PROJECT_ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")

    web_block = _service_block(compose_text, "web")
    worker_block = _service_block(compose_text, "worker")

    for service_block in (web_block, worker_block):
        assert "init: true" in service_block
        assert "stop_signal: SIGTERM" in service_block
        assert "stop_grace_period: 90s" in service_block


def test_entrypoint_migration_gate_and_db_wait_timeout():
    entrypoint_text = (PROJECT_ROOT / "entrypoint.sh").read_text(encoding="utf-8")

    assert "DB_WAIT_TIMEOUT=${DB_WAIT_TIMEOUT:-180}" in entrypoint_text
    assert "if [ \"${RUN_DB_MIGRATIONS:-0}\" = \"1\" ]; then" in entrypoint_text
    assert "Skipping database migrations" in entrypoint_text
