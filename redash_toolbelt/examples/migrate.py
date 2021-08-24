"""
Author: Jesse Whitehouse
Last updated: 24 August 2021
Notes:
  Copied from https://gist.github.com/arikfr/2c7d09f6837b256c58a3d3ef6a97f61a
"""


import sys, os, json, logging
import click
from redash_toolbelt import Redash

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logging.getLogger("requests").setLevel("ERROR")


#      ____                                          _
#     / ___|___  _ __ ___  _ __ ___   __ _ _ __   __| |___
#    | |   / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` / __|
#    | |__| (_) | | | | | | | | | | | (_| | | | | (_| \__ \
#     \____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|___/


class UserNotFoundException(Exception):
    pass


def check_data_sources(orig_client, dest_client):
    """Checks for obvious issues with the data source map that can cause issues further on"""
    if len(DATA_SOURCES) == 0 or (
        len(DATA_SOURCES) == 1 and DATA_SOURCES.get(-1) == -1234
    ):
        print("\n\nYou have not set up the data source map in meta.json")
        print("\n\nCheck complete: ERROR")
        return

    orig_data_sources = orig_client.get_data_sources()

    print(
        "\n\nYou have entered {} data sources into meta.json. Your source instance contains {} data sources.".format(
            len(DATA_SOURCES), len(orig_data_sources)
        )
    )
    if len(DATA_SOURCES) < len(orig_data_sources):
        print(
            "Any queries against data sources not specified in meta.json will fail to import"
        )

    print("\n")
    has_error = False
    for ds in orig_data_sources:
        if ds["id"] not in DATA_SOURCES:
            print(
                "WARNING: origin data source {} does not appear in meta.json".format(
                    ds["id"]
                )
            )
            has_error = True

    dest_data_sources = dest_client.get_data_sources()
    dest_ds_map = {i["id"]: i for i in dest_data_sources}

    for ds in orig_data_sources:
        dest_id = DATA_SOURCES.get(ds["id"])
        this_ds = dest_ds_map.get(dest_id)

        if dest_id is not None:
            if this_ds is None:
                print(
                    "WARNING: origin data source {} appears in meta.json but does not exist in the destination instance".format(
                        ds["id"]
                    )
                )
                has_error = True
                continue

            elif this_ds["type"] != ds["type"]:
                print(
                    "\n\nWARNING: origin data source {} is of type, destination data source {} is of type {}".format(
                        ds["id"], ds["type"], this_ds["id"], this_ds["type"]
                    )
                )
                continue

    if has_error:
        print("\n\nCheck complete: WARNING")
    else:
        print("\n\nCheck complete. OK")


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
    if not valid_user_meta(dest_users):
        print("ERROR: not all users in meta are present in destination instance.")
        return

    # Check if the user list has been synced between orig and dest
    # In this case, meta.json should be updated
    if user_lists_are_equal(orig_users, dest_users):
        print("OK: orig and dest user lists are in sync")
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

    fix_queries(orig_client, dest_client)


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

        user_api_key = user_with_api_key(
            orig_user_id,
            dest_client,
        )["api_key"]
        user_client = Redash(dest_client.redash_url, user_api_key)
        user_client.update_query(new_query_id, {"options": options})


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

        try:
            dest_user_api_key = user_with_api_key(orig_user_id, dest_client)["api_key"]
        except UserNotFoundException as e:
            print("Query {} - FAIL - Visualizations skipped: ".format(query_id, e))
            continue

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
                user_client = Redash(DESTINATION, dest_user_api_key)

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
            user_api_key = user_with_api_key(
                orig_user_id,
                dest_client,
            )["api_key"]
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
                print(
                    "Widget {} - SKIP - visualization is missing (check missing data source, query, or viz)".format(
                        widget["id"]
                    )
                )
                continue

            user_client.create_widget(
                new_dash_id, data["visualization_id"], data["text"], data["options"]
            )

        meta["dashboards"].update({d["slug"]: new_dashboard["slug"]})


def import_alerts(orig_client, dest_client):

    alerts = orig_client.alerts()
    for a in alerts:

        orig_id = a.get("id")

        dest_id = meta["alerts"].get(orig_id)
        if dest_id:
            print(f"Alert {orig_id} - SKIP - Already imported with new id {dest_id}")
            continue

        this_alert = orig_client.get_alert(a.get("id"))

        orig_target_query_id = this_alert.get("query", {}).get("id")

        # Check the target query is already present
        target_query_id = meta["queries"].get(orig_target_query_id)

        if target_query_id is None:
            print(
                f'Alert {this_alert["id"]} - SKIP - Origin target query {orig_target_query_id} has not been migrated'
            )
            continue

        data = {
            "name": this_alert.get("name"),
            "query_id": target_query_id,
            "options": this_alert.get("options"),
        }

        try:
            resp = dest_client.create_alert(**data)
            dest_id = resp["id"]
            print(f'Alert {this_alert["id"]} - OK - Imported with new id {dest_id}')
        except Exception as e:
            print(f'Alert {this_alert["id"]} - ERROR - {e}')

        meta["alerts"][this_alert.get("id")] = dest_id

        if this_alert.get("rearm"):
            dest_client.update_alert(id=dest_id, rearm=this_alert.get("rearm"))
            print(f'Alert {this_alert["id"]} - OK - Fixed rearm')


def import_favorites(orig_client, dest_client):

    for orig_id, data in meta["users"].items():

        user_orig_api_key = get_api_key(orig_client, orig_id)
        orig_user_client = Redash(ORIGIN, user_orig_api_key)
        dest_user_client = Redash(
            DESTINATION, user_with_api_key(orig_id, dest_client)["api_key"]
        )

        favorite_queries = orig_user_client.paginate(
            orig_user_client.queries, only_favorites=True
        )
        q_counter = 0
        for q in favorite_queries:
            try:
                dest_target_id = meta["queries"].get(q["id"])
                if dest_target_id is None:
                    continue
                dest_user_client.create_favorite(_type="query", id=dest_target_id)
                q_counter += 1
            except Exception as e:
                print(f"Favorites for origin user {orig_id}- ERROR - {e}")

        favorite_dashboards = orig_user_client.paginate(
            orig_user_client.dashboards, only_favorites=True
        )
        dest_dashboards = dest_client.paginate(dest_client.dashboards)
        d_counter = 0
        for d in favorite_dashboards:
            try:
                dest_target_slug = meta["dashboards"].get(d["slug"])
                if dest_target_slug is None:
                    continue

                dest_target_id = get_from_dictlist_by_key(
                    dest_dashboards, "slug", dest_target_slug
                )["id"]

                dest_target_obj = dest_client.get_dashboard(dest_target_id)
                dest_target_id = dest_target_obj["id"]
                dest_user_client.create_favorite(_type="dashboard", id=dest_target_id)
                d_counter += 1
            except Exception as e:
                print(f"Favorites - ERROR - {e}")

        print(
            f"Favorites - OK - Imported {q_counter} queries and {d_counter} dashboards for orig user {orig_id}"
        )


#     _   _ _   _ _ _ _   _
#    | | | | |_(_) (_) |_(_) ___  ___
#    | | | | __| | | | __| |/ _ \/ __|
#    | |_| | |_| | | | |_| |  __/\__ \
#     \___/ \__|_|_|_|\__|_|\___||___/


def valid_user_meta(dest_users):
    """Confirms all users in DEST are present in meta."""

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


def get_api_key(client, user_id):
    response = client._get(f"api/users/{user_id}")

    return response.json()["api_key"]


def get_from_dictlist_by_key(l, key, value):

    return [i for i in l if i.get(key) == value][0]


#
#          __  __      _
#         |  \/  | ___| |_ __ _
#         | |\/| |/ _ \ __/ _` |
#         | |  | |  __/ || (_| |
#         |_|  |_|\___|\__\__,_|
#


# include here any users you already created in the target Redash account.
# the key is the user id in the origin Redash instance.
base_meta = {
    "users": {
        "-1": {
            "id": -1,
            "email": "",
        }
    },
    "queries": {},
    "visualizations": {},
    "dashboards": {},
    "alerts": {},
    "flags": {"viz_import_complete": {}},
    "data_sources": {"-1": -1234},
    "settings": {
        "origin_url": "",
        "origin_admin_api_key": "",
        "destination_url": "",
        "destination_admin_api_key": "",
        "preserve_invite_links": True,
    },
}


def init():
    """Create a meta.json file"""
    if not os.path.exists("meta.json"):
        with open("meta.json", "w") as fp:
            json.dump(base_meta, fp, indent=4)
    else:
        print("meta.json file already exists!")


def get_meta(tries=0):

    if tries > 1:
        raise Exception("Could not create or read meta.json")

    try:
        with open("meta.json", "r") as fp:
            return json.load(fp)
    except FileNotFoundError:
        print("meta.json not found...creating...try again")
        init()
        return get_meta(tries + 1)
    except json.JSONDecodeError:
        raise Exception("badly formed meta.json...please delete and try again")


def save_meta():
    print("Saving meta...")
    with open("meta.json", "w") as f:
        json.dump(meta, f, indent=4)


def save_meta_wrapper(func):
    def wrapped(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(e)
        finally:
            save_meta()

    return wrapped


#      ____ _     ___
#     / ___| |   |_ _|
#    | |   | |    | |
#    | |___| |___ | |
#     \____|_____|___|


try:
    meta = get_meta()
    meta["users"] = {int(key): val for key, val in meta["users"].items()}
    meta["queries"] = {int(key): val for key, val in meta["queries"].items()}
    meta["alerts"] = {int(key): val for key, val in meta["alerts"].items()}
    meta["data_sources"] = {int(key): val for key, val in meta["data_sources"].items()}

    # The Redash instance you're copying from:
    ORIGIN = meta["settings"]["origin_url"]
    ORIGIN_API_KEY = meta["settings"]["origin_admin_api_key"]

    # The Redash account you're copying into:
    DESTINATION = meta["settings"]["destination_url"]
    DESTINATION_API_KEY = meta["settings"]["destination_admin_api_key"]

    PRESERVE_INVITE_LINKS = meta["settings"]["preserve_invite_links"]

    DATA_SOURCES = meta["data_sources"]
except Exception as e:
    print("Script failed during initialization.")
    print("Exception: {}".format(e))


@click.command()
@click.argument(
    "command",
)
def main(command):
    """Redash migration command. Can be used to migrate objects (queries, visualizations, dashboards)
    from one Redash instance to another.

    Usage: python migrate.py <COMMAND>

    Available commands are:

    check_data_sources: compare the data sources written to meta.json against those visible on origin and destination Redash instances

    users: migrate users

    queries: migrate queries and then fix any query-based dropdown list parameter references. Skips queries from users not in meta.json

    visualizations: migrate visualizations for queries that successfully migrated

    dashboards: migrate dashboards. skips widgets with missing visualizations or users

    These should be called in that order. Checking the contents of meta.json between steps to confirm
    expected behavior.
    """
    if command == "init":
        print("meta.json initialized")
        return

    from_client = Redash(ORIGIN, ORIGIN_API_KEY)
    to_client = Redash(DESTINATION, DESTINATION_API_KEY)

    command_map = {
        "check_data_sources": check_data_sources,
        "users": import_users,
        "queries": import_queries,
        "visualizations": import_visualizations,
        "dashboards": import_dashboards,
        "alerts": import_alerts,
        "favorites": import_favorites,
    }

    this_command = save_meta_wrapper(command_map.get(command))

    if this_command is None:
        print("No command provided. See --help for instructions")

    this_command(from_client, to_client)


if __name__ == "__main__":
    main()
