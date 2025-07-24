from uuid import UUID
from fastapi.testclient import TestClient
import pytest
from agents.runner import get_agentic_analytics_task_manager
from db_models import Profile
from main import app
from uuid import uuid4
from datetime import datetime, timezone
from routers.deps import get_current_user

client = TestClient(app)


@pytest.fixture(scope="function")
def inject_db_session_factory(db_session_factory):
    app.state.db_session_factory = db_session_factory
    yield
    del app.state.db_session_factory


@pytest.fixture(scope="function")
def agentic_analytics_task_manager(config_for_test, inject_db_session_factory):
    return get_agentic_analytics_task_manager(config_for_test)


MOCK_USER_ID = uuid4()
MOCK_USER_EMAIL = f"{str(MOCK_USER_ID)[:8]}@example.com"


class MockUser:
    def __init__(self, id=None, email=None):
        self.id = id or MOCK_USER_ID
        self.email = email or MOCK_USER_EMAIL


@pytest.fixture(scope="function")
def mock_user():
    return MockUser(id=MOCK_USER_ID, email=MOCK_USER_EMAIL)


@pytest.fixture(scope="function")
def create_profile(db_session, mock_user):
    profile = Profile(id=mock_user.id, name=mock_user.email)
    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture(scope="function")
def override_get_current_user(create_profile, mock_user):
    def _mock_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def unique_name(prefix):
    return f"{prefix}_{uuid4()}"


# --- Repo CRUD ---
def test_repo_crud(
    db_session,
    agentic_analytics_task_manager,
    override_get_current_user,
):
    repo_data = {
        "name": unique_name("repo"),
        "description": "A test repo",
        "url": "https://github.com/test/test",
    }
    # Create
    resp = client.post("/repo/", json=repo_data)
    assert resp.status_code == 201
    repo = resp.json()
    repo_id = UUID(repo["id"])
    # Read
    resp = client.get(f"/repo/{repo_id}")
    assert resp.status_code == 200
    # Update
    update_data = {"name": unique_name("repo_updated")}
    resp = client.put(f"/repo/{repo_id}", json=update_data)
    assert resp.status_code == 200
    assert resp.json()["name"] == update_data["name"]
    # List
    resp = client.get("/repo/")
    assert resp.status_code == 200
    assert any(r["id"] == str(repo_id) for r in resp.json())
    # Delete
    resp = client.delete(f"/repo/{repo_id}")
    assert resp.status_code == 204
    # Confirm gone
    resp = client.get(f"/repo/{repo_id}")
    assert resp.status_code == 404


# --- Plan CRUD ---
def test_plan_crud(
    db_session,
    agentic_analytics_task_manager,
    override_get_current_user,
):
    # Create a repo first
    repo_data = {
        "name": unique_name("repo"),
        "description": "A test repo",
        "url": "https://github.com/test/test",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    repo_resp = client.post("/repo/", json=repo_data)
    assert repo_resp.status_code == 201
    repo_id = UUID(repo_resp.json()["id"])

    plan_data = {
        "name": unique_name("plan"),
        "description": "A test plan",
        "status": "active",
        "version": "1.0",
        "import_source": "",
    }
    plan_resp = client.post("/plans/", json=plan_data)
    assert plan_resp.status_code == 201
    plan_id = UUID(plan_resp.json()["id"])

    add_repos_to_plan_data = {
        "repo_ids": [str(repo_id)],
    }
    add_repos_to_plan_resp = client.post(
        f"/plans/{plan_id}/repos", json=add_repos_to_plan_data
    )
    assert add_repos_to_plan_resp.status_code == 200
    assert add_repos_to_plan_resp.json() == [repo_resp.json()]
    assert len(add_repos_to_plan_resp.json()) == 1
    assert add_repos_to_plan_resp.json()[0]["id"] == str(repo_id)

    # Read
    resp = client.get(f"/repo/plans/{plan_id}")
    assert resp.status_code == 200
    # Update
    update_data = {"name": unique_name("plan_updated")}
    resp = client.put(f"/repo/plans/{plan_id}", json=update_data)
    assert resp.status_code == 200
    assert resp.json()["name"] == update_data["name"]
    # List
    resp = client.get(f"/repo/{repo_id}/plans")
    assert resp.status_code == 200
    assert any(p["id"] == str(plan_id) for p in resp.json()), resp.json()
    # Delete
    resp = client.delete(f"/repo/plans/{plan_id}")
    assert resp.status_code == 204
    # Confirm gone
    resp = client.get(f"/repo/plans/{plan_id}")
    assert resp.status_code == 404
    # Repo should still exist
    resp = client.get(f"/repo/{repo_id}")
    assert resp.status_code == 200


# --- UserEvent CRUD ---
def test_user_event_crud(
    db_session, agentic_analytics_task_manager, override_get_current_user
):
    # Create repo and plan first
    repo_data = {
        "name": unique_name("repo"),
        "description": "A test repo",
        "url": "https://github.com/test/test",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    repo_resp = client.post("/repo/", json=repo_data)
    assert repo_resp.status_code == 201, repo_resp.json()
    repo_id = UUID(repo_resp.json()["id"])
    plan_data = {
        "name": unique_name("plan"),
        "description": "A test plan",
        "status": "active",
        "version": "1.0",
        "import_source": "",
    }
    plan_resp = client.post("/repo/plans", json=plan_data)
    plan_id = UUID(plan_resp.json()["id"])
    event_data = {
        "plan_id": str(plan_id),
        "repo_id": str(repo_id),
        "event_name": unique_name("event"),
        "context": "ctx",
        "tags": ["tag1", "tag2"],
        "file_path": "file.py",
        "line_number": 42,
    }
    # Create
    resp = client.post("/repo/events", json=event_data)
    assert resp.status_code == 201
    event = resp.json()
    event_id = UUID(event["id"])
    # Read (list for plan)
    resp = client.get(f"/repo/plans/{plan_id}/events")
    assert resp.status_code == 200
    assert any(e["id"] == str(event_id) for e in resp.json())
    # Update
    update_data = {"event_name": unique_name("event_updated")}
    resp = client.put(f"/repo/events/{event_id}", json=update_data)
    assert resp.status_code == 200
    assert resp.json()["event_name"] == update_data["event_name"]
    # Delete
    resp = client.delete(f"/repo/events/{event_id}")
    assert resp.status_code == 204
    # Confirm gone
    resp = client.get(f"/repo/plans/{plan_id}/events")
    assert not any(e["id"] == str(event_id) for e in resp.json())


# --- Cascade/Non-cascade delete logic ---
def test_delete_repo_cascades_user_events(
    db_session, agentic_analytics_task_manager, override_get_current_user
):
    # Create repo, plan, event
    repo_data = {
        "name": unique_name("repo"),
        "description": "A test repo",
        "url": "https://github.com/test/test",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    repo_resp = client.post("/repo/", json=repo_data)
    repo_id = UUID(repo_resp.json()["id"])
    plan_data = {
        "repo_id": str(repo_id),
        "name": unique_name("plan"),
        "description": "A test plan",
        "status": "active",
        "version": "1.0",
        "import_source": "",
    }
    plan_resp = client.post("/repo/plans", json=plan_data)
    plan_id = UUID(plan_resp.json()["id"])
    event_data = {
        "plan_id": str(plan_id),
        "repo_id": str(repo_id),
        "event_name": unique_name("event"),
        "context": "ctx",
        "tags": ["tag1"],
        "file_path": "file.py",
        "line_number": 1,
    }
    event_resp = client.post("/repo/events", json=event_data)
    event_id = UUID(event_resp.json()["id"])
    # Delete repo
    resp = client.delete(f"/repo/{repo_id}")
    assert resp.status_code == 204
    # UserEvent should be deleted
    resp = client.get(f"/repo/plans/{plan_id}/events")
    assert all(e["id"] != str(event_id) for e in resp.json())
    # Plan should still exist
    resp = client.get(f"/repo/plans/{plan_id}")
    assert resp.status_code == 200


def test_delete_plan_does_not_affect_repo_or_user_events(
    db_session, agentic_analytics_task_manager, override_get_current_user
):
    # Create repo, plan, event
    repo_data = {
        "name": unique_name("repo"),
        "description": "A test repo",
        "url": "https://github.com/test/test",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    repo_resp = client.post("/repo/", json=repo_data)
    repo_id = repo_resp.json()["id"]
    plan_data = {
        "repo_id": str(repo_id),
        "name": unique_name("plan"),
        "description": "A test plan",
        "status": "active",
        "version": "1.0",
        "import_source": "",
    }
    plan_resp = client.post("/repo/plans", json=plan_data)
    plan_id = plan_resp.json()["id"]
    event_data = {
        "plan_id": str(plan_id),
        "repo_id": str(repo_id),
        "event_name": unique_name("event"),
        "context": "ctx",
        "tags": ["tag1"],
        "file_path": "file.py",
        "line_number": 1,
    }
    event_resp = client.post("/repo/events", json=event_data)
    event_id = event_resp.json()["id"]
    # Delete plan
    resp = client.delete(f"/repo/plans/{plan_id}")
    assert resp.status_code == 204
    # Repo should still exist
    resp = client.get(f"/repo/{repo_id}")
    assert resp.status_code == 200
    # UserEvent should still exist
    resp = client.get(f"/events/{event_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(event_id)
