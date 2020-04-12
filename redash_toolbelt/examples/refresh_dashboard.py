import click
from redash_toolbelt import Redash, get_frontend_vals


def refresh_dashboard(baseurl, apikey, slug):

    client = Redash(baseurl, apikey)
    todays_dates = get_frontend_vals()
    queries_dict = get_queries_on_dashboard(client, slug)

    # loop through each query and its JSON data
    for idx, qry in queries_dict.items():

        params = {
            p.get("name"): fill_dynamic_val(todays_dates, p)
            for p in qry["options"].get("parameters", [])
        }

        # Pass max_age to ensure a new result is provided.
        body = {"parameters": params, "max_age": 0}

        r = client._post(f"api/queries/{idx}/results", json=body)

        print(f"Query: {idx} -- Code {r.status_code}")


def get_queries_on_dashboard(client, slug):

    # Get a list of queries on this dashboard
    dash = client.dashboard(slug=slug)

    # Dashboards have visualization and text box widgets. Get the viz widgets.
    viz_widgets = [i for i in dash["widgets"] if "visualization" in i.keys()]

    # Visualizations are tied to queries
    l_query_ids = [i["visualization"]["query"]["id"] for i in viz_widgets]

    return {id: client._get(f"api/queries/{id}").json() for id in l_query_ids}


def fill_dynamic_val(dates, p):
    """Accepts parameter default information from the Redash API.

    If the default value is not a date type, or its value cannot be calculated,
    then the default value is returned unchanged.

	Otherwise, the dynamic value is retrieved from the dates param and returned
	"""

    if not is_dynamic_param(dates, p):
        return p.get("value")
    dyn_val = getattr(dates, p.get("value"))

    if is_date_range(dyn_val):
        return format_date_range(dyn_val)
    else:
        return format_date(dyn_val)


def is_dynamic_param(dates, param):

    return "date" in param.get("type") and param.get("value") in dates._fields


def is_date_range(value):
    return hasattr(value, "start") and hasattr(value, "end")


def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")


def format_date_range(date_range_obj):

    start = format_date(date_range_obj.start)
    end = format_date(date_range_obj.end)

    return dict(start=start, end=end)


@click.command()
@click.argument("url",)
@click.argument("key",)
@click.argument("slug",)
def main(url, key, slug):
    """Refresh URL/dashboards/SLUG using KEY"""

    refresh_dashboard(url, key, slug)


if __name__ == "__main__":
    main()
