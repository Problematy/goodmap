import datetime
import humanize


def get_delta(now, date_in):
    date = datetime.datetime.strptime(date_in.split(".")[0], "%Y-%m-%dT%H:%M:%S")
    delta = humanize.naturaltime(now - date)
    return delta


def format_post(post):
    now = datetime.datetime.now()
    for comment in post["comments"]:
        comment.update({"time_delta": get_delta(now, comment["date"])})
    post["comments"].sort(key=lambda x: x["date"], reverse=True)
    return post
