# Copied from https://gist.github.com/arikfr/2c7d09f6837b256c58a3d3ef6a97f61a

import json
import requests
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger("requests").setLevel("ERROR")

# The Redash instance you're copying from:
ORIGIN = "https://redash.acme.com"
ORIGIN_API_KEY = ""  # admin API key

# The Redash account you're copying into:
DESTINATION = 'https://app.redash.io/acme'
DESTINATION_API_KEY = ""  # admin API key

# You need to create the data sources in advance in the destination account. Once created, update the map here:
# (origin Redash data source id -> destination Redash data source id)
DATA_SOURCES = {
    1: 1234,
}


meta = {
    # include here any users you already created in the target Redash account.
    # the key is the user id in the origin Redash instance. make sure to include the API key, as it used to recreate any objects
    # this user might have owned.
    "users": {
        "1": {
            "id": "",
            "email": "",
            "invite_link": "",
            "api_key": ""
        },
    },
    "queries": {},
    "visualizations": {},
    "dashboards": {}
}


def auth_headers(api_key):
    return {
        "Authorization": "Key {}".format(api_key)
    }


def api_request(api):
    response = requests.get(ORIGIN + api, headers=auth_headers(ORIGIN_API_KEY))
    response.raise_for_status()

    return response.json()

def get_paginated_resource(resource, api_key):
    objects = []
    headers = {'Authorization': 'Key {}'.format(api_key)}
    has_more = True
    page = 1
    while has_more:
        response = requests.get(resource, headers=headers,
                                params={'page': page}).json()
        objects.extend(response['results'])
        has_more = page * response['page_size'] + 1 <= response['count']
        page += 1

    return objects 


def get_queries(url, api_key):
    path = "{}/api/queries".format(url)
    return get_paginated_resource(path, api_key)


def get_users(url, api_key):
    path = "{}/api/users".format(url)
    return get_paginated_resource(path, api_key)


def import_users():
    print("Importing users...")

    users = get_users(ORIGIN, ORIGIN_API_KEY)
    for user in users:
        print("   importing: {}".format(user['id']))
        data = {
            "name": user['name'],
            "email": user['email']
        }

        if str(user['id']) in meta['users']:
            print("    ... skipping: exists.")
            continue

        if user['email'] == 'admin':
            print("    ... skipping: admin.")
            continue

        response = requests.post(DESTINATION + '/api/users?no_invite=1',
                                 json=data, headers=auth_headers(DESTINATION_API_KEY))
        response.raise_for_status()

        new_user = response.json()
        meta['users'][user['id']] = {
            'id': new_user['id'],
            'email': new_user['email'],
            'invite_link': "" # new_user['invite_link']
        }


def get_api_key(user_id):
    response = requests.get(DESTINATION + '/api/users/{}'.format(user_id),
                            headers=auth_headers(DESTINATION_API_KEY))
    response.raise_for_status()

    return response.json()['api_key']


def user_with_api_key(user_id):
    user = meta['users'].get(user_id) or meta['users'].get(str(user_id))
    if 'api_key' not in user:
        user['api_key'] = get_api_key(user['id'])
    return user


def convert_schedule(schedule):
    if schedule is None:
        return schedule
    
    if isinstance(schedule, dict):
        return schedule

    schedule_json = {
        'interval': None,
        'until': None,
        'day_of_week': None,
        'time': None
    }

    if ":" in schedule:
        schedule_json['interval'] = 86400
        schedule_json['time'] = schedule
    else:
        schedule_json['interval'] = schedule

    return schedule_json


def import_queries():
    print("Import queries...")

    queries = get_queries(ORIGIN, ORIGIN_API_KEY)

    for query in queries:
        print("   importing: {}".format(query['id']))
        data_source_id = DATA_SOURCES.get(query['data_source_id'])
        if data_source_id is None:
            print("   skipped ({})".format(data_source_id))
            continue

        if str(query['id']) in meta['queries']:
            print("   skipped - was already imported".format(data_source_id))
            continue

        data = {
            "data_source_id": data_source_id,
            "query": query['query'],
            "is_archived": query['is_archived'],
            "schedule": convert_schedule(query['schedule']),
            "description": query['description'],
            "name": query['name'],
        }

        user = user_with_api_key(query['user']['id'])

        response = requests.post(
            DESTINATION + '/api/queries', json=data, headers=auth_headers(user['api_key']))
        response.raise_for_status()

        new_query_id = response.json()['id']
        meta['queries'][query['id']] = new_query_id

        if not query['is_draft']:
            response = requests.post(DESTINATION + '/api/queries/' + str(new_query_id), json={'is_draft': False}, headers=auth_headers(user['api_key']))
            response.raise_for_status()


def import_visualizations():
    print("Importing visualizations...")

    for query_id, new_query_id in meta['queries'].items():
        query = api_request('/api/queries/{}'.format(query_id))
        print("   importing visualizations of: {}".format(query_id))

        for v in query['visualizations']:
            if v['type'] == 'TABLE':
                response = requests.get(DESTINATION + '/api/queries/{}'.format(
                    new_query_id), headers=auth_headers(DESTINATION_API_KEY))
                response.raise_for_status()

                new_vis = response.json()['visualizations']
                for new_v in new_vis:
                    if new_v['type'] == 'TABLE':
                        meta['visualizations'][v['id']] = new_v['id']
            else:
                if str(v['id']) in meta['visualizations']:
                    continue

                user = user_with_api_key(query['user']['id'])
                data = {
                    "name": v['name'],
                    "description": v['description'],
                    "options": v['options'],
                    "type": v['type'],
                    "query_id": new_query_id
                }
                response = requests.post(
                    DESTINATION + '/api/visualizations', json=data, headers=auth_headers(user['api_key']))
                response.raise_for_status()

                meta['visualizations'][v['id']] = response.json()['id']


def import_dashboards():
    print("Importing dashboards...")

    dashboards = get_paginated_resource(ORIGIN + '/api/dashboards', ORIGIN_API_KEY)

    for dashboard in dashboards:
        print("   importing: {}".format(dashboard['slug']))
        d = api_request('/api/dashboards/{}'.format(dashboard['slug']))
        data = {'name': d['name']}
        user = user_with_api_key(d['user_id'])
        response = requests.post(
            DESTINATION + '/api/dashboards', json=data, headers=auth_headers(user['api_key']))
        response.raise_for_status()

        new_dashboard = response.json()
        requests.post(
            DESTINATION + '/api/dashboards/{}'.format(new_dashboard['id']), json={'is_draft': False}, headers=auth_headers(user['api_key']))

        # recreate widget
        for widget in d['widgets']:
            data = {
                'dashboard_id': new_dashboard['id'],
                'options': widget['options'],
                'width': widget['width'],
                'text': widget['text'],
                'visualization_id': None
            }

            if not isinstance(widget['options'], dict):
                widget['options'] = {}

            if 'visualization' in widget:
                data['visualization_id'] = meta['visualizations'].get(
                    str(widget['visualization']['id']))

            if 'visualization' in widget and not data['visualization_id']:
                print('skipping for missing viz')
                continue

            response = requests.post(
                DESTINATION + '/api/widgets', json=data, headers=auth_headers(user['api_key']))
            response.raise_for_status()


def fix_queries():
    """
    This runs after importing all queries, so we can update the query id reference
    in parameter definitions.
    """
    print("Updating queries options...")

    for query_id, new_query_id in meta['queries'].items():
        query = api_request('/api/queries/{}'.format(query_id))
        print("   Fixing: {}".format(query_id))

        options = query['options']
        for p in options.get('parameters', []):
            if 'queryId' in p:
                p['queryId'] = meta['queries'].get(str(p['queryId']))

        user = user_with_api_key(query['user']['id'])
        response = requests.post(DESTINATION + '/api/queries/' + str(new_query_id), json={'options': options}, headers=auth_headers(user['api_key']))
        response.raise_for_status()


def save_meta():
    print("Saving meta...")
    with open('meta.json', 'w') as f:
        json.dump(meta, f)


def import_all():
    try:
        # If you had an issue while running this the first time, fixed it and running again, uncomment the following to skip content already imported.
        # with open('meta.json') as f:
            # meta.update(json.load(f))
        import_users()
        import_queries()
        fix_queries()
        import_visualizations()
        import_dashboards()
    except Exception as ex:
        logging.exception(ex)

    save_meta()


if __name__ == '__main__':
    import_all()