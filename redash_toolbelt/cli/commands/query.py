"""Query commands."""
import click

import redash_toolbelt.cli.completion as completion
from redash_toolbelt.cli.commands import CustomCommand, CustomGroup


@click.command(cls=CustomCommand, name="list")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only query identifier and no labels or other meta data. "
    "This is useful for piping the ids into other commands.",
)
@click.option("--raw", is_flag=True, help="Outputs raw JSON response of the API.")
@click.pass_obj
def list_command(app, id_only, raw):
    """List queries.

    This command lists all queries from a redash deployment.
    """
    api = app.get_api()
    all_queries = api.queries()
    if id_only:
        for _ in sorted(all_queries, key=lambda k: k["id"]):
            app.echo_info(str(_["id"]))
        return
    if raw:
        app.echo_info_json(all_queries)
        return
    table = []
    for _ in sorted(all_queries, key=lambda k: k["name"].lower()):
        row = [_["id"], _["name"]]
        table.append(row)
    app.echo_info_table(table, headers=["ID", "Name"])


@click.command(cls=CustomCommand, name="open")
@click.argument(
    "QUERY_IDS",
    type=click.INT,
    nargs=-1,
    required=True,
    autocompletion=completion.queries,
)
@click.pass_obj
def open_command(app, query_ids):
    """Open queries in the browser.

    With this command, you can open queries from the query catalog in
    the query editor in your browser (e.g. in order to change them).
    The command accepts multiple query IDs.
    """
    api = app.get_api()
    for _ in query_ids:
        open_query_uri = api.redash_url + "/queries/" + str(_)
        app.echo_debug("Open {}: {}".format(_, open_query_uri))
        click.launch(open_query_uri)


@click.command(cls=CustomCommand, name="export")
@click.option(
    "--to-file",
    is_flag=True,
    help="Writes the json export into individual files. FIlenames follow the pattern: 'query_{id}.json'."
)
@click.option(
    "--output-dir",
    type=click.Path(
        writable=True,
        file_okay=False
    ),
    help="Export to this directory. Filenames follow the pattern: '<output-dir>/query_{id}.json'"
)
@click.option(
    "-a", "--all", "all_",
    is_flag=True,
    help="Exports all queries."
)
@click.argument(
    "QUERY_IDS",
    type=click.INT,
    nargs=-1,
    required=False,
    autocompletion=completion.queries
)
@click.pass_obj
def export_command(app, to_file, output_dir, all_, query_ids):
    """Export queries.

    This command exports selected or all querie(s).
    """
    q_ids = []
    if all_:
        all_queries = app.api.queries()
        q_ids = [q['id'] for q in all_queries ]
    else:
        q_ids = query_ids

    for qid in q_ids:
        qry = app.api.query(qid)
        if to_file is not None or output_dir is not None:
            filename = 'query_{}.json'.format(qry['id'])
            if output_dir is not None:
                # create directory
                if not os.path.exists(output_dir):
                    app.echo_warning("Output directory does not exist: will create it.")
                    os.makedirs(output_dir)
                # join with given output directory and normalize full path
                filename = os.path.normpath(os.path.join(output_dir, filename))
            save_dict_as_json_file(qry, filename)
            app.echo_info(
                "query id: {id}, name: {name} was exported to: {file}".format(id=qid, name=qry['name'], file=filename))
        else:
            app.echo_info_json(qry)


@click.group(cls=CustomGroup)
def query():
    """List and open queries.

    Queries retrieve data from a data source based on a custom query string.
    They are identified with a unique integer
    """


query.add_command(list_command)
query.add_command(open_command)
query.add_command(export_command)
