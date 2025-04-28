import pytest
import json
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_check(self, client):
        """Test that the health check endpoint returns ok"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'


class TestPermissionEndpoint:
    """Tests for the permission endpoint"""

    @patch('gitlab_util.modify_permission')
    def test_permission_endpoint_success(self, mock_modify_permission, client):
        """Test successful permission modification via the API"""
        # Mock the response from the gitlab_util function
        mock_modify_permission.return_value = {
            'status': 'success',
            'message': 'Successfully set test_user\'s role to developer on test-group',
            'data': {'id': 123, 'access_level': 30}
        }

        # Make the API request
        response = client.post(
            '/permission',
            json={
                'username': 'test_user',
                'target': 'test-group',
                'role': 'developer'
            }
        )

        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'Successfully set test_user\'s role' in data['message']

    @patch('gitlab_util.modify_permission')
    def test_permission_endpoint_error(self, mock_modify_permission, client):
        """Test error handling in permission endpoint"""
        # Mock an error response
        mock_modify_permission.return_value = {
            'status': 'error',
            'message': 'User not found'
        }

        # Make the API request
        response = client.post(
            '/permission',
            json={
                'username': 'nonexistent_user',
                'target': 'test-group',
                'role': 'developer'
            }
        )

        # Check the response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'User not found' in data['message']

    def test_permission_endpoint_missing_params(self, client):
        """Test validation of required parameters"""
        # Make the API request with missing parameters
        response = client.post(
            '/permission',
            json={
                'username': 'test_user',
                # Missing 'target' and 'role'
            }
        )

        # Check the response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing required parameters' in data['message']


class TestItemsEndpoint:
    """Tests for the items endpoint"""

    @patch('gitlab_util.get_items_by_year')
    def test_items_endpoint_success(self, mock_get_items, client):
        """Test successful retrieval of items via the API"""
        # Mock the response from the gitlab_util function
        mock_get_items.return_value = {
            'status': 'success',
            'message': 'Retrieved 2 issues from 2023',
            'data': [
                {
                    'id': 1,
                    'iid': 101,
                    'title': 'Test Issue 1',
                    'state': 'opened',
                    'created_at': '2023-01-01T10:00:00Z',
                    'web_url': 'https://gitlab.com/test/project/-/issues/101',
                    'author': 'test_user'
                },
                {
                    'id': 2,
                    'iid': 102,
                    'title': 'Test Issue 2',
                    'state': 'closed',
                    'created_at': '2023-02-01T10:00:00Z',
                    'web_url': 'https://gitlab.com/test/project/-/issues/102',
                    'author': 'another_user'
                }
            ]
        }

        # Make the API request
        response = client.get('/items?type=issues&year=2023')

        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'Retrieved 2 issues from 2023' in data['message']
        assert len(data['data']) == 2

    @patch('gitlab_util.get_items_by_year')
    def test_items_endpoint_error(self, mock_get_items, client):
        """Test error handling in items endpoint"""
        # Mock an error response
        mock_get_items.return_value = {
            'status': 'error',
            'message': 'Invalid year'
        }

        # Make the API request
        response = client.get('/items?type=issues&year=9999')

        # Check the response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid year' in data['message']

    def test_items_endpoint_missing_params(self, client):
        """Test validation of required parameters"""
        # Make the API request with missing parameters
        response = client.get('/items?type=issues')  # Missing 'year'

        # Check the response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Missing required parameter: year' in data['message']


if __name__ == "__main__":
    pytest.main(["-v", "test_app.py"])