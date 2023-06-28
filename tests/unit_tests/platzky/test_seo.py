from unittest.mock import MagicMock

from flask import Flask

from goodmap.platzky.seo import seo


def test_config_creation_with_incorrect_mappings():
    db_mock = MagicMock()
    config_mock = MagicMock()
    config_mock.__getitem__.return_value = "/prefix"

    seo_blueprint = seo.create_seo_blueprint(db_mock, config_mock)
    app = Flask(__name__)
    app.config.update({"TESTING": True, "DEBUG": True})
    app.register_blueprint(seo_blueprint)

    response = app.test_client().get("/prefix/robots.txt")
    assert b"Sitemap: https://localhost/sitemap.xml" in response.data
    assert response.status_code == 200


def test_sitemap():
    db_mock = MagicMock()
    db_mock.get_all_posts.return_value = [
        {
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
    ]
    config_mock = MagicMock()
    config = {"SEO_PREFIX": "/prefix", "DOMAIN_TO_LANG": {"localhost": "en"}}
    config_mock.__getitem__.side_effect = config.__getitem__

    seo_blueprint = seo.create_seo_blueprint(db_mock, config_mock)
    app = Flask(__name__)
    app.config.update({"TESTING": True, "DEBUG": True})
    app.register_blueprint(seo_blueprint)

    response = app.test_client().get("/prefix/sitemap.xml")
    assert response.status_code == 200
    assert b"http://localhost/slug" in response.data
