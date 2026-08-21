from datetime import datetime, timedelta


USER_A_HEADERS = {"X-User-Token": "a" * 64}
USER_B_HEADERS = {"X-User-Token": "b" * 64}
ADMIN_HEADERS = {"X-Admin-Token": "test-admin-token"}


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
    created = client.post("/api/tasks", json=_payload(title="  report  "), headers=USER_A_HEADERS)
    assert created.status_code == 201
    assert created.json()["title"] == "report"
    assert created.json()["can_manage"] is False

    from db import SessionLocal
    from models import DiffTask

    with SessionLocal() as db:
        task = db.query(DiffTask).filter_by(id=created.json()["id"]).one()
        assert task.owner_token_hash != USER_A_HEADERS["X-User-Token"]
        assert len(task.owner_token_hash) == 64

    summary = client.get("/api/tasks", headers=USER_A_HEADERS).json()[0]
    assert summary["column_a_count"] == 2
    assert summary["column_b_count"] == 2

    too_many_lines = "\n".join(str(index) for index in range(1001))
    rejected = client.post("/api/preview", json=_payload(column_a=too_many_lines))
    assert rejected.status_code == 422

    invalid_limit = client.get("/api/tasks?limit=0", headers=USER_A_HEADERS)
    assert invalid_limit.status_code == 422
    assert invalid_limit.headers["X-Request-ID"]
    assert invalid_limit.json()["error"]["code"] == "VALIDATION_ERROR"


def test_user_identity_is_required_for_saved_tasks(client):
    assert client.post("/api/tasks", json=_payload()).status_code == 401
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/preview", json=_payload()).status_code == 200


def test_users_can_only_access_their_own_tasks_while_admin_can_access_all(client):
    task_a = client.post("/api/tasks", json=_payload(title="A"), headers=USER_A_HEADERS).json()
    task_b = client.post("/api/tasks", json=_payload(title="B"), headers=USER_B_HEADERS).json()

    assert [task["id"] for task in client.get("/api/tasks", headers=USER_A_HEADERS).json()] == [task_a["id"]]
    assert [task["id"] for task in client.get("/api/tasks", headers=USER_B_HEADERS).json()] == [task_b["id"]]
    assert client.get(f"/api/tasks/{task_a['id']}", headers=USER_B_HEADERS).status_code == 404
    assert client.get(f"/api/tasks/{task_a['id']}/export", headers=USER_B_HEADERS).status_code == 404

    admin_history = client.get("/api/tasks", headers=ADMIN_HEADERS).json()
    assert {task["id"] for task in admin_history} == {task_a["id"], task_b["id"]}
    admin_detail = client.get(f"/api/tasks/{task_a['id']}", headers=ADMIN_HEADERS)
    assert admin_detail.status_code == 200
    assert admin_detail.json()["can_manage"] is True


def test_legacy_unowned_tasks_are_admin_only(client):
    from db import SessionLocal
    from models import DiffTask

    with SessionLocal() as db:
        legacy = DiffTask(
            title="legacy",
            mode="find_diff",
            column_a="a",
            column_b="b",
            options="{}",
            result_meta="{}",
        )
        db.add(legacy)
        db.commit()
        legacy_id = legacy.id

    assert client.get(f"/api/tasks/{legacy_id}", headers=USER_A_HEADERS).status_code == 404
    assert client.get(f"/api/tasks/{legacy_id}", headers=ADMIN_HEADERS).status_code == 200


def test_not_found_response_preserves_request_id_and_error_shape(client):
    headers = {**USER_A_HEADERS, "X-Request-ID": "trace-123"}
    response = client.get("/api/tasks/missing", headers=headers)

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "trace-123"
    assert response.json()["error"] == {
        "code": "HTTP_ERROR",
        "message": "Task not found",
        "request_id": "trace-123",
    }


def test_expired_task_is_hidden_from_task_and_share_endpoints(client):
    created = client.post("/api/tasks", json=_payload(), headers=USER_A_HEADERS)
    task_id = created.json()["id"]
    token = client.post(f"/api/tasks/{task_id}/share", headers=ADMIN_HEADERS).json()["token"]

    from db import SessionLocal
    from models import DiffTask

    with SessionLocal() as db:
        task = db.query(DiffTask).filter_by(id=task_id).one()
        task.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

    assert client.get(f"/api/tasks/{task_id}", headers=USER_A_HEADERS).status_code == 404
    assert client.get(f"/api/share/{token}").status_code == 404
    assert client.get("/api/tasks", headers=USER_A_HEADERS).json() == []


def test_share_link_is_admin_managed_and_read_only(client):
    created = client.post("/api/tasks", json=_payload(), headers=USER_A_HEADERS)
    task_id = created.json()["id"]

    assert client.post(f"/api/tasks/{task_id}/share", headers=USER_A_HEADERS).status_code == 401
    share = client.post(
        f"/api/tasks/{task_id}/share",
        json={"expires_in_days": 1},
        headers=ADMIN_HEADERS,
    )
    token = share.json()["token"]

    assert share.status_code == 200
    assert "expires_at" in share.json()
    assert client.get(f"/api/tasks/{task_id}/share", headers=ADMIN_HEADERS).json()["token"] == token
    assert client.get("/api/tasks", headers=USER_A_HEADERS).json()[0]["share_token"] is None
    assert client.get("/api/tasks", headers=ADMIN_HEADERS).json()[0]["share_token"] == token
    shared_task = client.get(f"/api/share/{token}")
    assert shared_task.status_code == 200
    assert shared_task.json()["can_manage"] is False

    assert client.delete(f"/api/tasks/{task_id}/share", headers=ADMIN_HEADERS).status_code == 204
    assert client.get(f"/api/share/{token}").status_code == 404


def test_expired_share_link_is_not_accessible_while_task_remains_active(client):
    created = client.post("/api/tasks", json=_payload(), headers=USER_A_HEADERS)
    task_id = created.json()["id"]
    token = client.post(f"/api/tasks/{task_id}/share", headers=ADMIN_HEADERS).json()["token"]

    from db import SessionLocal
    from models import ShareLink

    with SessionLocal() as db:
        link = db.query(ShareLink).filter_by(access_token=token).one()
        link.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

    assert client.get(f"/api/tasks/{task_id}", headers=USER_A_HEADERS).status_code == 200
    assert client.get(f"/api/share/{token}").status_code == 404


def test_admin_token_is_verified_and_required_for_management(client):
    created = client.post("/api/tasks", json=_payload(), headers=USER_A_HEADERS)
    task_id = created.json()["id"]

    assert client.get("/api/admin/status").status_code == 401
    assert client.get("/api/admin/status", headers=ADMIN_HEADERS).json() == {"authenticated": True}
    assert client.delete(f"/api/tasks/{task_id}", headers=USER_A_HEADERS).status_code == 401
    assert client.delete(f"/api/tasks/{task_id}", headers=ADMIN_HEADERS).status_code == 204


def test_admin_endpoints_are_disabled_when_server_token_is_missing(client, monkeypatch):
    monkeypatch.delenv("DIFF_LAB_ADMIN_TOKEN")
    assert client.get("/api/admin/status", headers=ADMIN_HEADERS).status_code == 503
    assert client.get("/api/tasks", headers=USER_A_HEADERS).status_code == 200


def test_csv_export_prefixes_spreadsheet_formulas_and_uses_utf8_bom(client):
    created = client.post(
        "/api/tasks",
        json=_payload(column_a="=2+2\nnormal", column_b="other"),
        headers=USER_A_HEADERS,
    )

    exported = client.get(f"/api/tasks/{created.json()['id']}/export", headers=USER_A_HEADERS)
    assert exported.status_code == 200
    assert exported.content.startswith("\ufeff".encode())
    assert "'=2+2" in exported.text
