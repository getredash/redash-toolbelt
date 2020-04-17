import click

from redash_toolbelt import Redash


class Lookup(object):
    def __init__(self, redash, email):
        self.email = email.lower()
        self.redash = redash

    def check_query_result(self, query_result_id):
        if not query_result_id:
            return False

        result = self.redash._get(
            "api/query_results/{}".format(query_result_id))

        return self.email in result.text.lower()

    def check_query(self, query):
        found_in_query = False
        for field in ("query", "name", "description"):
            if self.email in (query[field] or "").lower():
                found_in_query = True

        for tag in query["tags"]:
            if self.email in (tag or "").lower():
                found_in_query = True

        found_in_result = self.check_query_result(
            query["latest_query_data_id"])

        return found_in_query or found_in_result

    def check_dashboard(self, dashboard):

        found_in_dashboard = False
        found_in_widget = False

        for field in ("slug", "name"):
            if self.email in (dashboard[field] or "").lower():
                found_in_dashboard = True

        for tag in dashboard["tags"]:
            if self.email in (tag or "").lower():
                found_in_dashboard = True

        if not found_in_dashboard:
            dash_widgets = self.redash._get("api/dashboards/{}".format(
                dashboard["slug"])).json()["widgets"]

            # Check text widgets
            if not isinstance(dash_widgets, type(None)):
                for widget in dash_widgets:
                    if "visualization" not in widget and self.email in widget[
                            "text"]:
                        found_in_widget = True

        return found_in_dashboard or found_in_widget

    def lookup(self):
        queries = self.redash.paginate(self.redash.queries)

        with click.progressbar(queries, label="Queries") as bar:
            found_q = [query for query in bar if self.check_query(query)]

        for query in found_q:
            query_url = "{}/queries/{}".format(self.redash.redash_url,
                                               query["id"])
            print(query_url)

        dashboards = self.redash.paginate(self.redash.dashboards)

        with click.progressbar(dashboards, label="Dashboards") as bar:
            found_d = [dash for dash in bar if self.check_dashboard(dash)]

        for dash in found_d:
            dash_url = "{}/dashboards/{}".format(self.redash.redash_url,
                                                 dash["slug"])
            print(dash_url)


@click.command()
@click.argument("redash_host")
@click.argument("email")
@click.option(
    "--api-key",
    "api_key",
    envvar="REDASH_API_KEY",
    show_envvar=True,
    prompt="API Key",
    help="User API Key",
)
def lookup(redash_host, email, api_key):
    """Search for EMAIL in queries and query results, output query URL if found."""

    redash = Redash(redash_host, api_key)
    lookup = Lookup(redash, email)
    lookup.lookup()


if __name__ == "__main__":
    lookup()
