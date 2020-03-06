try:
	from .. import Redash
except ImportError:
	from redash_toolbelt import Redash

import json, datetime

def get_all_query_text(baseurl=None, apikey=None, client=None):

	if isinstance(client, type(None)):
		client = Redash(baseurl, apikey)

	fields = ['id', 'name', 'description', 'query', 'options']

	return	[
		{field: i.get(field) for field in fields}
		for i in client.paginate(client.queries)
			]
