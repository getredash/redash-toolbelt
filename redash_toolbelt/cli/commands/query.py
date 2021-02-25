"""Query commands."""
import click

import redash_toolbelt.cli.completion as completion
from redash_toolbelt.cli.commands import CustomCommand, CustomGroup


@click.command(cls=CustomCommand, name="list")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only query identifier and no labels or other meta data. "
         "This is useful for piping the ids into other commands."
)
@click.option(
    "--raw",
    is_flag=True,
    help="Outputs raw JSON response of the API."
)
@click.pass_obj
def list_command(app, id_only, raw):
    """List queries.

    This command lists all queries from a redash deployment.
    """
    all_queries = app.api.paginate(app.api.queries)
    if id_only:
        for _ in sorted(all_queries, key=lambda k: k["id"]):
            app.echo_info(str(_["id"]))
        return
    if raw:
        app.echo_info_json(all_queries)
        return
    table = []
    for _ in sorted(all_queries, key=lambda k: k["name"].lower()):
        row = [
            _["id"],
            _["name"]
        ]
        table.append(row)
    app.echo_info_table(
        table,
        headers=["ID", "Name"]
    )


@click.command(cls=CustomCommand, name="open")
@click.argument(
    "QUERY_IDS",
    type=click.INT,
    nargs=-1,
    required=True,
    autocompletion=completion.queries
)
@click.pass_obj
def open_command(app, query_ids):
    """Open queries in the browser.

    With this command, you can open queries from the query catalog in
    the query editor in your browser (e.g. in order to change them).
    The command accepts multiple query IDs.
    """
    for _ in query_ids:
        open_query_uri = app.api.redash_url + "/queries/" + str(_)
        app.echo_debug("Open {}: {}".format(_, open_query_uri))
        click.launch(open_query_uri)


@click.group(cls=CustomGroup)
def query():
    """List queries.

    Queries retrieve data from a data source based on a custom query string.
    """


query.add_command(list_command)
query.add_command(open_command)
