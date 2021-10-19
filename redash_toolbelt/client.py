import requests


class Redash(object):
    def __init__(self, redash_url, api_key):
        self.redash_url = redash_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": "Key {}".format(api_key)})

    def test_credentials(self):
        try:
            response = self._get("api/session")
            return True
        except requests.exceptions.HTTPError:
            return False

    def queries(self, page=1, page_size=25, only_favorites=False):
        """GET api/queries"""

        target_url = "api/queries/favorites" if only_favorites else "api/queries"

        return self._get(target_url, params=dict(page=page, page_size=page_size)).json()

    def create_favorite(self, _type: str, id):
        """POST to api/queries/<id>/favorite or api/dashboards/<id>/favorite"""

        if _type == "dashboard":
            url = f"api/dashboards/{id}/favorite"
        elif _type == "query":
            url = f"api/queries/{id}/favorite"
        else:
            return

        return self._post(url, json={})

    def get_query(self, query_id):
        """GET api/queries/<query_id>"""
        return self._get(f"api/queries/{query_id}").json()

    def users(self, page=1, page_size=25, only_disabled=False):
        """GET api/users"""

        params = dict(page=page, page_size=page_size, disabled=only_disabled)

        return self._get("api/users", params=params).json()

    def disable_user(self, user_id):
        """POST api/users/<user_id>/disable"""
        return self._post(f"api/users/{user_id}/disable").json()

    def dashboards(self, page=1, page_size=25, only_favorites=False):
        """GET api/dashboards"""

        target_url = "api/dashboards/favorites" if only_favorites else "api/dashboards"

        return self._get(target_url, params=dict(page=page, page_size=page_size)).json()

    def get_dashboard(self, id):
        """GET api/dashboards/<id>"""

        return self._get(
            f"api/dashboards/{id}",
        ).json()

    def get_data_sources(self):
        """GET api/data_sources"""
        return self._get(
            "api/data_sources",
        ).json()

    def get_data_source(self, id):
        """GET api/data_sources/<id>"""

        return self._get("api/data_sources/{}".format(id)).json()

    def create_data_source(self, name, _type, options):
        """POST api/data_sources"""

        payload = {"name": name, "type": _type, "options": options}

        return self._post("api/data_sources", json=payload)

    def dashboard(self, slug):
        """GET api/dashboards/{slug}"""
        return self._get("api/dashboards/{}".format(slug)).json()

    def create_query(self, query_json):
        return self._post("api/queries", json=query_json)

    def create_dashboard(self, name):
        return self._post("api/dashboards", json={"name": name}).json()

    def update_dashboard(self, dashboard_id, properties):
        return self._post(
            "api/dashboards/{}".format(dashboard_id), json=properties
        ).json()

    def create_widget(self, dashboard_id, visualization_id, text, options):
        data = {
            "dashboard_id": dashboard_id,
            "visualization_id": visualization_id,
            "text": text,
            "options": options,
            "width": 1,
        }
        return self._post("api/widgets", json=data)

    def duplicate_dashboard(self, slug, new_name=None):
        current_dashboard = self.dashboard(slug)

        if new_name is None:
            new_name = "Copy of: {}".format(current_dashboard["name"])

        new_dashboard = self.create_dashboard(new_name)
        if current_dashboard["tags"]:
            self.update_dashboard(
                new_dashboard["id"], {"tags": current_dashboard["tags"]}
            )

        for widget in current_dashboard["widgets"]:
            visualization_id = None
            if "visualization" in widget:
                visualization_id = widget["visualization"]["id"]
            self.create_widget(
                new_dashboard["id"], visualization_id, widget["text"], widget["options"]
            )

        return new_dashboard

    def duplicate_query(self, query_id, new_name=None):

        response = self._post(f"api/queries/{query_id}/fork")
        new_query = response.json()

        if not new_name:
            return new_query

        new_query["name"] = new_name

        return self.update_query(new_query.get("id"), new_query).json()

    def scheduled_queries(self):
        """Loads all queries and returns only the scheduled ones."""
        queries = self.paginate(self.queries)
        return filter(lambda query: query["schedule"] is not None, queries)

    def update_query(self, query_id, data):
        """POST /api/queries/{query_id} with the provided data object."""
        path = "api/queries/{}".format(query_id)
        return self._post(path, json=data)

    def update_visualization(self, viz_id, data):
        """POST /api/visualizations/{viz_id} with the provided data object."""
        path = "api/visualizations/{}".format(viz_id)
        return self._post(path, json=data)

    def alerts(self):
        """GET api/alerts
        This API endpoint is not paginated."""
        return self._get("api/alerts").json()

    def get_alert(self, alert_id):
        """GET api/alerts/<alert_id>"""
        return self._get(f"api/alerts/{alert_id}").json()

    def create_alert(self, name, options, query_id):
        """POST api/alerts to create a new alert"""

        payload = dict(
            name=name,
            options=options,
            query_id=query_id,
        )
        return self._post(f"api/alerts", json=payload).json()

    def update_alert(self, id, name=None, options=None, query_id=None, rearm=None):

        payload = dict(name=name, options=options, query_id=query_id, rearm=rearm)

        no_none = {key: val for key, val in payload.items() if val is not None}

        return self._post(f"api/alerts/{id}", json=no_none)

    def paginate(self, resource, page=1, page_size=100, **kwargs):
        """Load all items of a paginated resource

        NOTE: This might fail due to rate limit (50/hr, 200/day).
        TODO: Add backoff?
        """

        response = resource(page=page, page_size=page_size, **kwargs)
        items = response["results"]

        if response["page"] * response["page_size"] >= response["count"]:
            return items
        else:
            return [
                *items,
                *self.paginate(resource, page=page + 1, page_size=page_size, **kwargs),
            ]

    def _get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)

    def _post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)

    def _delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)

    def _request(self, method, path, **kwargs):
        url = "{}/{}".format(self.redash_url, path)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
