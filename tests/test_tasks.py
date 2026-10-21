"""
Deeper behavioral tests for the Task Manager API.

Unlike tests/test_smoke.py (one health check + one happy-path round trip),
these tests exercise validation errors, every 404 path, partial updates,
multi-row listing, status-field transitions, and edge-case input. They
follow the same fixture pattern as test_smoke.py (tests/conftest.py's
`client` fixture, which talks to a real disposable Postgres instance via
DATABASE_URL, reset before every test).
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app

pytestmark = pytest.mark.asyncio


# ===== Validation errors (422) =====

async def test_create_task_missing_title_returns_422(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"description": "no title here"})
    assert response.status_code == 422


async def test_create_task_null_title_returns_422(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": None})
    assert response.status_code == 422


async def test_create_task_title_wrong_type_returns_422(client: AsyncClient) -> None:
    # Pydantic v2 does not coerce int -> str for a plain `str` field.
    response = await client.post("/tasks", json={"title": 12345})
    assert response.status_code == 422


async def test_create_task_status_wrong_type_returns_422(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": "Valid title", "status": 123})
    assert response.status_code == 422


async def test_create_task_empty_body_returns_422(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={})
    assert response.status_code == 422


async def test_update_task_wrong_type_returns_422(client: AsyncClient) -> None:
    create_resp = await client.post("/tasks", json={"title": "Task to update"})
    task_id = create_resp.json()["id"]

    response = await client.patch(f"/tasks/{task_id}", json={"title": 999})
    assert response.status_code == 422

    # Confirm the bad update did not get applied.
    get_resp = await client.get(f"/tasks/{task_id}")
    assert get_resp.json()["title"] == "Task to update"


# ===== 404s for every resource-not-found path =====

async def test_get_missing_task_returns_404(client: AsyncClient) -> None:
    response = await client.get("/tasks/999999")
    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


async def test_update_missing_task_returns_404(client: AsyncClient) -> None:
    response = await client.patch("/tasks/999999", json={"status": "completed"})
    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


async def test_delete_missing_task_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/tasks/999999")
    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


async def test_get_task_after_deletion_returns_404(client: AsyncClient) -> None:
    create_resp = await client.post("/tasks", json={"title": "Temp task"})
    task_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/tasks/{task_id}")
    assert delete_resp.status_code == 200

    get_resp = await client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404

    # Deleting it again (already gone) is also a 404, not a silent success.
    second_delete_resp = await client.delete(f"/tasks/{task_id}")
    assert second_delete_resp.status_code == 404


# NOTE: this API has no uniqueness/ownership constraints anywhere (titles
# can repeat freely, there is no auth), so there is no 400/409 conflict
# path to exercise. Confirmed by reading main.py/models.py in full: every
# non-404 failure mode is a plain pydantic 422.


# ===== Partial updates (PATCH) preserve untouched fields =====

async def test_partial_update_preserves_other_fields(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/tasks",
        json={"title": "Original title", "description": "Original description", "status": "pending"},
    )
    task = create_resp.json()
    task_id = task["id"]

    # Only touch status.
    update_resp = await client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["status"] == "in_progress"
    assert updated["title"] == "Original title"
    assert updated["description"] == "Original description"
    assert updated["created_at"] == task["created_at"]

    # Only touch title this time; status/description from the previous
    # update must survive.
    update_resp_2 = await client.patch(f"/tasks/{task_id}", json={"title": "New title"})
    assert update_resp_2.status_code == 200
    updated_2 = update_resp_2.json()
    assert updated_2["title"] == "New title"
    assert updated_2["status"] == "in_progress"
    assert updated_2["description"] == "Original description"


async def test_empty_patch_body_is_a_no_op(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/tasks", json={"title": "Untouched", "description": "Stays the same", "status": "pending"}
    )
    task = create_resp.json()

    update_resp = await client.patch(f"/tasks/{task['id']}", json={})
    assert update_resp.status_code == 200
    assert update_resp.json() == task


async def test_update_description_to_null_clears_it(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/tasks", json={"title": "Has a description", "description": "Will be cleared"}
    )
    task_id = create_resp.json()["id"]

    update_resp = await client.patch(f"/tasks/{task_id}", json={"description": None})
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] is None
    # Title must be untouched.
    assert update_resp.json()["title"] == "Has a description"


# ===== Listing with realistic multi-row data =====

async def test_list_tasks_returns_all_created_tasks_with_correct_data(client: AsyncClient) -> None:
    created = []
    for i in range(5):
        resp = await client.post(
            "/tasks",
            json={"title": f"Task {i}", "description": f"Description {i}", "status": "pending"},
        )
        created.append(resp.json())

    list_resp = await client.get("/tasks")
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert len(tasks) == 5

    by_id = {t["id"]: t for t in tasks}
    for task in created:
        assert task["id"] in by_id
        assert by_id[task["id"]]["title"] == task["title"]
        assert by_id[task["id"]]["description"] == task["description"]


async def test_list_tasks_reflects_mixed_statuses_and_deletions(client: AsyncClient) -> None:
    ids = []
    for status in ["pending", "in_progress", "completed"]:
        resp = await client.post("/tasks", json={"title": f"{status} task", "status": status})
        ids.append(resp.json()["id"])

    # Delete the middle one.
    await client.delete(f"/tasks/{ids[1]}")

    list_resp = await client.get("/tasks")
    tasks = list_resp.json()
    assert len(tasks) == 2
    remaining_ids = {t["id"] for t in tasks}
    assert ids[0] in remaining_ids
    assert ids[1] not in remaining_ids
    assert ids[2] in remaining_ids


async def test_list_tasks_empty_when_no_tasks_exist(client: AsyncClient) -> None:
    response = await client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


# ===== Status-field transitions =====
#
# TaskDB.status is a plain String(50) column and TaskUpdate.status is a
# plain `str | None`; there is no enum, no state machine, and no
# transition validation anywhere in main.py or models.py. The tests below
# confirm (not invent) that behavior: every transition -- forward,
# backward, or to a nonsense value -- is currently accepted as-is.

async def test_status_transition_pending_to_in_progress_to_completed(client: AsyncClient) -> None:
    create_resp = await client.post("/tasks", json={"title": "Lifecycle task", "status": "pending"})
    task_id = create_resp.json()["id"]

    resp_1 = await client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert resp_1.status_code == 200
    assert resp_1.json()["status"] == "in_progress"

    resp_2 = await client.patch(f"/tasks/{task_id}", json={"status": "completed"})
    assert resp_2.status_code == 200
    assert resp_2.json()["status"] == "completed"


async def test_status_transition_backwards_is_currently_allowed(client: AsyncClient) -> None:
    create_resp = await client.post("/tasks", json={"title": "Backslide task", "status": "completed"})
    task_id = create_resp.json()["id"]

    # Going from "completed" back to "pending" has no guard in the
    # current implementation -- document that, don't assert a 4xx that
    # doesn't actually happen.
    resp = await client.patch(f"/tasks/{task_id}", json={"status": "pending"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"


async def test_status_arbitrary_string_is_currently_accepted(client: AsyncClient) -> None:
    # No enum/constraint on status: any non-empty string round-trips.
    create_resp = await client.post("/tasks", json={"title": "Loose status", "status": "banana"})
    assert create_resp.status_code == 200
    assert create_resp.json()["status"] == "banana"

    update_resp = await client.patch(f"/tasks/{create_resp.json()['id']}", json={"status": "also-not-real"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "also-not-real"


# ===== Edge cases =====

async def test_create_task_with_empty_title_is_currently_accepted(client: AsyncClient) -> None:
    # `title: str` has no min_length, so an empty string passes pydantic
    # and is accepted by the DB (nullable=False just means "not NULL",
    # not "not empty").
    response = await client.post("/tasks", json={"title": ""})
    assert response.status_code == 200
    assert response.json()["title"] == ""


async def test_create_task_with_empty_description_is_accepted(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": "Has empty desc", "description": ""})
    assert response.status_code == 200
    assert response.json()["description"] == ""


async def test_create_task_default_status_when_omitted(client: AsyncClient) -> None:
    response = await client.post("/tasks", json={"title": "No status given"})
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


async def test_create_task_title_at_column_boundary_255_chars_succeeds(client: AsyncClient) -> None:
    # TaskDB.title is String(255); exactly 255 chars must fit.
    title = "x" * 255
    response = await client.post("/tasks", json={"title": title})
    assert response.status_code == 200
    assert response.json()["title"] == title
    assert len(response.json()["title"]) == 255


async def test_create_task_title_over_column_boundary_currently_500s(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # TaskDB.title is String(255), but neither TaskCreate (a plain `str`
    # with no max_length) nor the endpoint itself enforces that limit
    # before hitting the database. Postgres rejects the oversized value
    # at the VARCHAR(255) column, and main.py has no exception handler
    # for that -- so today this is an unhandled 500, not a 422. This test
    # documents that gap rather than asserting a validation response
    # that doesn't exist yet.
    #
    # A dedicated client (raise_app_exceptions=False) is used here
    # instead of the shared `client` fixture so the underlying
    # SQLAlchemy/asyncpg error surfaces as a 500 response rather than
    # propagating as a raw exception through the test.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/tasks", json={"title": "x" * 256})
        assert response.status_code == 500


async def test_get_task_invalid_id_type_returns_422(client: AsyncClient) -> None:
    # task_id is typed as `int` in the path; a non-numeric path segment
    # fails FastAPI's path-parameter validation before the handler runs.
    response = await client.get("/tasks/not-a-number")
    assert response.status_code == 422


async def test_create_task_with_whitespace_only_title_is_accepted(client: AsyncClient) -> None:
    # No strip()/min_length validation means whitespace-only strings are
    # indistinguishable from "real" content to this API today.
    response = await client.post("/tasks", json={"title": "   "})
    assert response.status_code == 200
    assert response.json()["title"] == "   "


async def test_lifespan_initializes_database() -> None:
    # main.lifespan() (startup print + init_db() + shutdown print) only
    # runs when something drives the ASGI lifespan protocol; the plain
    # ASGITransport used by the `client` fixture does not do that (by
    # design -- it only forwards HTTP requests), so it's otherwise never
    # exercised. Call it directly the way Starlette/Uvicorn would.
    from main import lifespan

    async with lifespan(app):
        pass


async def test_session_dependency_yields_usable_async_session() -> None:
    # Exercises database.get_session()'s generator body directly (it is
    # otherwise only ever invoked indirectly via FastAPI's Depends()).
    from database import get_session

    gen = get_session()
    session = await gen.__anext__()
    assert isinstance(session, AsyncSession)
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()
