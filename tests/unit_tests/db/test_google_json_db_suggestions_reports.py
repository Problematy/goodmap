# pyright: reportArgumentType=false, reportCallIssue=false
"""Tests for google_json_db suggestions and reports functionality."""

import json
from unittest import mock

import pytest
from platzky.db.google_json_db import GoogleJsonDb

from goodmap.db import (
    google_json_db_add_report,
    google_json_db_add_suggestion,
    google_json_db_delete_report,
    google_json_db_delete_suggestion,
    google_json_db_get_report,
    google_json_db_get_reports,
    google_json_db_get_reports_paginated,
    google_json_db_get_suggestion,
    google_json_db_get_suggestions,
    google_json_db_get_suggestions_paginated,
    google_json_db_update_report,
    google_json_db_update_suggestion,
)

# Test data
data = {
    "data": [
        {"position": [50, 50], "uuid": "1", "name": "one"},
        {"position": [10, 10], "uuid": "2", "name": "two"},
    ],
    "categories": {"test-category": ["searchable", "unsearchable"]},
    "location_obligatory_fields": [["name", "str"]],
}
data_json = json.dumps({"map": data})


@pytest.fixture
def mock_cli():
    """Mock Google Cloud Storage client."""
    with mock.patch("platzky.db.google_json_db.Client"):
        yield


# ------------------------------------------------
# Suggestion tests
# ------------------------------------------------


def test_google_json_db_add_suggestion(mock_cli):
    """Test that google_json_db_add_suggestion is a no-op (read-only)."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        suggestion = {"uuid": "s1", "foo": "bar"}
        # Should not raise an error, just a no-op
        result = google_json_db_add_suggestion(db, suggestion)
        assert result is None


def test_google_json_db_get_suggestions(mock_cli):
    """Test that google_json_db_get_suggestions returns empty list."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        suggestions = google_json_db_get_suggestions(db, {})
        assert suggestions == []

        # Test with status filter
        suggestions = google_json_db_get_suggestions(db, {"status": ["pending"]})
        assert suggestions == []


def test_google_json_db_get_suggestions_paginated(mock_cli):
    """Test that google_json_db_get_suggestions_paginated returns empty paginated response."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        query = {"page": ["1"], "per_page": ["10"]}
        result = google_json_db_get_suggestions_paginated(db, query)
        assert result["items"] == []
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 10


def test_google_json_db_get_suggestion(mock_cli):
    """Test that google_json_db_get_suggestion returns None."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        suggestion = google_json_db_get_suggestion(db, "s1")
        assert suggestion is None


def test_google_json_db_update_suggestion(mock_cli):
    """Test that google_json_db_update_suggestion is a no-op (read-only)."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        # Should not raise an error, just a no-op
        result = google_json_db_update_suggestion(db, "s1", "accepted")
        assert result is None


def test_google_json_db_delete_suggestion(mock_cli):
    """Test that google_json_db_delete_suggestion is a no-op (read-only)."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        # Should not raise an error, just a no-op
        result = google_json_db_delete_suggestion(db, "s1")
        assert result is None


# ------------------------------------------------
# Report tests
# ------------------------------------------------


def test_google_json_db_add_report(mock_cli):
    """Test that google_json_db_add_report is a no-op (read-only)."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        report = {"uuid": "r1", "location_id": "loc1", "description": "Issue"}
        # Should not raise an error, just a no-op
        result = google_json_db_add_report(db, report)
        assert result is None


def test_google_json_db_get_reports(mock_cli):
    """Test that google_json_db_get_reports returns empty list."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        reports = google_json_db_get_reports(db, {})
        assert reports == []

        # Test with filters
        reports = google_json_db_get_reports(db, {"status": ["pending"], "priority": ["high"]})
        assert reports == []


def test_google_json_db_get_reports_paginated(mock_cli):
    """Test that google_json_db_get_reports_paginated returns empty paginated response."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        query = {"page": ["1"], "per_page": ["20"]}
        result = google_json_db_get_reports_paginated(db, query)
        assert result["items"] == []
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["per_page"] == 20


def test_google_json_db_get_report(mock_cli):
    """Test that google_json_db_get_report returns None."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        report = google_json_db_get_report(db, "r1")
        assert report is None


def test_google_json_db_update_report(mock_cli):
    """Test that google_json_db_update_report is a no-op (read-only)."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        # Should not raise an error, just a no-op
        result = google_json_db_update_report(db, "r1", status="resolved", priority="low")
        assert result is None


def test_google_json_db_delete_report(mock_cli):
    """Test that google_json_db_delete_report is a no-op (read-only)."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        # Should not raise an error, just a no-op
        result = google_json_db_delete_report(db, "r1")
        assert result is None


# ------------------------------------------------
# Integration tests
# ------------------------------------------------


def test_google_json_db_suggestions_reports_integration(mock_cli):
    """Test that all suggestion/report methods work together without errors."""
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        # Add operations (no-ops)
        google_json_db_add_suggestion(db, {"uuid": "s1"})
        google_json_db_add_report(db, {"uuid": "r1"})

        # Get operations (return empty/None)
        assert google_json_db_get_suggestions(db, {}) == []
        assert google_json_db_get_suggestion(db, "s1") is None
        assert google_json_db_get_reports(db, {}) == []
        assert google_json_db_get_report(db, "r1") is None

        # Update operations (no-ops)
        google_json_db_update_suggestion(db, "s1", "accepted")
        google_json_db_update_report(db, "r1", status="resolved")

        # Delete operations (no-ops)
        google_json_db_delete_suggestion(db, "s1")
        google_json_db_delete_report(db, "r1")

        # Verify everything still returns empty
        assert google_json_db_get_suggestions(db, {}) == []
        assert google_json_db_get_reports(db, {}) == []
