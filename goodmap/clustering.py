import uuid

from scipy.spatial import KDTree


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
    points_coords = [(point["position"][0], point["position"][1]) for point in points]
    tree = KDTree(points_coords)
    for cluster in clusters:
        if cluster["count"] == 1:
            cluster_coords = (cluster["longitude"], cluster["latitude"])
            dist, idx = tree.query(cluster_coords)
            if dist < 0.00000001:
                closest_point = points[idx]
                cluster["uuid"] = closest_point["uuid"]
    return clusters
