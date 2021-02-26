"""Dashboard commands."""
import click
import os

import redash_toolbelt.cli.completion as completion
from redash_toolbelt.cli.commands import CustomCommand, CustomGroup
from redash_toolbelt.utils import save_dict_as_json_file


@click.command(cls=CustomCommand, name="list")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only dashboard identifier and no labels or other meta data. "
    "This is useful for piping the ids into other commands.",
)
@click.option("--raw", is_flag=True, help="Outputs raw JSON response of the API.")
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
        row = [_["slug"], _["name"]]
        table.append(row)
    app.echo_info_table(table, headers=["Slug", "Name"])


@click.command(cls=CustomCommand, name="open")
@click.argument(
    "DASHBOARD_SLUGS",
    type=click.STRING,
    nargs=-1,
    required=True,
    autocompletion=completion.dashboards,
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


@click.command(cls=CustomCommand, name="export")
@click.option(
    "--to-file",
    is_flag=True,
    help="Writes the json export into individual files. FIlenames follow the pattern: 'dashboard_{id}_{slug}.json'."
)
@click.option(
    "--output-dir",
    type=click.Path(
        writable=True,
        file_okay=False
    ),
    help="Export to this directory. Filenames follow the pattern: '<output-dir>/dashboard_{id}_{slug}.json'"
)
@click.option(
    "-a", "--all", "all_",
    is_flag=True,
    help="Exports all queries."
)
@click.argument(
    "DASHBOARD_SLUGS",
    type=click.STRING,
    nargs=-1,
    required=True,
    autocompletion=completion.dashboards,
)
@click.pass_obj
def export_command(app, to_file, output_dir, all_, dashboard_slugs):
    """Export dashboard(s).

    This command exports selected or all dashbopard(s).
    """
    api = app.get_api()
    db_slugs = []
    if all_:
        all_dashboards = api.dashboards()
        db_slugs = [db['slug'] for db in all_dashboards]
    else:
        db_slugs = dashboard_slugs

    for slug in db_slugs:
        db = api.dashboard(slug)
        if to_file or output_dir is not None:
            filename = 'dashboard_{}_{}.json'.format(db['id'], slug)
            if output_dir is not None:
                # create directory
                if not os.path.exists(output_dir):
                    app.echo_warning("Output directory does not exist: will create it.")
                    os.makedirs(output_dir)
                # join with given output directory and normalize full path
                filename = os.path.normpath(os.path.join(output_dir, filename))
            save_dict_as_json_file(db, filename)
            app.echo_info(
                "dashboard id: {id}, slug: {slug}, name: {name} was exported to: {file}".format(
                    id=db['id'], slug=slug, name=db['name'], file=filename))
        else:
            app.echo_info_json(db)


@click.group(cls=CustomGroup)
def dashboard():
    """List and open dashboards.

    Dashboards arrange visualizations of queries on a grid.
    They are identified by their slug, which is unique string and part of
    the access URL.
    """


dashboard.add_command(list_command)
dashboard.add_command(open_command)
dashboard.add_command(export_command)
