import logging
import uuid

from scipy.spatial import KDTree

# Maximum distance to consider a point-cluster match (accounts for floating point errors)
DISTANCE_THRESHOLD = 1e-8

logger = logging.getLogger(__name__)


def map_clustering_data_to_proper_lazy_loading_object(input_array):
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
    coordinates back to the original point to retrieve its UUID. The 'uuid' key is optional
    and will only be present in single-point clusters where a matching point is found.

    Args:
        points: List of point dicts with 'position' and 'uuid' keys
        clusters: List of cluster dicts with 'longitude', 'latitude', and 'count' keys.
                 For single-point clusters (count=1), a 'uuid' key will be added if a
                 matching point is found (modified in place)

    Returns:
        The modified clusters list with 'uuid' keys added to matched single-point clusters
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
    return clusters
