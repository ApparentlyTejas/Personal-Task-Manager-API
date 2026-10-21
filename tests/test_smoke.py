"""
Minimal smoke tests for the Task Manager API.

These are intentionally narrow: a health check and one full CRUD
round-trip. They exist so coverage/CI have something real to measure,
not as a substitute for a full test suite (see README's "Known gaps").
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


async def test_task_crud_round_trip(client: AsyncClient) -> None:
    # Create
    create_resp = await client.post(
        "/tasks",
        json={"title": "Write tests", "description": "Add CI coverage", "status": "pending"},
    )
    assert create_resp.status_code == 200
    task = create_resp.json()
    task_id = task["id"]
    assert task["title"] == "Write tests"
    assert task["status"] == "pending"

    # Read (single)
    get_resp = await client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task_id

    # Read (list)
    list_resp = await client.get("/tasks")
    assert list_resp.status_code == 200
    assert any(t["id"] == task_id for t in list_resp.json())

    # Update
    update_resp = await client.patch(f"/tasks/{task_id}", json={"status": "completed"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "completed"

    # Delete
    delete_resp = await client.delete(f"/tasks/{task_id}")
    assert delete_resp.status_code == 200

    # Verify deletion
    missing_resp = await client.get(f"/tasks/{task_id}")
    assert missing_resp.status_code == 404


async def test_get_missing_task_returns_404(client: AsyncClient) -> None:
    response = await client.get("/tasks/999999")
    assert response.status_code == 404
