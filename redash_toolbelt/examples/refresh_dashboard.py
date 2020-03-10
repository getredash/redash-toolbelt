try:
	from .. import Redash, get_frontend_vals
except ImportError:
	from redash_toolbelt import Redash, get_frontend_vals


# Build API client
apikey = 'RCoU8KMv5voSZSX8XB0BTt9JjFZ3szZsEktNPdnS'
baseurl = 'https://app.redash.io/default'
redash = Redash(baseurl, apikey)

# Get today's dynamic dates
dd = get_frontend_vals()

# Get a list of queries on this dashboard
dash = redash.dashboard(slug='curious-metrics')
viz_widgets = [i for i in dash['widgets'] if 'visualization' in i.keys()]
l_query_ids = [i['visualization']['query']['id'] for i in viz_widgets]
l_query_info = [redash._get(f'api/queries/{i}').json() for i in l_query_ids]

# cycle through each query and refresh it
#	+ queries without parameters: execute normally.
# 	+ queries with parameters: pass the default value
#	+ queries with dynamic date parameters: pass a calculated value

# Refresh queries without parameters
for q in [i for i in l_query_info if 'parameters' not in i['options']]:

	r = redash._post(f"api/queries/{q['id']}/refresh")

	print(r.status_code)

# Prepare params
for q in [i for i in l_query_info if 'parameters' in i['options']]:

	raw_params = {f"p_{p.get('name')}": p.get('value') for p in q['options']['parameters'] }
	
	# Remove nesting of start and end values on date range parameters
	flat_params = {}
	for k,v in raw_params.items():

		# Case: the date parameter is dynamic.
		if v in dd._fields:
			flat_params[f"{k}.start"] = getattr(dd, v).start.strftime('%Y-%m-%d')
			flat_params[f"{k}.end"] = getattr(dd, v).end.strftime('%Y-%m-%d')

		# Case: the date parameter is a hardcoded dictionary with 'start' and 'end' keys
		elif isinstance(v, dict):
			flat_params[f"{k}.start"] = v.get('start')
			flat_params[f"{k}.end"] = v.get('end')
		
		# Case: this is not a date parameter
		else:
			flat_params.update({k:v})

	r = redash._post(f"api/queries/{q['id']}/refresh", params=flat_params)
	print(r.status_code)
	