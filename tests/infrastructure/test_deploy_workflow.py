import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _service_block(compose_text: str, service_name: str) -> str:
    pattern = rf"(?ms)^  {service_name}:\n.*?(?=^  [a-zA-Z0-9_-]+:\n|\Z)"
    match = re.search(pattern, compose_text)
    if match is None:
        raise AssertionError(f"service block not found: {service_name}")
    return match.group(0)


def test_worker_runtime_verification_gate():
    compose_text = (PROJECT_ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    workflow_text = (PROJECT_ROOT / ".github/workflows/deploy.yml").read_text(
        encoding="utf-8"
    )

    worker_block = _service_block(compose_text, "worker")
    assert "init: true" in worker_block
    assert worker_block.count('"doppler"') == 1

    restart_index = workflow_text.index(
        "docker compose -f docker-compose.prod.yml up -d --force-recreate"
    )
    init_check_index = workflow_text.index(
        "docker inspect -f '{{.HostConfig.Init}}' tuum-hotdeal-worker"
    )
    doppler_check_index = workflow_text.index(
        "docker inspect -f '{{.Path}} {{join .Args \" \"}}' tuum-hotdeal-worker"
    )
    defunct_check_index = workflow_text.index("DEFUNCT_AFTER=")

    assert restart_index < init_check_index < doppler_check_index < defunct_check_index


def test_deploy_fails_when_worker_invariant_breaks():
    workflow_text = (PROJECT_ROOT / ".github/workflows/deploy.yml").read_text(
        encoding="utf-8"
    )

    assert "if: ${{ failure() }}" in workflow_text
    assert "Fail deploy on runtime invariant gate failure" in workflow_text

    assert (
        "docker inspect -f '{{.HostConfig.Init}}' tuum-hotdeal-worker"
        " | grep -qx 'true' || { echo \"Runtime invariant failed: worker init must be true.\"; exit 1; }"
    ) in workflow_text
    assert (
        "docker inspect -f '{{.Path}} {{join .Args \" \"}}' tuum-hotdeal-worker"
        " | grep -o 'doppler' | wc -l | tr -d ' '"
        " | grep -qx '1' || { echo \"Runtime invariant failed: doppler wrapping must be single.\"; exit 1; }"
    ) in workflow_text
    assert "DEFUNCT_BEFORE=0" in workflow_text
    assert (
        "docker exec tuum-hotdeal-worker sh -lc \"grep -s '^State:[[:space:]]*Z' /proc/[0-9]*/status | wc -l\" | tr -d ' '"
    ) in workflow_text
    assert (
        "[ \"\\${DEFUNCT_AFTER}\" -le \"\\${DEFUNCT_BEFORE}\" ] || { echo \"Runtime invariant failed: defunct baseline regression"
    ) in workflow_text


def test_deploy_healthcheck_wait_strategy_and_diagnostics():
    workflow_text = (PROJECT_ROOT / ".github/workflows/deploy.yml").read_text(
        encoding="utf-8"
    )

    assert "MAX_RETRIES=60" in workflow_text
    assert "SLEEP_SECONDS=5" in workflow_text
    assert "HEALTH_OK=false" in workflow_text
    assert (
        'docker exec \\${SERVICE_NAME} sh -lc "curl -fsS http://localhost:8000/health >/dev/null"'
        in workflow_text
    )
    assert "docker logs --tail 20 \\${SERVICE_NAME} || true" in workflow_text
    assert (
        "docker inspect --format='{{json .State.Health}}' \\${SERVICE_NAME} || true"
        in workflow_text
    )
    assert "docker logs --tail 200 \\${SERVICE_NAME} || true" in workflow_text


def test_predeploy_migration_runs_before_recreate():
    workflow_text = (PROJECT_ROOT / ".github/workflows/deploy.yml").read_text(
        encoding="utf-8"
    )

    migration_index = workflow_text.index(
        "docker compose -f docker-compose.prod.yml run -T --rm --no-deps -e RUN_DB_MIGRATIONS=1 web doppler run -- /app/entrypoint.sh true"
    )
    recreate_index = workflow_text.index(
        "docker compose -f docker-compose.prod.yml up -d --force-recreate"
    )
    strict_mode_index = workflow_text.index("set -euo pipefail")

    assert strict_mode_index < migration_index < recreate_index


def test_backend_ci_and_backend_deploy_filters_are_split():
    workflow_text = (PROJECT_ROOT / ".github/workflows/deploy.yml").read_text(
        encoding="utf-8"
    )
    backend_ci_match = re.search(
        r"(?ms)^ {12}backend_ci:\n(?P<section>(?: {14}- .*\n)+)", workflow_text
    )
    backend_deploy_match = re.search(
        r"(?ms)^ {12}backend_deploy:\n(?P<section>(?: {14}- .*\n)+)", workflow_text
    )

    assert backend_ci_match is not None
    assert backend_deploy_match is not None

    backend_ci_section = backend_ci_match.group("section")
    backend_deploy_section = backend_deploy_match.group("section")

    assert "backend_ci:" in workflow_text
    assert "backend_deploy:" in workflow_text
    assert workflow_text.count("- 'tests/**'") == 1
    assert workflow_text.count("- 'pytest.ini'") == 1
    assert workflow_text.count("- '.env.test'") == 1
    assert workflow_text.count("- 'Makefile'") == 1
    assert workflow_text.count("- 'pyrightconfig.json'") == 1
    assert "- 'Makefile'" in backend_ci_section
    assert "- 'pyrightconfig.json'" in backend_ci_section
    assert "- 'Makefile'" not in backend_deploy_section
    assert "- 'pyrightconfig.json'" not in backend_deploy_section
    assert "needs.changes.outputs.backend_ci == 'true'" in workflow_text
    assert "needs.changes.outputs.backend_deploy == 'true'" in workflow_text
    assert "needs: [changes, lint, test]" in workflow_text


def test_build_cache_uses_gha_and_registry_sources():
    workflow_text = (PROJECT_ROOT / ".github/workflows/deploy.yml").read_text(
        encoding="utf-8"
    )

    assert "cache-from: |" in workflow_text
    assert "type=gha,scope=backend-arm64" in workflow_text
    assert (
        "type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache-arm64"
        in workflow_text
    )
    assert "cache-to: |" in workflow_text
    assert "type=gha,scope=backend-arm64,mode=max" in workflow_text
    assert (
        "type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache-arm64,"
        "mode=max,image-manifest=true,oci-mediatypes=true"
    ) in workflow_text
