"""Groups commands."""
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
    """List Groups.

    This command lists all user groups from a redash deployment.
    """
    api = app.get_api()
    all_groups = api.groups()
    if id_only:
        for _ in sorted(all_groups, key=lambda k: k["id"]):
            app.echo_info(str(_["id"]))
        return
    if raw:
        app.echo_info_json(all_groups)
        return
    table = []
    for _ in sorted(all_groups, key=lambda k: k["name"].lower()):
        row = [
            _["id"],
            _["name"],
        ]
        table.append(row)
    app.echo_info_table(
        table,
        headers=["ID", "Name"]
    )


@click.command(cls=CustomCommand, name="open")
@click.argument(
    "GROUP_IDS",
    type=click.INT,
    nargs=-1,
    required=True,
    autocompletion=completion.groups
)
@click.pass_obj
def open_command(app, group_ids):
    """Open a user profile in the browser.

    With this command, you can open a user group in your browser
    The command accepts multiple user group IDs.
    """
    api = app.get_api()
    for _ in group_ids:
        open_query_uri = api.redash_url + "/groups/" + str(_)
        app.echo_debug("Open {}: {}".format(_, open_query_uri))
        click.launch(open_query_uri)


@click.group(cls=CustomGroup)
def group():
    """List and open user groups.

    User groups are identified with a unique integer.
    """


group.add_command(list_command)
group.add_command(open_command)
