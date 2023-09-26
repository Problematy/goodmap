# TODO rename file, extract it to another library, remove qgl and aiohttp from dependencies

import json

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import Field

from goodmap.platzky.blog.db import DB, DBConfig


class GraphQlDbConfig(DBConfig):
    endpoint: str = Field(alias="CMS_ENDPOINT")
    token: str = Field(alias="CMS_TOKEN")


def get_db(config: GraphQlDbConfig):
    return GraphQL(config.endpoint, config.token)


class GraphQL(DB):
    def __init__(self, endpoint, token):
        full_token = "bearer " + token
        transport = AIOHTTPTransport(url=endpoint, headers={"Authorization": full_token})
        self.client = Client(transport=transport)

    def get_all_posts(self, lang):
        all_posts = gql(
            """
            query MyQuery($lang: Lang!) {
              posts(where: {language: $lang},  orderBy: date_DESC, stage: PUBLISHED){
                createdAt
                date
                title
                excerpt
                slug
                tags
                coverImage {
                  alternateText
                  image {
                    url
                  }
                }
              }
            }
            """
        )
        return self.client.execute(all_posts, variable_values={"lang": lang})["posts"]

    def get_menu_items(self):
        menu_items = gql(
            """
            query MyQuery {
              menuItems(stage: PUBLISHED){
                name
                url
              }
            }
            """
        )
        return self.client.execute(menu_items)["menuItems"]

    def get_post(self, slug):
        post = gql(
            """
            query MyQuery($slug: String!) {
              post(where: {slug: $slug}, stage: PUBLISHED) {
                title
                contentInRichText {
                  text
                  markdown
                }
                excerpt
                tags
                coverImage {
                  alternateText
                  image {
                    url
                  }
                }
                comments {
                    author
                    comment
                    date: createdAt
                }
              }
            }
            """
        )
        return self.client.execute(post, variable_values={"slug": slug})["post"]

    # TODO Cleanup page logic of internationalization (now it depends on translation of slugs)
    def get_page(self, slug):
        post = gql(
            """
            query MyQuery ($slug: String!){
              page(where: {slug: $slug}, stage: PUBLISHED) {
                title
                contentInMarkdown
                coverImage
                {
                    url
                }
              }
            }
            """
        )
        return self.client.execute(post, variable_values={"slug": slug})["page"]

    def get_posts_by_tag(self, tag, lang):
        post = gql(
            """
            query MyQuery ($tag: String!, $lang: Lang!){
              posts(where: {tags_contains_some: [$tag], language: $lang}, stage: PUBLISHED) {
                    tags
                    title
                    slug
                    excerpt
                    date
                    coverImage {
                      alternateText
                      image {
                        url
                      }
                    }
              }
            }
            """
        )
        return self.client.execute(post, variable_values={"tag": tag, "lang": lang})["posts"]

    def get_all_providers(self):
        all_providers = gql(
            """
            query MyQuery {
              providers(stage: PUBLISHED) {
                link
                name
                offer
                currency
              }
            }
            """
        )
        providers = self.client.execute(all_providers)["providers"]
        for provider in providers:
            provider["offer"] = json.loads(provider["offer"])
        return providers

    def get_all_questions(self):
        all_questions = gql(
            """
            query MyQuery {
              questions(stage: PUBLISHED) {
                question
                field
                inputType
              }
            }
            """
        )
        query = self.client.execute(all_questions)
        return query["questions"]

    def add_comment(self, author_name, comment, post_slug):
        add_comment = gql(
            """
            mutation MyMutation($author: String!, $comment: String!, $slug: String!) {
                createComment(
                    data: {
                        author: $author,
                        comment: $comment,
                        post: {connect: {slug: $slug}}
                    }
                ) {
                    id
                }
            }
            """
        )
        self.client.execute(
            add_comment,
            variable_values={
                "author": author_name,
                "comment": comment,
                "slug": post_slug,
            },
        )
