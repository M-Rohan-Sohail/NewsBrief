from fastapi.testclient import TestClient
from main import app
from db import get_db
from models import User
from auth import get_current_user
import uuid
import datetime

client = TestClient(app)

mock_user_id = uuid.uuid4()
mock_user = User(id=mock_user_id, email="test@example.com")

def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

def test_analytics_flow():
    class MockDB:
        def __init__(self):
            self.events = []

        def query(self, model):
            class QueryMock:
                def __init__(self, db, model):
                    self.db = db
                    self.model = model
                
                def filter(self, *args, **kwargs):
                    return self
                    
                def order_by(self, *args, **kwargs):
                    return self
                    
                def limit(self, *args, **kwargs):
                    return self
                    
                def count(self):
                    return 1
                    
                def distinct(self):
                    return self
                    
                def all(self):
                    return self.db.events
                    
                def first(self):
                    return mock_user
            return QueryMock(self, model)
            
        def execute(self, statement):
            class ResultMock:
                def fetchall(self):
                    return [(mock_user_id, "app", 5)]
            return ResultMock()
            
        def add(self, item):
            if item.__class__.__name__ == 'UserEventLog':
                item.id = uuid.uuid4()
                item.created_at = datetime.datetime.now(datetime.timezone.utc)
                self.events.append(item)
                
        def delete(self, item):
            pass
            
        def commit(self):
            pass
            
        def refresh(self, item):
            pass

    mock_db = MockDB()
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db

    # Test POST /analytics/event
    response = client.post("/analytics/event", json={
        "channel": "app",
        "event_name": "app_session",
        "properties": {"session_seconds": 120}
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Test GET /analytics/email-open
    response = client.get(f"/analytics/email-open/{mock_user_id}/2026-09-20")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    
    # Test GET /analytics/email-click
    response = client.get(f"/analytics/email-click/{mock_user_id}/cluster-123", follow_redirects=False)
    assert response.status_code == 302
    
    # Test GET /admin/analytics
    response = client.get("/admin/analytics?key=mysecret")
    assert response.status_code == 200
    data = response.json()
    assert "channel_breakdown" in data
    assert "total_users" in data
