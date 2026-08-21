import logging
import uuid

from scipy.spatial import KDTree

# Maximum distance to consider a point-cluster match (accounts for floating point errors)
DISTANCE_THRESHOLD = 1e-8

# Zoom range SuperCluster is built for. Also the range the API accepts, so that a zoom
# the clusterer could serve is never rejected by validation, and vice versa - keep the
# request model and the SuperCluster call reading these, not their own copies.
MIN_ZOOM = 0
MAX_ZOOM = 16

logger = logging.getLogger(__name__)


def map_clustering_data_to_proper_lazy_loading_object(input_array):
    """Convert clustering data into lazy-loading response objects.

    Transforms an array of clustered point data into response objects suitable
    for lazy loading on the frontend. Single-point clusters become "point" type
    objects with their original UUID, while multi-point clusters become "cluster"
    type objects with a generated UUID and count.

    Args:
        input_array: List of cluster dicts with 'count', 'longitude', 'latitude',
                     'uuid' and 'marker' keys.

    Returns:
        List of response dicts with 'position', 'uuid', 'cluster_uuid',
        'cluster_count' and 'type' keys, plus 'marker' for points that have
        any pin styling.
    """
    response_array = []
    for item in input_array:
        if item["count"] == 1:
            response_object = {
                "position": [item["longitude"], item["latitude"]],
                "uuid": item["uuid"],
                "cluster_uuid": None,
                "cluster_count": None,
                "type": "point",
            }
            # Left out entirely rather than sent as null for an unstyled point, so a
            # point here looks exactly like the same point from /api/locations.
            if item.get("marker") is not None:
                response_object["marker"] = item["marker"]
            response_array.append(response_object)
            continue
        response_object = {
            "position": [item["longitude"], item["latitude"]],
            "uuid": None,
            "cluster_uuid": str(uuid.uuid4()),
            "cluster_count": item["count"],
            "type": "cluster",
        }
        response_array.append(response_object)
    return response_array


# Since there can be some floating point errors
# we need to check if the distance is close enough to 0
def match_clusters_uuids(points, clusters):
    """
    Match single-point clusters to their original point UUIDs.

    For clusters containing exactly one point, this function attempts to match the cluster
    coordinates back to the original point to retrieve its UUID and marker styling. The
    'uuid'/'marker' keys are optional and will only be present in single-point clusters
    where a matching point is found.

    Args:
        points: List of point dicts with 'position', 'uuid' and 'marker' keys
        clusters: List of cluster dicts with 'longitude', 'latitude', and 'count' keys.
                 For single-point clusters (count=1), 'uuid' and 'marker' keys will be
                 added, from the matching point if found or None otherwise (modified
                 in place)

    Returns:
        The modified clusters list with 'uuid'/'marker' keys added to single-point clusters
    """
    points_coords = [(point["position"][0], point["position"][1]) for point in points]
    tree = KDTree(points_coords)
    for cluster in clusters:
        if cluster["count"] == 1:
            cluster_coords = (cluster["longitude"], cluster["latitude"])
            dist, idx = tree.query(cluster_coords)
            if dist < DISTANCE_THRESHOLD:
                closest_point = points[idx]
                cluster["uuid"] = closest_point["uuid"]
                cluster["marker"] = closest_point.get("marker")
            else:
                # Log warning when no match is found - indicates data inconsistency
                logger.warning(
                    "No matching UUID found for cluster at coordinates (%f, %f). "
                    "Distance to nearest point: %f (threshold: %f)",
                    cluster["longitude"],
                    cluster["latitude"],
                    dist,
                    DISTANCE_THRESHOLD,
                )
                cluster["uuid"] = None
                cluster["marker"] = None
    return clusters
