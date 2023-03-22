from datetime import datetime

from freezegun import freeze_time

from goodmap.platzky.blog.post_formatter import format_post, get_delta


@freeze_time("2022-01-01")
def test_post_formatting():
    post = {
        "title": "title",
        "language": "en",
        "slug": "slug",
        "tags": ["tag/1"],
        "contentInRichText": {"markdown": "content"},
        "date": "2021-02-19",
        "coverImage": {
            "alternateText": "text which is alternative",
            "image": {"url": "https://media.graphcms.com/XvmCDUjYTIq4c9wOIseo"},
        },
        "comments": [{"date": "2021-02-19T00:00:00", "comment": "komentarz", "author": "autor"}],
    }

    wanted_post = {
        "title": "title",
        "language": "en",
        "slug": "slug",
        "tags": ["tag/1"],
        "contentInRichText": {"markdown": "content"},
        "date": "2021-02-19",
        "coverImage": {
            "alternateText": "text which is alternative",
            "image": {"url": "https://media.graphcms.com/XvmCDUjYTIq4c9wOIseo"},
        },
        "comments": [
            {
                "time_delta": "10 months ago",
                "date": "2021-02-19T00:00:00",
                "comment": "komentarz",
                "author": "autor",
            }
        ],
    }

    assert format_post(post) == wanted_post


def test_time_delta():
    now_date = datetime.strptime("2022-11-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
    delta = get_delta(now_date, "2022-11-02T00:00:00")
    assert delta == "a day from now"
