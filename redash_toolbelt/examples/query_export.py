import click
import requests
from redash_toolbelt.client import Redash

template = u"""/*
Name: {name}
Data source: {data_source}
Created By: {created_by}
Last Updated At: {last_updated_at}
*/
{query}"""


def save_queries(queries):
    for query in queries:
        filename = "query_{}.sql".format(query["id"])
        with open(filename, "w") as f:
            content = template.format(
                name=query["name"],
                data_source=query["data_source_id"],
                created_by=query["user"]["name"],
                last_updated_at=query["updated_at"],
                query=query["query"],
            )
            f.write(content)


@click.command()
@click.argument("redash_url")
@click.option(
    "--api-key",
    "api_key",
    required=True,
    envvar="REDASH_API_KEY",
    show_envvar=True,
    prompt="API Key",
    help="User API Key",
)
def main(redash_url, api_key):
    redash = Redash(redash_url, api_key)
    queries = redash.paginate(redash.queries)
    save_queries(queries)


if __name__ == "__main__":
    main()
