import click
from redash_toolbelt import Redash, get_frontend_vals


def refresh_dashboard(baseurl, apikey, slug):
	
	# build a client, fetch the dashboard, and calculate todays dates
	client = Redash(baseurl, apikey)
	todays_dates = get_frontend_vals()
	queries_dict = get_queries_on_dashboard(client, slug)

	# idx is the query ID. qry is the JSON data about that query ID.
	for idx, qry in queries_dict.items():

		if query_has_parameters(qry):
			params = {key: fill_dynamic_val(todays_dates, val)
				for key, val in iter_params(qry)}
		else:
			params = {}

		# Pass max_age to ensure a new result is provided.
		r = client._post(f"api/queries/{idx}/results",
			json={'parameters': params, "max_age": 0} )
		
		print(f"Query: {idx} -- Code {r.status_code}")


def get_queries_on_dashboard(client, slug):

	# Get a list of queries on this dashboard
	dash = client.dashboard(slug=slug)

	# Dashboards have visualization and text box widgets. Get the viz widgets.
	viz_widgets = [i for i in dash['widgets'] if 'visualization' in i.keys()]

	# Visualizations are tied to queries
	l_query_ids = [i['visualization']['query']['id'] for i in viz_widgets]

	return {id: client._get(f'api/queries/{id}').json() for id in l_query_ids}


def query_has_parameters(query_details):

	params = query_details['options'].get('parameters', None)
	return params is not None and len(params) > 0


def fill_dynamic_val(dates, val):
	'''Returns the appropriate dynamic date parameter value.
	If the input is not a valid dynamic parameter it is returned unchanged.
	'''

	if val not in dates._fields:
		return val

	new_val = getattr(dates, val)

	if not is_date_range(new_val):
		return format_date(new_val)

	else:
		return dict(start=format_date(new_val.start),
			end=format_date(new_val.end))


def is_date_range(value):
	return hasattr(value, 'start') and hasattr(value, 'end')


def format_date(date_obj):
	return date_obj.strftime('%Y-%m-%d')


def iter_params(query_object):
	"""Returns an iterator of parameter name-value pairs
	from an API query object"""

	return {i.get('name'): i.get('value')
		for i in query_object['options']['parameters']}.items()



@click.command()
@click.argument('url',)
@click.argument('key',)
@click.argument('slug',)
def main(url, key, slug):
	"""Refresh URL/dashboards/SLUG using KEY"""

	refresh_dashboard(url, key, slug)


if __name__ == '__main__':
    main()
