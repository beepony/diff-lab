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

    summary = client.get("/api/tasks").json()[0]
    assert summary["column_a_count"] == 2
    assert summary["column_b_count"] == 2

    too_many_lines = "\n".join(str(index) for index in range(1001))
    rejected = client.post("/api/preview", json=_payload(column_a=too_many_lines))
    assert rejected.status_code == 422

    invalid_limit = client.get("/api/tasks?limit=0")
    assert invalid_limit.status_code == 422
    assert invalid_limit.headers["X-Request-ID"]
    assert invalid_limit.json()["error"]["code"] == "VALIDATION_ERROR"


def test_not_found_response_preserves_request_id_and_error_shape(client):
    response = client.get("/api/tasks/missing", headers={"X-Request-ID": "trace-123"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "trace-123"
    assert response.json()["error"] == {
        "code": "HTTP_ERROR",
        "message": "Task not found",
        "request_id": "trace-123",
    }


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


def test_share_link_has_its_own_expiry_and_can_be_revoked(client):
    created = client.post("/api/tasks", json=_payload())
    task_id = created.json()["id"]
    share = client.post(f"/api/tasks/{task_id}/share", json={"expires_in_days": 1})
    token = share.json()["token"]

    assert share.status_code == 200
    assert "expires_at" in share.json()
    assert client.get(f"/api/tasks/{task_id}/share").json()["token"] == token

    assert client.delete(f"/api/tasks/{task_id}/share").status_code == 204
    assert client.get(f"/api/share/{token}").status_code == 404


def test_expired_share_link_is_not_accessible_while_task_remains_active(client):
    created = client.post("/api/tasks", json=_payload())
    task_id = created.json()["id"]
    token = client.post(f"/api/tasks/{task_id}/share").json()["token"]

    from db import SessionLocal
    from models import ShareLink

    with SessionLocal() as db:
        link = db.query(ShareLink).filter_by(access_token=token).one()
        link.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

    assert client.get(f"/api/tasks/{task_id}").status_code == 200
    assert client.get(f"/api/share/{token}").status_code == 404


def test_management_endpoints_require_token_when_configured(client, monkeypatch):
    monkeypatch.setenv("DIFF_LAB_ADMIN_TOKEN", "test-admin-token")

    rejected = client.post("/api/tasks", json=_payload())
    assert rejected.status_code == 401
    assert rejected.headers["WWW-Authenticate"] == "Bearer"

    accepted = client.post("/api/tasks", json=_payload(), headers={"X-Admin-Token": "test-admin-token"})
    assert accepted.status_code == 201

    assert client.post("/api/preview", json=_payload()).status_code == 200


def test_csv_export_prefixes_spreadsheet_formulas_and_uses_utf8_bom(client):
    created = client.post(
        "/api/tasks",
        json=_payload(column_a="=2+2\nnormal", column_b="other"),
    )

    exported = client.get(f"/api/tasks/{created.json()['id']}/export")
    assert exported.status_code == 200
    assert exported.content.startswith("\ufeff".encode())
    assert "'=2+2" in exported.text
