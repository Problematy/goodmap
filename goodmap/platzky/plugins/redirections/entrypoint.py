from functools import partial

from flask import redirect
from gql import gql

from pydantic import BaseModel, Field

def json_db_get_redirections(self):
    return self.data.get("redirections", {})


def json_file_db_get_redirections(self):
    return json_db_get_redirections(self)


def google_json_db_get_redirections(self):
    return self.data.get("redirections", {})


def graph_ql_db_get_redirections(self):
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


class Redirection(BaseModel):
    source: str
    destiny: str


def process(app, config):
    redirections = [Redirection.parse_obj({'source': source, 'destiny': destiny}) for source,destiny in config.items()]
    function_name = f"{app.db.module_name}_get_redirections"
    app.db.extend("get_redirections", globals()[function_name])
    for redirection in redirections:
        func = partial(redirect, redirection.destiny, code=301)
        func.__name__ = f"{redirection.source}-{redirection.destiny}"
        app.route(rule=redirection.source)(func)

    return app
