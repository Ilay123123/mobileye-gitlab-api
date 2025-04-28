import pytest
import json
from unittest.mock import patch, MagicMock
import gitlab_util
import os


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_variables(monkeypatch):
    """Set up environment variables for testing"""
    monkeypatch.setenv("GITLAB_TOKEN", "fake_token_for_testing")
    monkeypatch.setenv("GITLAB_URL", "https://gitlab.com/")

    # Also patch the TOKEN and HEADERS variables directly
    # This is needed because these might be initialized at module import time
    monkeypatch.setattr(gitlab_util, "TOKEN", "fake_token_for_testing")
    monkeypatch.setattr(gitlab_util, "HEADERS", {"PRIVATE-TOKEN": "fake_token_for_testing"})


@pytest.fixture
def mock_user_response():
    """Fixture to return a mock user response"""
    return [
        {
            "id": 123,
            "username": "test_user",
            "name": "Test User",
            "state": "active"
        }
    ]


@pytest.fixture
def mock_issues_response():
    """Fixture to return mock issues"""
    return [
        {
            "id": 1,
            "iid": 101,
            "title": "First test issue",
            "state": "opened",
            "created_at": "2023-01-01T10:00:00Z",
            "web_url": "https://gitlab.com/test-group/test-project/-/issues/101",
            "author": {
                "username": "test_user",
                "id": 123
            }
        },
        {
            "id": 2,
            "iid": 102,
            "title": "Second test issue",
            "state": "closed",
            "created_at": "2023-02-01T10:00:00Z",
            "web_url": "https://gitlab.com/test-group/test-project/-/issues/102",
            "author": {
                "username": "another_user",
                "id": 456
            }
        }
    ]


class TestModifyPermission:
    """Tests for the modify_permission function"""

    def test_validate_inputs_with_valid_data(self):
        """Test validation with valid inputs"""
        errors = gitlab_util.validate_inputs(
            username="test_user",
            target="test-group",
            role="developer"
        )
        assert errors == []

    def test_validate_inputs_with_invalid_role(self):
        """Test validation with invalid role"""
        errors = gitlab_util.validate_inputs(
            username="test_user",
            target="test-group",
            role="invalid_role"
        )
        assert len(errors) > 0
        assert any("Invalid role" in error for error in errors)

    @patch("requests.get")
    @patch("requests.post")
    def test_modify_permission_success(self, mock_post, mock_get, mock_user_response):
        """Test successful permission modification"""
        # Mock the API responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_user_response

        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": 123, "access_level": 30}

        # Call the function
        result = gitlab_util.modify_permission("test_user", "test-group", "developer")

        # Check the result
        assert result["status"] == "success"
        assert "Successfully set test_user's role" in result["message"]

    @patch("requests.get")
    def test_modify_permission_user_not_found(self, mock_get):
        """Test permission modification when user not found"""
        # Mock the API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []

        # Call the function
        result = gitlab_util.modify_permission("nonexistent_user", "test-group", "developer")

        # Check the result
        assert result["status"] == "error"
        assert "User 'nonexistent_user' not found" in result["message"]


class TestGetItemsByYear:
    """Tests for the get_items_by_year function"""

    def test_validate_inputs_with_valid_data(self):
        """Test validation with valid inputs"""
        errors = gitlab_util.validate_inputs(
            item_type="issues",
            year="2023"
        )
        assert errors == []

    def test_validate_inputs_with_invalid_item_type(self):
        """Test validation with invalid item type"""
        errors = gitlab_util.validate_inputs(
            item_type="invalid_type",
            year="2023"
        )
        assert len(errors) > 0
        assert any("Invalid item type" in error for error in errors)

    def test_validate_inputs_with_invalid_year(self):
        """Test validation with invalid year"""
        errors = gitlab_util.validate_inputs(
            item_type="issues",
            year="9999"
        )
        assert len(errors) > 0
        assert any("Invalid year" in error for error in errors)

    @patch("requests.get")
    def test_get_items_by_year_success(self, mock_get, mock_issues_response):
        """Test successful retrieval of items by year"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues_response

        # First call returns data, second call returns empty list to end pagination
        mock_get.side_effect = [mock_response, MagicMock(status_code=200, json=MagicMock(return_value=[]))]

        # Call the function
        result = gitlab_util.get_items_by_year("issues", "2023")

        # Check the result
        assert result["status"] == "success"
        assert "Retrieved 2 issues from 2023" in result["message"]
        assert len(result["data"]) == 2

        # Verify the filtered fields
        for item in result["data"]:
            assert set(item.keys()) == {"id", "iid", "title", "state", "created_at", "web_url", "author"}

    @patch("requests.get")
    def test_get_items_by_year_api_error(self, mock_get):
        """Test error handling for API errors"""
        # Mock the API response
        mock_get.return_value.status_code = 401
        mock_get.return_value.text = "Unauthorized"

        # Call the function
        result = gitlab_util.get_items_by_year("issues", "2023")

        # Check the result
        assert result["status"] == "error"
        assert "401" in result["message"]


if __name__ == "__main__":
    pytest.main(["-v", "test_gitlab_util.py"])