import click

from redash_toolbelt import Redash


def duplicate(client, slug, prefix=None):
    """Creates a blank dashboard, duplicates the original's queries,
    and populates it with fresh widgets that mirror the original widgets.
    """

    # Copped this logic directly from Redash.duplicate_dashboard
    current_dashboard = client.dashboard(slug)
    new_dash_name = "Copy of: {}".format(current_dashboard["name"])
    new_dashboard = client.create_dashboard(new_dash_name)

    if current_dashboard["tags"]:
        client.update_dashboard(
            new_dashboard["id"], {"tags": current_dashboard["tags"]}
        )

    # Widgets can hold text boxes or visualizations. Filter out text boxes.
    # I use a dictionary here because it de-duplicates query IDs
    queries_to_duplicate = {
        widget["visualization"]["query"]["id"]: widget["visualization"]["query"]
        for widget in current_dashboard.get("widgets", [])
        if "visualization" in widget
    }

    # Fetch full query details for the old query IDs
    # Duplicate the query and store the result
    old_vs_new_query_pairs = [
        {
            "old_query": client._get(f"api/queries/{old_query.get('id')}").json(),
            "new_query": client.duplicate_query(
                old_query.get("id"), new_name=" ".join([prefix + old_query.get("name")])
            ),
        }
        for old_query in queries_to_duplicate.values()
    ]

    # Compare old visualizations to new ones
    # Create a mapping of old visualization IDs to new ones
    old_viz_vs_new_viz = {
        old_viz.get("id"): new_viz.get("id")
        for pair in old_vs_new_query_pairs
        for old_viz in pair["old_query"].get("visualizations")
        for new_viz in pair["new_query"].get("visualizations")
        if old_viz.get("options") == new_viz.get("options")
    }

    # This is a version of the same logic from Redash.duplicate_dashboard
    # But it substitutes in the new visualiation ID pointing at the copied query.
    for widget in current_dashboard["widgets"]:
        visualization_id = None
        if "visualization" in widget:
            visualization_id = old_viz_vs_new_viz.get(widget["visualization"]["id"])
        client.create_widget(
            new_dashboard["id"], visualization_id, widget["text"], widget["options"]
        )

    return new_dashboard


@click.command()
@click.argument("redash_host")
@click.argument("slug")
@click.option(
    "--api-key",
    "api_key",
    envvar="REDASH_API_KEY",
    show_envvar=True,
    prompt="API Key",
    help="User API Key",
)
@click.argument("prefix")
def main(redash_host, slug, api_key, prefix=""):
    """Calls the duplicate function using Click commands"""

    client = Redash(redash_host, api_key)
    duplicate(client, slug, prefix)


if __name__ == "__main__":
    main()
