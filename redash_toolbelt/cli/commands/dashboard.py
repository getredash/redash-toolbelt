"""Dashboard commands."""
import click

import redash_toolbelt.cli.completion as completion
from redash_toolbelt.cli.commands import CustomCommand, CustomGroup


@click.command(cls=CustomCommand, name="list")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only dashboard identifier and no labels or other meta data. "
         "This is useful for piping the ids into other commands."
)
@click.option(
    "--raw",
    is_flag=True,
    help="Outputs raw JSON response of the API."
)
@click.pass_obj
def list_command(app, id_only, raw):
    """List dashboards.

    This command lists all dashboards from a redash deployment.
    """
    api = app.get_api()
    all_dashboards = api.dashboards()
    if id_only:
        for _ in sorted(all_dashboards, key=lambda k: k["slug"]):
            app.echo_info(str(_["slug"]))
        return
    if raw:
        app.echo_info_json(all_dashboards)
        return
    table = []
    for _ in sorted(all_dashboards, key=lambda k: k["name"].lower()):
        row = [
            _["slug"],
            _["name"]
        ]
        table.append(row)
    app.echo_info_table(
        table,
        headers=["Slug", "Name"]
    )


@click.command(cls=CustomCommand, name="open")
@click.argument(
    "DASHBOARD_SLUGS",
    type=click.STRING,
    nargs=-1,
    required=True,
    autocompletion=completion.dashboards
)
@click.pass_obj
def open_command(app, dashboard_slugs):
    """Open dashboard in the browser.

    With this command, you can open dashboards from in your browser
    (e.g. in order to change them).
    The command accepts multiple dashboard IDs.
    """
    api = app.get_api()
    for _ in dashboard_slugs:
        open_query_uri = api.redash_url + "/dashboard/" + str(_)
        app.echo_debug("Open {}: {}".format(_, open_query_uri))
        click.launch(open_query_uri)


@click.group(cls=CustomGroup)
def dashboard():
    """List and open dashboards.

    Dashboards arrange visualizations of queries on a grid.
    They are identified by their slug, which is unique string and part of
    the access URL.
    """


dashboard.add_command(list_command)
dashboard.add_command(open_command)
