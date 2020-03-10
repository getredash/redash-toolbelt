try:
	from .. import Redash
except ImportError:
	from redash_toolbelt import Redash


def get_all_query_text(client):

	fields = ['id', 'name', 'description', 'query', 'options']

	return	[{field: i.get(field) for field in fields}
			  for i in client.paginate(client.queries)]

def refresh_dashboard_queries(client, slug):

	# Get all queries that power the dashboard

	dash = client.dashboard(slug=slug)
	viz_widgets = [i for i in dash['widgets'] if 'visualization' in i.keys()]
	l_queries = [i['visualization']['query']['id'] for i in viz_widgets]
	d_queries = {q: client._get(f'api/queries/{q}').json() for q in l_queries}

	
