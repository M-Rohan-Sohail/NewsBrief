from fastapi.testclient import TestClient
from main import app
from db import get_db
from unittest.mock import MagicMock
from models import User, BetaFeedback, FeedbackVote
from auth import get_current_user
import uuid
import datetime
from schemas import FeedbackCreate

client = TestClient(app)

mock_user_id = uuid.uuid4()
mock_user = User(id=mock_user_id, email="test@example.com")

def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

def test_feedback_flow():
    # Setup mock DB
    class MockDB:
        def __init__(self):
            self.feedbacks = []
            self.votes = []

        def query(self, model):
            class QueryMock:
                def __init__(self, db, model):
                    self.db = db
                    self.model = model
                
                def filter(self, *args, **kwargs):
                    return self
                    
                def order_by(self, *args, **kwargs):
                    return self
                    
                def all(self):
                    if hasattr(self.model, '__name__') and self.model.__name__ == 'BetaFeedback':
                        return self.db.feedbacks
                    if hasattr(self.model, '__name__') and self.model.__name__ == 'FeedbackVote':
                        return self.db.votes
                    return []
                    
                def first(self):
                    if hasattr(self.model, '__name__') and self.model.__name__ == 'BetaFeedback' and len(self.db.feedbacks) > 0:
                        return self.db.feedbacks[0]
                    return None
            return QueryMock(self, model)
            
        def add(self, item):
            if item.__class__.__name__ == 'BetaFeedback':
                item.id = uuid.uuid4()
                item.created_at = datetime.datetime.now(datetime.timezone.utc)
                if not getattr(item, 'status', None):
                    item.status = "under_review"
                self.feedbacks.append(item)
            elif item.__class__.__name__ == 'FeedbackVote':
                self.votes.append(item)
                
        def delete(self, item):
            pass
            
        def flush(self):
            pass
            
        def commit(self):
            pass
            
        def refresh(self, item):
            pass

    mock_db = MockDB()
    def override_get_db():
        yield mock_db
        
    app.dependency_overrides[get_db] = override_get_db

    # Test Create
    response = client.post("/feedback", json={"title": "Test Feedback", "description": "This is a test", "category": "feature"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Feedback"
    assert data["upvotes_count"] == 1
    assert data["has_upvoted"] == True
    feedback_id = data["id"]
    
    # Test List
    response = client.get("/feedback?sort_by=upvotes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    # Test Admin Status Update
    response = client.patch(f"/admin/feedback/{feedback_id}/status?key=mysecret", json={"status": "planned"})
    assert response.status_code == 200
    assert response.json()["new_status"] == "planned"
