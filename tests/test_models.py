from pathlib import Path

from delivery_risk_agent.models import ProjectSnapshot


def test_sample_project_can_be_loaded():
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "sample_project.json"

    snapshot = ProjectSnapshot.model_validate_json(
        data_file.read_text()
    )

    assert snapshot.name == "Payments Platform"
    assert len(snapshot.work_items) == 3
    assert len(snapshot.pull_requests) == 2
    assert snapshot.work_items[0].id == "PAY-101"
    assert snapshot.pull_requests[0].number == 42