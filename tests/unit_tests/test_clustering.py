"""Unit tests for goodmap.clustering module."""

from unittest import mock

from goodmap.clustering import (
    map_clustering_data_to_proper_lazy_loading_object,
    match_clusters_uuids,
)


def test_map_clustering_data_single_point():
    """Test mapping clustering data for a single point"""
    input_data = [{"longitude": 50.0, "latitude": 60.0, "count": 1, "uuid": "test-uuid"}]

    result = map_clustering_data_to_proper_lazy_loading_object(input_data)

    assert len(result) == 1
    assert result[0]["type"] == "point"
    assert result[0]["uuid"] == "test-uuid"
    assert result[0]["cluster_uuid"] is None
    assert result[0]["cluster_count"] is None
    assert result[0]["position"] == [50.0, 60.0]


def test_map_clustering_data_cluster():
    """Test mapping clustering data for a cluster"""
    input_data = [{"longitude": 50.0, "latitude": 60.0, "count": 5, "uuid": None}]

    result = map_clustering_data_to_proper_lazy_loading_object(input_data)

    assert len(result) == 1
    assert result[0]["type"] == "cluster"
    assert result[0]["uuid"] is None
    assert result[0]["cluster_uuid"] is not None
    assert result[0]["cluster_count"] == 5
    assert result[0]["position"] == [50.0, 60.0]


def test_match_clusters_uuids_exact_match():
    """Test matching cluster UUIDs with exact coordinate match"""
    points = [
        {"position": [50.0, 60.0], "uuid": "uuid-1"},
        {"position": [51.0, 61.0], "uuid": "uuid-2"},
    ]

    clusters = [
        {"longitude": 50.0, "latitude": 60.0, "count": 1},
        {"longitude": 51.0, "latitude": 61.0, "count": 1},
    ]

    result = match_clusters_uuids(points, clusters)

    assert result[0]["uuid"] == "uuid-1"
    assert result[1]["uuid"] == "uuid-2"


def test_match_clusters_uuids_multi_point_cluster():
    """Test that multi-point clusters don't get UUIDs assigned"""
    points = [
        {"position": [50.0, 60.0], "uuid": "uuid-1"},
        {"position": [51.0, 61.0], "uuid": "uuid-2"},
    ]

    clusters = [
        {"longitude": 50.5, "latitude": 60.5, "count": 5},  # Multi-point cluster
    ]

    result = match_clusters_uuids(points, clusters)

    # Multi-point cluster should not get a uuid assigned
    assert "uuid" not in result[0]


def test_match_clusters_uuids_no_match_warning():
    """Test that a warning is logged when no matching UUID is found for a single-point cluster"""
    points = [
        {"position": [50.0, 60.0], "uuid": "uuid-1"},
    ]

    # Cluster with coordinates far from any point
    clusters = [
        {"longitude": 100.0, "latitude": 100.0, "count": 1},
    ]

    with mock.patch("goodmap.clustering.logger") as mock_logger:
        result = match_clusters_uuids(points, clusters)

        # Should have logged a warning
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "No matching UUID found" in warning_call
        assert result[0]["uuid"] is None


def test_match_clusters_uuids_floating_point_precision():
    """Test that clusters within floating point threshold match correctly"""
    points = [
        {"position": [50.0, 60.0], "uuid": "uuid-1"},
    ]

    # Cluster with tiny floating point difference
    clusters = [
        {"longitude": 50.0 + 1e-9, "latitude": 60.0 + 1e-9, "count": 1},
    ]

    result = match_clusters_uuids(points, clusters)

    # Should match despite tiny floating point difference
    assert result[0]["uuid"] == "uuid-1"
