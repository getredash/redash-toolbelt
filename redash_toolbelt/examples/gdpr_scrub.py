import click

from redash_toolbelt import Redash


class Lookup(object):
    def __init__(self, redash, email_list):
        self.email_list = [i.lower() for i in email_list]
        self.redash = redash

    def check_query_result(self, query_result_id):
        if not query_result_id:
            return False

        result = self.redash._get("api/query_results/{}".format(query_result_id))

        return any([email in result.text.lower() for email in self.email_list])

    def check_query(self, query):

        found_in_query = any(
            [
                email in (query[field] or "").lower()
                for email in self.email_list
                for field in ["query", "name", "description"]
            ]
        )

        found_in_tags = any(
            [
                email in (tag or "").lower()
                for email in self.email_list
                for tag in query["tags"]
            ]
        )

        found_in_result = self.check_query_result(query["latest_query_data_id"])

        return found_in_query or found_in_result or found_in_tags

    def check_dashboard(self, dashboard):

        found_in_dashboard = any(
            [
                email in (dashboard[field] or "").lower()
                for email in self.email_list
                for field in ("slug", "name")
            ]
        )
        found_in_tags = any(
            [
                email in (tag or "").lower()
                for email in self.email_list
                for tag in dashboard["tags"]
            ]
        )

        if found_in_dashboard or found_in_tags:
            return True

        dash_widgets = (
            self.redash._get("api/dashboards/{}".format(dashboard["slug"]))
            .json()
            .get("widgets", [])
        )

        # Check text widgets
        found_in_widget = any(
            [
                email in widget["text"]
                for email in self.email_list
                for widget in dash_widgets
                if "visualization" not in widget
            ]
        )

        return found_in_dashboard or found_in_widget or found_in_tags

    def lookup(self):
        queries = self.redash.paginate(self.redash.queries)

        with click.progressbar(queries, label="Queries") as bar:
            found_q = [query for query in bar if self.check_query(query)]

        for query in found_q:
            query_url = "{}/queries/{}".format(self.redash.redash_url, query["id"])
            print(query_url)

        dashboards = self.redash.paginate(self.redash.dashboards)

        with click.progressbar(dashboards, label="Dashboards") as bar:
            found_d = [dash for dash in bar if self.check_dashboard(dash)]

        for dash in found_d:
            dash_url = "{}/dashboards/{}".format(self.redash.redash_url, dash["slug"])
            print(dash_url)


@click.command()
@click.argument("redash_host")
@click.argument("email", nargs=-1)
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
