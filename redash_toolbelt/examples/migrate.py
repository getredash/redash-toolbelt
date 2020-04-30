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

meta["users"] = {int(key): val for key,val in meta["users"].items()}


def import_users(orig_client, dest_client):
    print("Importing users...")

    users = orig_client.paginate(orig_client.users)
    for user in users:
        print("   importing: {}".format(user['id']))
        data = {
            "name": user['name'],
            "email": user['email']
        }

        if user['id'] in  meta['users']:
            print("    ... skipping: exists.")
            continue

        if user['email'] == 'admin':
            print("    ... skipping: admin.")
            continue

        response = dest_client._post(f'/api/users?no_invite=1', json=data)

        new_user = response.json()
        meta['users'][user['id']] = {
            'id': new_user['id'],
            'email': new_user['email'],
            'invite_link': "" # new_user['invite_link']
        }


def get_api_key(client, user_id):
    client.get(f'/api/users/{user_id}')

    return response.json()['api_key']


def user_with_api_key(user_id):
    user = meta['users'].get(user_id)
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


def import_queries(orig_client, dest_client):
    print("Import queries...")

    queries = orig_client.paginate(orig_client.queries)

    for query in queries:

        origin_id = query['id']

        print(f"   importing: {origin_id}")
        data_source_id = DATA_SOURCES.get(query['data_source_id'])
        if data_source_id is None:
            print("   skipped ({})".format(data_source_id))
            continue

        if origin_id in meta['queries']:
            print("   skipped - was already imported".format(origin_id))
            continue

        data = {
            "data_source_id": data_source_id,
            "query": query['query'],
            "is_archived": query['is_archived'],
            "schedule": convert_schedule(query['schedule']),
            "description": query['description'],
            "name": query['name'],
        }

        user_api_key = get_api_key(client, query['user']['id'])
        user_client = Redash(DESTINATION, user_api_key)
        response = user_client._post("/api/queries", json=data)

        destination_id = response.json()['id']
        meta['queries'][query['id']] = destination_id

        # New queries are always saved as drafts.
        # Need to sync the ORIGIN draft status to DESTINATION.
        if not query['is_draft']:
            response = dest_client._post(
                f"{DESTINATION}'/api/queries/{destination_id}",json={'is_draft': False})



def import_visualizations(orig_client, dest_client):
    print("Importing visualizations...")

    for query_id, new_query_id in meta['queries'].items():
        query = orig_client._get(f'/api/queries/{query_id}')
        orig_user_id = query['user']['id']
        dest_user_id = meta['users'].get(orig_user_id).get('id')

        print("   importing visualizations of: {}".format(query_id))

        for v in query['visualizations']:
            if v['type'] == 'TABLE':
                response = dest_client._get(f'/api/queries/{new_query_id}')

                new_vis = response.json()['visualizations']
                for new_v in new_vis:
                    if new_v['type'] == 'TABLE':
                        meta['visualizations'][v['id']] = new_v['id']
            else:
                if str(v['id']) in meta['visualizations']:
                    continue

                user_api_key = get_api_key(dest_client, dest_user_id)
                user_client = Redash(DESTINATION, user_api_key)
    
                data = {
                    "name": v['name'],
                    "description": v['description'],
                    "options": v['options'],
                    "type": v['type'],
                    "query_id": new_query_id
                }
                response = user_client._post('/api/visualizations', json=data)

                meta['visualizations'][v['id']] = response.json()['id']


def import_dashboards(orig_client, dest_client):
    print("Importing dashboards...")

    dashboards = orig_client.paginate(orig_client.dashboards)

    for dashboard in dashboards:
        print("   importing: {}".format(dashboard['slug']))

        d = orig_client(f'/api/dashboards/{dashboard['slug']}')

        orig_user_id = d['user']['id']
        dest_user_id = meta['users'].get(orig_user_id).get('id')

        data = {'name': d['name']}
        
        user_api_key = get_api_key(dest_client, dest_user_id)
        user_client = Redash(DESTINATION, user_api_key)        

        response = dest_client._post('/api/dashboards', json=data)

        new_dashboard = response.json()
        user_client._post(f'/api/dashboards/{new_dashboard['id']}', json={'is_draft': False})

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

            response = user_client._post('/api/widgets', json=data)


def fix_queries(orig_client, dest_client):
    """
    This runs after importing all queries, so we can update the query id reference
    in parameter definitions.
    """
    print("Updating queries options...")

    for query_id, new_query_id in meta['queries'].items():
        query = orig_client(f'/api/queries/{query_id}')
        orig_user_id = query['user']['id']
        dest_user_id = meta['users'].get(orig_user_id).get('id')

        print("   Fixing: {}".format(query_id))

        options = query['options']
        for p in options.get('parameters', []):
            if 'queryId' in p:
                p['queryId'] = meta['queries'].get(str(p['queryId']))

        user_api_key = get_api_key(dest_user_id)
        user_client = Redash(DESTINATION, user_api_key)
        response = user_client._post(f'/api/queries/{new_query_id}', json={'options': options})


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