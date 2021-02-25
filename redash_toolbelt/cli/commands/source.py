"""Data source commands."""
import click

import redash_toolbelt.cli.completion as completion
from redash_toolbelt.cli.commands import CustomCommand, CustomGroup


@click.command(cls=CustomCommand, name="list")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only data source identifier and no labels or other meta data. "
         "This is useful for piping the ids into other commands."
)
@click.option(
    "--raw",
    is_flag=True,
    help="Outputs raw JSON response of the API."
)
@click.pass_obj
def list_command(app, id_only, raw):
    """List data sources.

    This command lists all data sources from a redash deployment.
    """
    api = app.get_api()
    all_sources = api.data_sources()
    if id_only:
        for _ in sorted(all_sources, key=lambda k: k["id"]):
            app.echo_info(str(_["id"]))
        return
    if raw:
        app.echo_info_json(all_sources)
        return
    table = []
    for _ in sorted(all_sources, key=lambda k: k["name"].lower()):
        row = [
            _["id"],
            _["name"],
            _["type"]
        ]
        table.append(row)
    app.echo_info_table(
        table,
        headers=["ID", "Name", "Type"]
    )


@click.command(cls=CustomCommand, name="open")
@click.argument(
    "SOURCE_IDS",
    type=click.INT,
    nargs=-1,
    required=True,
    autocompletion=completion.sources
)
@click.pass_obj
def open_command(app, source_ids):
    """Open data source in the browser.

    With this command, you can open data sources from in your browser
    (e.g. in order to change them).
    The command accepts multiple data source IDs.
    """
    api = app.get_api()
    for _ in source_ids:
        open_query_uri = api.redash_url + "/data_sources/" + str(_)
        app.echo_debug("Open {}: {}".format(_, open_query_uri))
        click.launch(open_query_uri)


@click.group(cls=CustomGroup)
def source():
    """List and open data sources.

    Data sources configure data access to an external data provider.
    They are used run queries on them and are identified with a unique integer.
    """


source.add_command(list_command)
source.add_command(open_command)
