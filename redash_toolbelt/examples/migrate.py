# Copied from https://gist.github.com/arikfr/2c7d09f6837b256c58a3d3ef6a97f61a

### TODO: document 400 Client Error: BAD REQUEST for url: http://localhost:5000/api/queries


import json
import requests
import logging
import sys
from redash_toolbelt import Redash


class UserNotFoundException(Exception):
    pass


logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
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

# If true, the invitation link for users created by this script will be 
# preserved in meta.json. Otherwise, users will need to click the "forgot password"
# link to login for the first time.
PRESERVE_INVITE_LINKS = True

base_meta = {
    # include here any users you already created in the target Redash account.
    # the key is the user id in the origin Redash instance. make sure to include the API key, as it used to recreate any objects
    # this user might have owned.
    "users": {"1": {"id": "", "email": "", "invite_link": "", "api_key": ""},},
    "queries": {},
    "visualizations": {},
    "dashboards": {},
    "flags": {"viz_import_complete": {}},
}

meta = {}


def read_meta():
    print("Opening meta...")
    with open("meta.json", "r") as fp:
        _meta = json.load(fp)
        _meta.setdefault("users", {})
        _meta.setdefault("queries", {})
        _meta.setdefault("visualizations", {})
        _meta.setdefault("dashboards", {})
        _meta.setdefault("flags", {"viz_import_complete": {}})

        return _meta


def save_meta():
    print("Saving meta...")
    with open("meta.json", "w") as f:
        json.dump(meta, f)


def save_meta_wrapper(func):
    def wrapped(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
        finally:
            save_meta()

    return wrapped


meta = read_meta() or base_meta
meta["users"] = {int(key): val for key, val in meta["users"].items()}


@save_meta_wrapper
def import_users(orig_client, dest_client):
    """This function expects that the meta object already includes details for admin users on the DEST instance.
    If you already created users on the DEST instance, enter their details into meta before using this function.
    """

    print("Importing users...")

    def user_lists_are_equal(orig_list, dest_list):

        dest_user_emails = set([i["email"] for i in dest_list])
        orig_user_emails = set([i["email"] for i in orig_list])

        return dest_user_emails == orig_user_emails

    orig_users = orig_client.paginate(orig_client.users)
    dest_users = dest_client.paginate(dest_client.users)

    # Check if the user list has already been synced between orig, dest, and meta
    if valid_user_meta(dest_users):
        print("OK: users have been synced. Okay to proceed.")
        return

    # Check if the user list has been synced between orig and dest
    # In this case, meta.json should be updated
    if user_lists_are_equal(orig_users, dest_users):
        print(
            "CAUTION: orig and dest user lists are in sync, but users are missing from meta.json"
        )
        return

    # Users are missing from dest and meta (default case)
    # Add these users to the dest instance and add them to meta.json
    for user in orig_users:
        print("   importing: {}".format(user["id"]))
        data = {"name": user["name"], "email": user["email"]}

        if user["id"] in meta["users"]:
            print("    ... skipping: exists.")
            continue

        if user["email"] == "admin":
            print("    ... skipping: admin.")
            continue

        try:
            response = dest_client._post(f"api/users?no_invite=1", json=data)
        except Exception as e:
            print(
                "Could not create user: probably this user already exists but is not present in meta.json"
            )
            continue

        new_user = response.json()
        meta["users"][user["id"]] = {
            "id": new_user["id"],
            "email": new_user["email"],
            "invite_link": PRESERVE_INVITE_LINKS and new_user["invite_link"] or "",
        }

    dest_users = dest_client.paginate(dest_client.users)
    dest_user_emails = [i["email"] for i in dest_users]
    org_user_emails = [i["email"] for i in orig_users]

    if set(dest_user_emails) == set(org_user_emails):
        print("User list is now synced!")
    else:
        print(
            "CAUTION: user list is not in sync! Destination contains {} users. Origin contains {} users".format(
                len(dest_user_emails), len(org_user_emails)
            )
        )


def valid_user_meta(dest_users):
    """Confirms all users in DEST are present in meta.
    """

    meta_user_list = [i["email"] for i in meta["users"].values()]

    missing = []
    for usr in dest_users:
        email = usr["email"]
        if email in meta_user_list:
            continue
        else:
            missing.append(email)

    if len(missing) == 0:
        print("OK: Meta agrees with dest user list")
        return True
    else:
        print("CAUTION: Some users are missing from the meta.json. ")
        [print(i) for i in missing]
        return False


def get_api_key(client, user_id):
    response = client._get(f"api/users/{user_id}")

    return response.json()["api_key"]


def user_with_api_key(origin_user_id, dest_client):
    """Look up the destination user object using its origin user ID.

    The destination client must be an admin to have access to the user API key.
    """
    user = meta["users"].get(origin_user_id)

    if user is None:
        raise UserNotFoundException(
            "Origin user: {} not found in meta.json. Was this user disabled?".format(
                origin_user_id
            )
        )
    if "api_key" not in user:
        user["api_key"] = get_api_key(dest_client, user["id"])
    return user


def convert_schedule(schedule):
    if schedule is None:
        return schedule

    if isinstance(schedule, dict):
        return schedule

    schedule_json = {"interval": None, "until": None, "day_of_week": None, "time": None}

    if ":" in schedule:
        schedule_json["interval"] = 86400
        schedule_json["time"] = schedule
    else:
        schedule_json["interval"] = schedule

    return schedule_json


@save_meta_wrapper
def import_queries(orig_client, dest_client):
    print("Import queries...")

    queries = orig_client.paginate(orig_client.queries)

    for query in queries:

        origin_id = query["id"]

        data_source_id = DATA_SOURCES.get(query["data_source_id"])

        if origin_id in meta["queries"] or str(origin_id) in meta["queries"]:
            print("Query {} - SKIP - was already imported".format(origin_id))
            continue

        if data_source_id is None:
            print(
                "Query {} - SKIP - data source has not been mapped ({})".format(
                    origin_id, query["data_source_id"]
                )
            )
            continue

        data = {
            "data_source_id": data_source_id,
            "query": query["query"],
            "is_archived": query["is_archived"],
            "schedule": convert_schedule(query["schedule"]),
            "description": query["description"],
            "name": query["name"],
            "options": query["options"],
        }

        try:
            user_api_key = user_with_api_key(query["user"]["id"], dest_client)[
                "api_key"
            ]
        except UserNotFoundException as e:
            print("Query {} - FAIL - {}".format(query["id"], e))
            continue

        print("Query {} - OK  - importing".format(origin_id))

        user_client = Redash(DESTINATION, user_api_key)

        try:
            response = user_client.create_query(data)
        except Exception as e:
            print("Query {} - FAIL - {}".format(origin_id, e))
            continue

        destination_id = response.json()["id"]
        meta["queries"][query["id"]] = destination_id

        # New queries are always saved as drafts.
        # Need to sync the ORIGIN draft status to DESTINATION.
        if not query["is_draft"]:
            response = dest_client.update_query(destination_id, {"is_draft": False})


@save_meta_wrapper
def fix_queries(orig_client, dest_client):
    """
    This runs after importing all queries, so we can update the query id reference
    in parameter definitions.
    """
    print("Updating queries options...")

    for query_id, new_query_id in meta["queries"].items():
        query = orig_client.get_query(query_id)
        orig_user_id = query["user"]["id"]

        dest_user_id = meta["users"].get(orig_user_id).get("id")

        print("   Fixing: {}".format(query_id))

        options = query["options"]
        for p in options.get("parameters", []):
            if "queryId" in p:
                p["queryId"] = meta["queries"].get(str(p["queryId"]))

        user_api_key = user_with_api_key(orig_user_id, dest_client,)["api_key"]
        user_client = Redash(dest_client.redash_url, user_api_key)
        user_client.update_query(new_query_id, {"options": options})


@save_meta_wrapper
def import_visualizations(orig_client, dest_client):
    print("Importing visualizations...")
    
    for query_id, new_query_id in meta["queries"].items():

        if meta.get("flags", {}).get("viz_import_complete", {}).get(query_id):
            print(
                "Query {} - SKIP - All visualisations already imported".format(query_id)
            )
            continue

        query = orig_client.get_query(query_id)

        orig_user_id = query["user"]["id"]
        dest_user_id = meta["users"].get(orig_user_id).get("id")

        print("   importing visualizations of: {}".format(query_id))

        for v in query["visualizations"]:

            if str(v["id"]) in meta["visualizations"]:
                print("Viz {} - SKIP - Already imported".format(v["id"]))
                continue

            if v["type"] == "TABLE":
                response = dest_client.get_query(new_query_id)

                new_vis = response["visualizations"]
                for new_v in new_vis:
                    if new_v["type"] == "TABLE":
                        meta["visualizations"][v["id"]] = new_v["id"]
            else:
                user_api_key = get_api_key(dest_client, dest_user_id)
                user_client = Redash(DESTINATION, user_api_key)

                data = {
                    "name": v["name"],
                    "description": v["description"],
                    "options": v["options"],
                    "type": v["type"],
                    "query_id": new_query_id,
                }
                response = user_client._post("api/visualizations", json=data)

                meta["visualizations"][v["id"]] = response.json()["id"]

        meta["flags"]["viz_import_complete"][query_id] = True


@save_meta_wrapper
def import_dashboards(orig_client, dest_client):
    print("Importing dashboards...")

    dashboards = orig_client.paginate(orig_client.dashboards)

    for dashboard in dashboards:
        if dashboard["slug"] in meta["dashboards"]:
            print("Dashboard `{}` - SKIP - Already imported".format(dashboard["slug"]))
            continue

        print("   importing: {}".format(dashboard["slug"]))

        d = orig_client.dashboard(dashboard["slug"])

        orig_user_id = d["user"]["id"]

        try:
            user_api_key = user_with_api_key(orig_user_id, dest_client,)["api_key"]
        except UserNotFoundException as e:
            print("Dashboard {} - FAIL - {}".format(d["slug"], e))
            continue
    
        user_client = Redash(DESTINATION, user_api_key)

        new_dashboard = user_client.create_dashboard(d["name"])

        new_dash_id = new_dashboard["id"]

        # Sets published status to match source instance
        not d["is_draft"] and user_client.update_dashboard(
            new_dash_id, {"is_draft": False}
        )

        # recreate widget
        for widget in d["widgets"]:
            data = {
                "dashboard_id": new_dash_id,
                "options": widget["options"] or {},
                "width": widget["width"],
                "text": widget["text"],
                "visualization_id": None,
            }

            if "visualization" in widget:
                data["visualization_id"] = meta["visualizations"].get(
                    str(widget["visualization"]["id"])
                )

            if "visualization" in widget and not data["visualization_id"]:
                print("Widget {} - SKIP - visualization is missing (check missing data source, query, or viz)".format(widget["id"]))
                continue

            user_client.create_widget(
                new_dash_id, data["visualization_id"], data["text"], data["options"]
            )

        meta["dashboards"].update({d["slug"]: new_dashboard["slug"]})

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


if __name__ == "__main__":
    import_all()
