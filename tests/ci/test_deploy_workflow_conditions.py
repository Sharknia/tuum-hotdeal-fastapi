import re
from pathlib import Path

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github/workflows/deploy.yml"


def _read_workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _get_job_block(workflow_text: str, job_name: str) -> str:
    pattern = rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)"
    match = re.search(pattern, workflow_text)
    assert match is not None, f"job 블록을 찾을 수 없습니다: {job_name}"
    return match.group(1)


def test_lint_job_if_uses_backend_only():
    workflow_text = _read_workflow_text()
    block = _get_job_block(workflow_text, "lint")

    assert (
        "if: ${{ needs.changes.outputs.backend == 'true' }}" in block
    ), "lint job은 backend 변경 여부만으로 실행되어야 합니다."
    assert (
        "needs.changes.outputs.frontend != 'true'" not in block
    ), "lint job이 frontend 변경 여부로 차단되면 안 됩니다."


def test_test_job_if_uses_backend_only():
    workflow_text = _read_workflow_text()
    block = _get_job_block(workflow_text, "test")

    assert (
        "if: ${{ needs.changes.outputs.backend == 'true' }}" in block
    ), "test job은 backend 변경 여부만으로 실행되어야 합니다."
    assert (
        "needs.changes.outputs.frontend != 'true'" not in block
    ), "test job이 frontend 변경 여부로 차단되면 안 됩니다."


def test_deploy_frontend_job_if_uses_frontend_only():
    workflow_text = _read_workflow_text()
    block = _get_job_block(workflow_text, "deploy-frontend")

    assert (
        "if: ${{ needs.changes.outputs.frontend == 'true' }}" in block
    ), "deploy-frontend job은 frontend 변경일 때만 실행되어야 합니다."


def test_tag_job_supports_backend_or_frontend_deploy_success():
    workflow_text = _read_workflow_text()
    block = _get_job_block(workflow_text, "tag")

    assert "needs: [deploy, deploy-frontend]" in block
    assert "needs.deploy.result == 'success'" in block
    assert "needs.deploy-frontend.result == 'success'" in block
