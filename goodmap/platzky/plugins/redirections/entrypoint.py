from functools import partial

from flask import redirect
from gql import gql


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


def process(app, config):
    function_name = f"{app.db.module_name}_get_redirections"
    app.db.extend("get_redirections", globals()[function_name])
    redirects = app.db.get_redirections()
    for source, destiny in redirects.items():
        func = partial(redirect, destiny, code=301)
        func.__name__ = f"{source}-{destiny}"
        app.route(rule=source)(func)

    return app
