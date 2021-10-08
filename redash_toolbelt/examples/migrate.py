"""
Author: Jesse Whitehouse
Last updated: 10 October 2021
Notes:
  Copied from https://gist.github.com/arikfr/2c7d09f6837b256c58a3d3ef6a97f61a
"""


import sys, os, json, logging, textwrap
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


def import_data_sources(orig_client, dest_client):
    """Create stub data sources at DESTINATION based on the data sources in ORIGIN."""

    orig_data_sources = orig_client.get_data_sources()
    allowed_types = {
        i["type"]: i for i in dest_client._get("api/data_sources/types").json()
    }

    for ds in orig_data_sources:

        dsid = ds["id"]

        if dsid in meta["data_sources"]:
            print(
                "WARNING: origin data source {} -- SKIP -- already exists".format(dsid)
            )
            continue

        ds_def = orig_client.get_data_source(dsid)

        if ds_def["type"] not in allowed_types:
            print(
                "WARNING: origin data source {} -- SKIP -- destination instance does not support this type: {}".format(
                    dsid, ds_def["type"]
                )
            )
            continue

        new_data_source_def = {
            "name": ds_def["name"],
            "_type": ds_def["type"],
            "options": ds_def["options"],
        }

        try:
            new_ds = dest_client.create_data_source(**new_data_source_def).json()
            meta["data_sources"][dsid] = new_ds["id"]
        except Exception as e:
            print(
                "ERROR: origin data source {} -- FAIL -- could not be imported: {}".format(
                    dsid, str(e)
                )
            )
            continue


def import_destinations(orig_client, dest_client):
    """Create stub alert destinations at DESTINATION based on the alert destinations in ORIGIN."""

    ALLOWED_TYPES = [
        i["type"] for i in dest_client._get("api/destinations/types").json()
    ]

    orig_destinations = orig_client._get("api/destinations").json()

    for dest in orig_destinations:
        id = dest["id"]
        _type = dest["type"]

        if _type not in ALLOWED_TYPES:
            print(
                f"Destination {id} -- SKIP -- Type {_type} is not enabled in destination instance"
            )
            continue

        if id in meta["destinations"]:
            print(
                f"Destination {id} -- SKIP -- Already present in destination instance"
            )
            continue

        details = orig_client._get(f"api/destinations/{id}").json()

        new_data = {"name": dest["name"], "type": _type, "options": details["options"]}

        try:
            resp = dest_client._post("api/destinations", json=new_data).json()
            dest_id = resp["id"]
            meta["destinations"][id] = dest_id
            print(
                f"Destination {id} -- OK -- Created stub destination in destination with id {dest_id}"
            )
        except Exception as e:
            print(f"Destination {id} - ERROR - {e}")


def import_groups(orig_client, dest_client):

    o_groups = orig_client._get("api/groups").json()

    for group in o_groups:

        id = group["id"]
        name = group["name"]

        if id in meta["groups"]:
            print(f"Origin group {id} -- SKIP -- Already exists in destination")
            continue

        # Post to GroupListResource to create the group in the destination
        resp = dest_client._post("api/groups", json={"name": name}).json()
        dest_id = resp["id"]

        print(
            f"Origin group {id} -- OK -- Group created at destination with id {dest_id}"
        )

        meta["groups"][id] = dest_id

        # Get from GroupMemberListResource
        members = orig_client._get(f"api/groups/{id}/members").json()
        if not members:
            print(f"Origin group {id} -- WARNING -- No members in origin group")
            continue

        for m in members:
            dest_member_id = meta["users"].get(m["id"]).get("id")
            if dest_member_id is None:
                print(
                    f"Origin group {id} -- ERROR -- Origin group member {m['id']} not present in destination"
                )
                continue

            # Post to GroupMemberListResource
            resp = dest_client._post(
                f"api/groups/{dest_id}/members", json={"user_id": dest_member_id}
            ).json()
            print(
                f"Origin group {id} -- OK -- Dest user {dest_member_id} added to {dest_id}"
            )

        print(
            f"Origin group {id} -- OK -- Finished copying users into destination group {dest_id}"
        )

        # Get from GroupDataSourceListResource
        data_sources = orig_client._get(f"api/groups/{id}/data_sources").json()

        if not data_sources:
            print(f"Origin group {id} -- WARNING -- No data sources tied to this group")
            continue

        for d in data_sources:
            ds_id = d["id"]
            dest_ds_id = meta["data_sources"].get(ds_id)

            if dest_ds_id is None:
                print(
                    f"Origin group {id} -- ERROR -- Origin data source {ds_id} not present in destination"
                )
                continue

            # Post to GroupDataSourceListResource
            resp = dest_client._post(
                f"api/groups/{dest_id}/data_sources",
                json={"data_source_id": dest_ds_id},
            ).json()
            print(
                f"Origin group {id} -- OK -- Associated destination group {dest_id} with data source {dest_ds_id}"
            )

            # Post to GroupDataSourceResource
            view_only = d.get("view_only", False)
            resp = dest_client._post(
                f"api/groups/{dest_id}/data_sources/{dest_ds_id}",
                json={"view_only": view_only},
            ).json()
            print(
                f"Origin group {id} -- OK -- View only permission on destination group {dest_id} for data source {dest_ds_id} set to {view_only}"
            )


def import_users(orig_client, dest_client):
    """This function expects that the meta object already includes details for admin users on the DEST instance.
    If you already created users on the DEST instance, enter their details into meta before using this function.
    """

    print("Importing users...")

    def user_lists_are_equal(orig_list, dest_list):

        dest_user_emails = set([i["email"] for i in dest_list])
        orig_user_emails = set([i["email"] for i in orig_list])

        return dest_user_emails == orig_user_emails

    def get_all_users(client):

        active_users = client.paginate(client.users, only_disabled=False)
        disabled_users = client.paginate(client.users, only_disabled=True)

        return [*active_users, *disabled_users]

    orig_users = get_all_users(orig_client)
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

    orig_users = sorted(orig_users, key=lambda x: x.get("created_at", 0))
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
            "disabled": user["is_disabled"],
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


def disable_users(orig_client, dest_client):

    count_disabled = 0
    for orig_id, dest_user in meta["users"].items():
        if dest_user.get("disabled") is True:
            print(
                f'Origin user {orig_id} is disabled at origin. Disabling {dest_user["id"]} at destination'
            )
            dest_client.disable_user(dest_user["id"])
            count_disabled += 1
        else:
            continue

    if count_disabled > 0:
        print(f"{count_disabled} users were disabled in the destination instance")
    else:
        print("No users were disabled")


def import_queries(orig_client, dest_client):

    queries_that_depend_on_queries = []

    print("Import queries...")

    queries = orig_client.paginate(orig_client.queries)
    queries = sorted(queries, key=lambda x: x.get("created_at", 0))

    for query in queries:

        options = query["options"]
        already_delayed = False
        for p in options.get("parameters", []):
            if not already_delayed and "queryId" in p:
                queries_that_depend_on_queries.append(query)
                already_delayed = True
                break

        # Wait to import this query until all others have been imported
        if already_delayed:
            continue

        def import_query_subroutine(query):
            origin_id = query["id"]

            data_source_id = DATA_SOURCES.get(query["data_source_id"])

            if origin_id in meta["queries"] or str(origin_id) in meta["queries"]:
                print("Query {} - SKIP - was already imported".format(origin_id))
                return

            if data_source_id is None:
                print(
                    "Query {} - SKIP - data source has not been mapped ({})".format(
                        origin_id, query["data_source_id"]
                    )
                )
                return

            data = {
                "data_source_id": data_source_id,
                "query": query["query"],
                "is_archived": query["is_archived"],
                "schedule": convert_schedule(query["schedule"]),
                "description": query["description"],
                "name": query["name"],
                "options": query["options"],
                "tags": query["tags"],
            }

            try:
                user_api_key = user_with_api_key(query["user"]["id"], dest_client)[
                    "api_key"
                ]
            except UserNotFoundException as e:
                print("Query {} - FAIL - {}".format(query["id"], e))
                return

            print("Query {} - OK  - importing".format(origin_id))

            user_client = Redash(DESTINATION, user_api_key)

            try:
                response = user_client.create_query(data)
            except Exception as e:
                print("Query {} - FAIL - {}".format(origin_id, e))
                return

            destination_id = response.json()["id"]
            meta["queries"][query["id"]] = destination_id

            # New queries are always saved as drafts.
            # Need to sync the ORIGIN draft status to DESTINATION.
            if not query["is_draft"]:
                response = dest_client.update_query(destination_id, {"is_draft": False})

        import_query_subroutine(query)

    for query in queries_that_depend_on_queries:

        # fix query reference
        options = query["options"]
        for p in options.get("parameters", []):
            if "queryId" in p:
                p["queryId"] = meta["queries"].get(p["queryId"])

        query["options"] = options

        import_query_subroutine(query)

    # fix_queries(orig_client, dest_client)


def fix_queries(orig_client, dest_client):
    """
    This runs after importing all queries, so we can update the query id reference
    in parameter definitions.
    """
    print("Updating queries options...")

    if not meta["flags"].get("fixed_queries"):
        meta["flags"]["fixed_queries"] = []

    for query_id, new_query_id in meta["queries"].items():

        if new_query_id in meta["flags"]["fixed_queries"]:
            print(f"Destination query {new_query_id} - SKIP - Already fixed")
            continue

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

        meta["flags"]["fixed_queries"].append(new_query_id)


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
    dashboards = sorted(dashboards, key=lambda x: x.get("created_at", 0))

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
            new_dash_id, {"is_draft": False, "tags": d["tags"]}
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
    alerts = sorted(alerts, key=lambda x: x.get("created_at", 0))
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

        # A post to the subscriptions handler endpoint automatically subscribes the current user
        # Unless it includes an alert destination_id in which case the destination is subscribed
        # We'll need a user client to subscribe the user. There's no way for an admin to sub-
        # scribe a user email address directly.

        subscriptions = (
            orig_client._get(f"api/alerts/{orig_id}/subscriptions").json() or []
        )
        subscriptions_base_kwargs = {"alert_id": dest_id}

        for sub in subscriptions:
            if "destination" in sub:
                # This points to an alert destination that exits
                sub_args = {
                    **subscriptions_base_kwargs,
                    "destination_id": meta["destinations"].get(
                        sub["destination"]["id"]
                    ),
                }
                dest_client._post(f"api/alerts/{dest_id}/subscriptions", json=sub_args)
            else:
                # This is a user subscription
                dest_user = meta["users"][sub["user"]["id"]]
                user_dest_api_key = dest_user["api_key"]
                dest_user_client = Redash(DESTINATION, user_dest_api_key)
                dest_user_client._post(
                    f"api/alerts/{dest_id}/subscriptions",
                    json=subscriptions_base_kwargs,
                )


def import_favorites(orig_client, dest_client):

    for orig_id, data in meta["users"].items():

        user_dest = user_with_api_key(orig_id, dest_client)
        user_dest_api_key = user_dest["api_key"]
        user_orig_api_key = get_api_key(orig_client, orig_id)

        if "disabled" in data and data["disabled"]:
            print(f"User {user_dest['email']} is disabled. Skipping import.")
            continue

        orig_user_client = Redash(ORIGIN, user_orig_api_key)
        dest_user_client = Redash(DESTINATION, user_dest_api_key)

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


# Don't enter information here. Run `redash-migrate init` to create a copy of this file
base_meta = {
    "users": {},
    "queries": {},
    "visualizations": {},
    "dashboards": {},
    "alerts": {},
    "flags": {"viz_import_complete": {}},
    "data_sources": {},
    "groups": {},
    "destinations": {},
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

    def clear():

        # for windows
        if os.name == "nt":
            _ = os.system("cls")

        # for mac and linux(here, os.name is 'posix')
        else:
            _ = os.system("clear")

    if os.path.exists("meta.json"):
        print("meta.json file already exists!")
        print("Consider renaming this file and try to run redash-migrate init again.")
        return

    clear()
    logo = r"""
           ___           ___           ___           ___           ___           ___
          /\  \         /\  \         /\  \         /\  \         /\  \         /\__\
         /::\  \       /::\  \       /::\  \       /::\  \       /::\  \       /:/  /
        /:/\:\  \     /:/\:\  \     /:/\:\  \     /:/\:\  \     /:/\ \  \     /:/__/
       /::\~\:\  \   /::\~\:\  \   /:/  \:\__\   /::\~\:\  \   _\:\~\ \  \   /::\  \ ___
      /:/\:\ \:\__\ /:/\:\ \:\__\ /:/__/ \:|__| /:/\:\ \:\__\ /\ \:\ \ \__\ /:/\:\  /\__\
      \/_|::\/:/  / \:\~\:\ \/__/ \:\  \ /:/  / \/__\:\/:/  / \:\ \:\ \/__/ \/__\:\/:/  /
         |:|::/  /   \:\ \:\__\    \:\  /:/  /       \::/  /   \:\ \:\__\        \::/  /
         |:|\/__/     \:\ \/__/     \:\/:/  /        /:/  /     \:\/:/  /        /:/  /
         |:|  |        \:\__\        \::/__/        /:/  /       \::/  /        /:/  /
          \|__|         \/__/         ~~            \/__/         \/__/         \/__/
     ___                       ___           ___           ___           ___           ___
    /\__\          ___        /\  \         /\  \         /\  \         /\  \         /\  \
   /::|  |        /\  \      /::\  \       /::\  \       /::\  \        \:\  \       /::\  \
  /:|:|  |        \:\  \    /:/\:\  \     /:/\:\  \     /:/\:\  \        \:\  \     /:/\:\  \
 /:/|:|__|__      /::\__\  /:/  \:\  \   /::\~\:\  \   /::\~\:\  \       /::\  \   /::\~\:\  \
/:/ |::::\__\  __/:/\/__/ /:/__/_\:\__\ /:/\:\ \:\__\ /:/\:\ \:\__\     /:/\:\__\ /:/\:\ \:\__\
\/__/~~/:/  / /\/:/  /    \:\  /\ \/__/ \/_|::\/:/  / \/__\:\/:/  /    /:/  \/__/ \:\~\:\ \/__/
      /:/  /  \::/__/      \:\ \:\__\      |:|::/  /       \::/  /    /:/  /       \:\ \:\__\
     /:/  /    \:\__\       \:\/:/  /      |:|\/__/        /:/  /     \/__/         \:\ \/__/
    /:/  /      \/__/        \::/  /       |:|  |         /:/  /                     \:\__\
    \/__/                     \/__/         \|__|         \/__/                       \/__/
"""

    print(logo)
    meta = base_meta

    msg = textwrap.dedent(
        """
    Thank you for using redash-migrate. To begin, please respond to the following prompts.

    It's important to provide the correct information here to ensure that all objects are copied
    correctly from the ORIGIN instance to the DESTINATION instance.

    Please note that this script will solicit an email address from you. But NO EMAILS WILL BE SENT.
    """
    )

    print(msg)

    print(
        "\n\nFirst, please enter information about connecting to your origin instance: "
    )

    origin_url = input(
        "Please enter the origin URL. Example: https://app.redash.io/acme: "
    )
    origin_admin_api_key = input(
        "Please enter an admin API key for the origin instance: "
    )
    origin_admin_user_id = input(
        "Please enter the user id for this admin on the origin instance: "
    )

    meta["settings"]["origin_url"] = origin_url
    meta["settings"]["origin_admin_api_key"] = origin_admin_api_key

    print("\n\nNext, we'll enter the same information for the new")

    destination_url = input(
        "Please enter the destination URL. Example: http://localhost: "
    )
    destination_admin_api_key = input(
        "Please enter an admin API key for the destination instance: "
    )
    destination_admin_user_id = input(
        "Please enter the user id for this admin on the destination instance: "
    )
    destination_admin_email_address = input(
        "Please enter the email address for the destination admin user: "
    )

    meta["settings"]["destination_url"] = destination_url
    meta["settings"]["destination_admin_api_key"] = destination_admin_api_key

    meta["users"][origin_admin_user_id] = {
        "id": destination_admin_user_id,
        "email": destination_admin_email_address,
    }

    print("Ready to proceed.")

    with open("meta.json", "w") as fp:
        json.dump(base_meta, fp, indent=4)


def get_meta():

    with open("meta.json", "r") as fp:
        return json.load(fp)


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


def make_global_meta():
    global meta
    global ORIGIN
    global ORIGIN_API_KEY
    global DESTINATION
    global DESTINATION_API_KEY
    global PRESERVE_INVITE_LINKS
    global DATA_SOURCES

    meta = get_meta()
    meta["users"] = {int(key): val for key, val in meta["users"].items()}
    meta["queries"] = {int(key): val for key, val in meta["queries"].items()}
    meta["alerts"] = {int(key): val for key, val in meta["alerts"].items()}
    meta["data_sources"] = {int(key): val for key, val in meta["data_sources"].items()}
    meta["groups"] = {int(key): val for key, val in meta["groups"].items()}
    meta["destinations"] = {int(key): val for key, val in meta["destinations"].items()}

    # The Redash instance you're copying from:
    ORIGIN = meta["settings"]["origin_url"]
    ORIGIN_API_KEY = meta["settings"]["origin_admin_api_key"]

    # The Redash account you're copying into:
    DESTINATION = meta["settings"]["destination_url"]
    DESTINATION_API_KEY = meta["settings"]["destination_admin_api_key"]
    PRESERVE_INVITE_LINKS = meta["settings"]["preserve_invite_links"]
    DATA_SOURCES = meta["data_sources"]


@click.command()
@click.argument(
    "command",
)
@click.version_option(version="1.0")
def main(command):
    """Redash migration tool. Can be used to migrate objects (users, queries, visualizations, dashboards, alerts, and favorites)
    from one Redash instance to another.

    Commands:

      \b
      init                  Create a meta.json template file in your working directory. You will be
                            prompted to enter authentication information for your origin and desti-
                            nation instances.

      \b
      data_sources          Create stubs of your origin data sources in your destination instance

      \b
      check_data_sources    Compare the data sources in your origin and destination instances

      \b
      users                 Duplicate user names, emails, and enabled/disabled status from the
                            origin instance into the destination instance.

      \b
      groups                Duplicate group names, member lists, and data source permissions from
                            the origin instance into the destination instance.

      \b
      queries               Duplicate queries from the origin instance to the destination instance.
                            Skips queries with an unknown destination data source or user.

      \b
      visualizations        Duplicate visualizations from the origin instance to the destination
                            instance. Only duplicates visualizations for queries moved by the
                            `queries` command.

      \b
      dashboards            Duplicate dashboards from the origin instance to the destination
                            instance. Skips any dashboard widget whose visualization was not moved
                            using the `visualizations` command.

      \b
      destinations          Create stubs of your origin alert destinations in your destination
                            instance

      \b
      alerts                Duplicate alert definitions from the origin instance to the destination
                            instance. Skips alerts that point to queries that were not migrated by
                            the `queries` command. Run the `destinations` command first.

      \b
      favorites             Duplicate favorite flags on queries and dashboards from the origin
                            instance to the destination instance.

      \b
      disable_users         Disable users in the destination instance that are disabled in the
                            origin instance.

      \b
      Commands should be called in the order specified here. Check meta.json between steps to
      confirm expected behavior.
    """

    try:
        make_global_meta()
    except Exception as e:
        if command == "init":
            pass
        else:
            print("Script could not proceed because of a problem reading meta.json")
            print("Please run redash-migrate init before proceeding")
            return

    if command == "init":
        return init()

    from_client = Redash(ORIGIN, ORIGIN_API_KEY)
    to_client = Redash(DESTINATION, DESTINATION_API_KEY)

    command_map = {
        "data_sources": import_data_sources,
        "check_data_sources": check_data_sources,
        "users": import_users,
        "groups": import_groups,
        "destinations": import_destinations,
        "queries": import_queries,
        "visualizations": import_visualizations,
        "dashboards": import_dashboards,
        "alerts": import_alerts,
        "favorites": import_favorites,
        "disable_users": disable_users,
    }

    _command = command_map.get(command)
    if _command is None:
        print(f"{command} is not a valid command. See --help for instructions")
        return

    wrapped = save_meta_wrapper(command_map.get(command))

    if wrapped is None:
        print("No command provided. See --help for instructions")

    return wrapped(from_client, to_client)


if __name__ == "__main__":
    main()
