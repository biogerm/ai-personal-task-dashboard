import pytest
from unittest.mock import patch
from src.app import create_app

from unittest.mock import MagicMock

@pytest.fixture
def app():
    # Use a dummy config to avoid using real tokens
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    
    # Attach a mock merger just like server/app.py does
    mock_merger = MagicMock()
    mock_merger.get_data.return_value = {
        "projects": [
            {"id": "1", "title": "Test Project", "urgency": "today"}
        ],
        "reminders": [],
        "sources": {"notion": {"status": "ok"}, "reminders": {"status": "ok"}}
    }
    app.merger = mock_merger
    
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'

def test_tasks_endpoint(client):
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert "projects" in data
    assert len(data["projects"]) == 1
    assert data["projects"][0]["title"] == "Test Project"
