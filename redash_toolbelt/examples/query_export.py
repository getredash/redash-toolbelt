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

def save_queries(target_redash_url, api_key, queries):
    for query in queries:
        save_to_disk(query)
        post_remote(target_redash_url, api_key, query)

def save_to_disk(query):
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

def post_remote(target_redash_url, api_key, query):
    payload = {
        "query": query,
        "name": query["name"],
        "data_source_id": query["data_source_id"],
        "schedule": None,
        "options": {"parameters":[]}
    }
    res = requests.post(
        target_redash_url + '/api/queries', 
        headers = {'Authorization': api_key },
        json=payload
    )

    if not res.ok:
        print(res.raw)


@click.command()
@click.argument("source_redash_url")
@click.argument("target_redash_url")
@click.option(
    "--api-key",
    "api_key",
    required=True,
    envvar="REDASH_API_KEY",
    show_envvar=True,
    prompt="API Key",
    help="User API Key",
)
def main(source_redash_url, target_redash_url, api_key):
    redash = Redash(source_redash_url, api_key)
    queries = redash.paginate(redash.queries)
    save_queries(target_redash_url, api_key, queries)

if __name__ == "__main__":
    main()
