try:
	from .. import Redash, get_frontend_vals
except ImportError:
	from redash_toolbelt import Redash, get_frontend_vals


def refresh_dashboard(baseurl, apikey, slug):
	
	# build a client, fetch the dashboard, and calculate todays dates
	client = Redash(baseurl, apikey)
	queries_dict = get_queries_on_dashboard(client, slug)
	todays_dates = get_frontend_vals()

	# idx is the query ID. qry is the JSON data about that query ID.
	for idx, qry in queries_dict.items():

		if query_has_parameters(qry):
			pdict = {i.get('name'): i.get('value')
				for i in qry['options']['parameters']}
			params = {key: fill_dynamic_val(todays_dates, val)
				for key, val in pdict.items()}
		else:
			params = {}
		
		# Now refresh
		r = client._post(f"api/queries/{idx}/results",
			json={'parameters': params} )
		print(r.status_code)


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


def format_date(date_obj):
	return date_obj.strftime('%Y-%m-%d')


def is_date_range(value):
	return hasattr(value, 'start') and hasattr(value, 'end')


def get_queries_on_dashboard(client, slug):

	# Get a list of queries on this dashboard
	dash = client.dashboard(slug=DASHBOARD_SLUG)

	# Dashboards have visualization and text box widgets. Get the viz widgets.
	viz_widgets = [i for i in dash['widgets'] if 'visualization' in i.keys()]

	# Visualizations are tied to queries
	l_query_ids = [i['visualization']['query']['id'] for i in viz_widgets]

	return {id: client._get(f'api/queries/{id}').json() for id in l_query_ids}


def query_has_parameters(query_details):

	params = query_details['options'].get('parameters', None)
	return params is not None and len(params) > 0


if __name__ == '__main__':
	# Build API client
	APIKEY = '<put your api key here>'
	BASEURL = '<put your base url here>'
	DASHBOARD_SLUG = '<put your slug here>'

	refresh_dashboard(BASEURL, APIKEY, DASHBOARD_SLUG)
