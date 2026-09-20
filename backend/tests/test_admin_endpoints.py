from fastapi.testclient import TestClient
from main import app
from db import get_db
from unittest.mock import MagicMock, patch
from fastapi import BackgroundTasks

client = TestClient(app)

def override_get_db():
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    yield mock_db

app.dependency_overrides[get_db] = override_get_db

# Patch add_task globally for the tests
patcher = patch.object(BackgroundTasks, 'add_task')
patcher.start()



def test_get_admin_dashboard_no_auth():
    response = client.get("/admin")
    assert response.status_code == 403

def test_get_admin_dashboard_with_auth():
    response = client.get("/admin?key=mysecret")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NewsBrief Admin Dashboard" in response.text

def test_get_admin_stats_no_auth():
    response = client.get("/admin/stats")
    assert response.status_code == 403

def test_get_admin_stats_with_auth():
    response = client.get("/admin/stats?key=mysecret")
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "sources_health" in data

def test_trigger_stage1_no_auth():
    response = client.post("/admin/trigger-stage1")
    assert response.status_code == 403

def test_trigger_stage1_with_auth():
    response = client.post("/admin/trigger-stage1?key=mysecret")
    assert response.status_code == 200
    assert response.json()["status"] == "Stage 1 Pipeline triggered in background"

def test_trigger_stage2_with_auth():
    response = client.post("/admin/trigger-stage2?key=mysecret")
    assert response.status_code == 200
    assert response.json()["status"] == "Stage 2 Pipeline triggered in background"

def test_trigger_deliveries_with_auth():
    response = client.post("/admin/trigger-deliveries?key=mysecret")
    assert response.status_code == 200
    assert response.json()["status"] == "Deliveries triggered in background"

def test_test_email_with_auth():
    response = client.post("/admin/test-email?key=mysecret", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert "Test email triggered" in response.json()["status"]
