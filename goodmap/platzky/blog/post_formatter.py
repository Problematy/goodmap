import datetime
from typing import Any, Dict

import humanize


def get_delta(now, date_in):
    date = datetime.datetime.strptime(date_in.split(".")[0], "%Y-%m-%dT%H:%M:%S")
    delta = humanize.naturaltime(now - date)
    return delta


def format_post(post):
    now = datetime.datetime.now()

    def comment_sort_key(comment_: Dict[str, Any]) -> Any:
        return comment_["date"]

    for comment in post["comments"]:
        comment.update({"time_delta": get_delta(now, comment["date"])})

    post["comments"].sort(key=comment_sort_key, reverse=True)
    return post
