from goodmap.platzky.db import google_json_db, graph_ql_db, json_file_db


def load_db_driver(db_type):
    db_type_to_db_loader = {
        "json_file": json_file_db,
        "google_json": google_json_db,
        "graph_ql": graph_ql_db,
    }

    return db_type_to_db_loader[db_type]
