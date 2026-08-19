from datetime import datetime, timedelta


def _payload(**overrides):
    payload = {
        "title": "comparison",
        "mode": "find_diff",
        "column_a": "apple\nbanana",
        "column_b": "apple\ncherry",
        "options": {"ignore_case": False, "trim": False, "skip_empty": True},
    }
    payload.update(overrides)
    return payload


def test_create_task_trims_title_and_enforces_limit(client):
    created = client.post("/api/tasks", json=_payload(title="  report  "))
    assert created.status_code == 201
    assert created.json()["title"] == "report"

    too_many_lines = "\n".join(str(index) for index in range(1001))
    rejected = client.post("/api/preview", json=_payload(column_a=too_many_lines))
    assert rejected.status_code == 422

    invalid_limit = client.get("/api/tasks?limit=0")
    assert invalid_limit.status_code == 422


def test_expired_task_is_hidden_from_task_and_share_endpoints(client):
    created = client.post("/api/tasks", json=_payload())
    task_id = created.json()["id"]
    share = client.post(f"/api/tasks/{task_id}/share")
    token = share.json()["token"]

    from db import SessionLocal
    from models import DiffTask

    with SessionLocal() as db:
        task = db.query(DiffTask).filter_by(id=task_id).one()
        task.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

    assert client.get(f"/api/tasks/{task_id}").status_code == 404
    assert client.get(f"/api/share/{token}").status_code == 404
    assert client.get("/api/tasks").json() == []


def test_csv_export_prefixes_spreadsheet_formulas_and_uses_utf8_bom(client):
    created = client.post(
        "/api/tasks",
        json=_payload(column_a="=2+2\nnormal", column_b="other"),
    )

    exported = client.get(f"/api/tasks/{created.json()['id']}/export")
    assert exported.status_code == 200
    assert exported.content.startswith("\ufeff".encode())
    assert "'=2+2" in exported.text
