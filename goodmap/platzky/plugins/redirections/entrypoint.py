from functools import partial

from flask import redirect
from gql import gql

from goodmap.platzky.db.google_json_db import GoogleJsonDb
from goodmap.platzky.db.graph_ql_db import GraphQL
from goodmap.platzky.db.json_db import Json
from goodmap.platzky.db.json_file_db import JsonFile


def json_get_redirections(self):
    return self.data.get("redirections", {})


def google_get_redirections(self):
    return self.data.get("redirections", {})


def graphql_get_redirections(self):
    redirections = gql(
        """
        query MyQuery{
          redirections(stage: PUBLISHED){
            source
            destination
          }
        }
        """
    )
    return {
        x["source"]: x["destination"] for x in self.client.execute(redirections)["redirections"]
    }


def get_proper_redirections(db_type):
    redirections = {
        Json: json_get_redirections,
        JsonFile: json_get_redirections,
        GraphQL: graphql_get_redirections,
        GoogleJsonDb: google_get_redirections,
    }
    return redirections[db_type]


def process(app, config):
    app.db.get_redirections = get_proper_redirections(app.db.__class__)
    redirects = app.db.get_redirections(app.db)
    for source, destiny in redirects.items():
        func = partial(redirect, destiny, code=301)
        func.__name__ = f"{source}-{destiny}"
        app.route(rule=source)(func)

    return app
