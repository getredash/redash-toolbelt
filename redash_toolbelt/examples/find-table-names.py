from redash_toolbelt import Redash
import json, re, click, itertools


# This regex captures three groups:
#
#   0. A FROM or JOIN statement
#   1. The whitespace character between FROM/JOIN and table name
#   2. The table name

PATTERN = re.compile(r"(FROM|JOIN)( )([^\s\(\)]+)", flags=re.IGNORECASE)


def find_table_names(url, key, data_source_id):

    client = Redash(url, key)

    queries = [
        i
        for i in client.paginate(client.queries)
        if i.get("data_source_id", None) == int(data_source_id)
    ]

    tables_by_qry = {
        i["id"]: [re_groups[2] for re_groups in re.findall(PATTERN, i["query"])]
        for i in queries
        if re.search(PATTERN, i["query"])
    }

    return tables_by_qry


def print_summary(tables_by_qry):
    """Builds a summary showing table names and count of queries that reference it."""

    summary = {
        t: sum([1 for qry, tables in tables_by_qry.items() if t in tables])
        for t in itertools.chain(*tables_by_qry.values())
    }

    align = max([len(t) for t in summary.keys()])

    print(f"\n\n{'table':>{align}} | {'number of queries':>17}")
    print("-" * align + " | " + "-" * 17)
    for t, num in summary.items():
        print(f"{t:>{align}} | {num:>17}")
    print("\n")


def print_details(tables_by_qry):
    """Prints out (query_id, tablename) tuples"""

    details = [[(qry, t) for t in tables] for qry, tables in tables_by_qry.items()]

    for row in itertools.chain(*details):
        print(",".join([str(i) for i in row]))


@click.command()
@click.argument("url",)
@click.argument("key",)
@click.argument("data_source_id")
@click.option(
    "--detail", default="no", help="Print out all table/query pairs? (yes or no)"
)
def main(url, key, data_source_id, detail):
    """Find table names referenced in queries against DATA_SOURCE_ID"""

    data = find_table_names(url, key, data_source_id)

    if detail == "yes":
        print_details(data)
    else:
        print_summary(data)


if __name__ == "__main__":
    main()
