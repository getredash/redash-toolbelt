import click
import requests
from redash_toolbelt.client import Redash

template = u"""/*
API KEY: {name}
*/
{query}"""

@click.command()
@click.argument("redash_url")
@click.argument("query_id")
@click.option(
    "--api-key",
    "api_key",
    required=True,
    envvar="REDASH_API_KEY",
    show_envvar=True,
    prompt="API Key",
    help="User API Key",
)

def main(redash_url, api_key, query_id):
    redash = Redash(redash_url, api_key)
    path = f'api/queries/{query_id}'
    redash._delete(path)

if __name__ == "__main__":
    main()
