import requests


class Redash(object):
    def __init__(self, redash_url, api_key):
        self.redash_url = redash_url
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'Key {}'.format(api_key)})

    def test_credentials(self):
        try:
            response = self._get('api/session')
            return True
        except requests.exceptions.HTTPError:
            return False

    def queries(self, page=1, page_size=25):
        """GET api/queries"""
        return self._get('api/queries', params=dict(page=page, page_size=page_size)).json()

    def dashboards(self, page=1, page_size=25):
        """GET api/dashboards"""
        return self._get('api/dashboards', params=dict(page=page, page_size=page_size)).json()

    def dashboard(self, slug):
        """GET api/dashboards/{slug}"""
        return self._get('api/dashboards/{}'.format(slug)).json()

    def create_dashboard(self, name):
        return self._post('api/dashboards', json={'name': name}).json()

    def update_dashboard(self, dashboard_id, properties):
        return self._post('api/dashboards/{}'.format(dashboard_id), json=properties).json()

    def create_widget(self, dashboard_id, visualization_id, text, options):
        data = {
            'dashboard_id': dashboard_id,
            'visualization_id': visualization_id,
            'text': text,
            'options': options,
            'width': 1,
        }
        return self._post('api/widgets', json=data)

    def duplicate_dashboard(self, slug, new_name=None):
        current_dashboard = self.dashboard(slug)

        if new_name is None:
            new_name = u'Copy of: {}'.format(current_dashboard['name'])

        new_dashboard = self.create_dashboard(new_name)
        if current_dashboard['tags']:
            self.update_dashboard(new_dashboard['id'], {'tags': current_dashboard['tags']})

        for widget in current_dashboard['widgets']:
            visualization_id = None
            if 'visualization' in widget:
                visualization_id = widget['visualization']['id']
            self.create_widget(new_dashboard['id'], visualization_id, widget['text'], widget['options'])

        return new_dashboard

    def scheduled_queries(self):
        """Loads all queries and returns only the scheduled ones."""
        queries = self.paginate(self.queries)
        return filter(lambda query: query['schedule'] is not None, queries)

    def update_query(self, query_id, data):
        """POST /api/queries/{query_id} with the provided data object."""
        path = 'api/queries/{}'.format(query_id)
        return self._post(path, json=data)

    def paginate(self, resource):
        """Load all items of a paginated resource"""
        stop_loading = False
        page = 1
        page_size = 100

        items = []

        while not stop_loading:
            response =  resource(page=page, page_size=page_size)

            items += response['results']
            page += 1

            stop_loading = response['page'] * response['page_size'] >= response['count']

        return items

    def _get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request('POST', path, **kwargs)

    def _request(self, method, path, **kwargs):
        url = '{}/{}'.format(self.redash_url, path)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
