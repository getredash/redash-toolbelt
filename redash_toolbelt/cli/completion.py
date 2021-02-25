"""Utility functions for CLI auto-completion functionality."""
# pylint: disable=unused-argument, broad-except
import os

from natsort import natsorted, ns

from redash_toolbelt.cli.context import CONTEXT

SORT_BY_KEY = 0
SORT_BY_DESC = 1


def _finalize_completion(
        candidates: list,
        incomplete: str = '',
        sort_by: int = SORT_BY_KEY,
        nat_sort: bool = False
) -> list:
    """Sort and filter candidates list.

    candidates are sorted with natsort library by sort_by key.

    Args:
        candidates (list):  completion dictionary to filter
        incomplete (str):   incomplete string at the cursor
        sort_by (str):      SORT_BY_KEY or SORT_BY_DESC
        nat_sort (bool):    if true, uses the natsort package for sorting

    Returns:
        filtered and sorted candidates list

    Raises:
        ValueError in case of wrong sort_by parameter
    """
    if sort_by not in (SORT_BY_KEY, SORT_BY_DESC):
        raise ValueError("sort_by should be 0 or 1.")
    incomplete = incomplete.lower()
    if len(candidates) == 0:
        return candidates
    # remove duplicates
    candidates = list(set(candidates))

    if isinstance(candidates[0], str):
        # list of strings filtering and sorting
        filtered_candidates = [
            element for element in candidates
            if element.lower().find(incomplete) != -1
        ]
        if nat_sort:
            return natsorted(
                seq=filtered_candidates,
                alg=ns.IGNORECASE
            )
        # this solves that case-insensitive sorting is not stable in ordering
        # of "equal" keys (https://stackoverflow.com/a/57923460)
        return sorted(
            filtered_candidates,
            key=lambda x: (x.casefold(), x)
        )
    if isinstance(candidates[0], tuple):
        # list of tuples filtering and sorting
        filtered_candidates = [
            element for element in candidates
            if element[0].lower().find(incomplete) != -1
            or element[1].lower().find(incomplete) != -1
        ]
        if nat_sort:
            return natsorted(
                seq=filtered_candidates,
                key=lambda k: k[sort_by],
                alg=ns.IGNORECASE
            )
        return sorted(
            filtered_candidates,
            key=lambda x: (x[sort_by].casefold(), x[sort_by])
        )
    raise ValueError(
        "candidates should be a list of strings or a list of tuples."
    )


def file_list(incomplete="", suffix="", description=""):
    """Prepare a list of files with specific parameter."""
    if os.path.isdir(incomplete):
        # given string is a directory, so we scan this directory and
        # add it as a prefix
        directory = incomplete
        incomplete = ""
        prefix = os.path.realpath(incomplete) + "/"
    else:
        # given string is NOT a directory so we just scan the current
        # directory
        directory = os.getcwd()
        prefix = ""
    options = []
    for file_name in os.listdir(directory):
        if os.path.isfile(file_name) \
                and file_name.endswith(suffix):
            options.append((prefix + file_name, description))
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete,
        sort_by=SORT_BY_KEY
    )


def ini_files(ctx, args, incomplete):
    """Prepare a list of ini files."""
    return file_list(
        incomplete=incomplete,
        suffix=".ini",
        description="INI file"
    )


def connections(ctx, args, incomplete):
    """Prepare a list of config connections."""
    # since ctx does not have an obj here, we re-create the object
    CONTEXT.set_connection_from_args(args)
    options = []
    for section in CONTEXT.config.sections():
        options.append(section)
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete
    )


def queries(ctx, args, incomplete):
    """Prepare a list of queries."""
    # since ctx does not have an obj here, we re-create the object
    CONTEXT.set_connection_from_args(args)
    api = CONTEXT.get_api()
    options = []
    for _ in api.queries():
        options.append((str(_["id"]), _["name"]))
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete,
        sort_by=SORT_BY_DESC
    )


def sources(ctx, args, incomplete):
    """Prepare a list of data sources."""
    # since ctx does not have an obj here, we re-create the object
    CONTEXT.set_connection_from_args(args)
    api = CONTEXT.get_api()
    options = []
    for _ in api.data_sources():
        options.append((str(_["id"]), _["name"]))
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete,
        sort_by=SORT_BY_DESC
    )


def dashboards(ctx, args, incomplete):
    """Prepare a list of dashboards."""
    # since ctx does not have an obj here, we re-create the object
    CONTEXT.set_connection_from_args(args)
    api = CONTEXT.get_api()
    options = []
    for _ in api.dashboards():
        options.append((str(_["slug"]), _["name"]))
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete,
        sort_by=SORT_BY_DESC
    )


def users(ctx, args, incomplete):
    """Prepare a list of users."""
    # since ctx does not have an obj here, we re-create the object
    CONTEXT.set_connection_from_args(args)
    api = CONTEXT.get_api()
    options = []
    for _ in api.users():
        options.append((str(_["id"]), _["name"]))
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete,
        sort_by=SORT_BY_DESC
    )


def groups(ctx, args, incomplete):
    """Prepare a list of users groups."""
    # since ctx does not have an obj here, we re-create the object
    CONTEXT.set_connection_from_args(args)
    api = CONTEXT.get_api()
    options = []
    for _ in api.groups():
        options.append((str(_["id"]), _["name"]))
    return _finalize_completion(
        candidates=options,
        incomplete=incomplete,
        sort_by=SORT_BY_DESC
    )
