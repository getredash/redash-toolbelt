import itertools, json, re
import click
from redash_toolbelt import Redash


# This regex captures three groups:
#
#   0. A FROM or JOIN statement
#   1. The whitespace character between FROM/JOIN and table name
#   2. The table name
PATTERN = re.compile(r"(?:FROM|JOIN)(?: )([^\s\(\)]+)", flags=re.IGNORECASE)


def find_table_names(url, key, data_source_id):

    client = Redash(url, key)

    schema_tables = [
        token.get("name")
        for token in client._get(f"api/data_sources/{data_source_id}/schema")
        .json()
        .get("schema", [])
    ]

    queries = [
        i
        for i in client.paginate(client.queries)
        if i.get("data_source_id", None) == int(data_source_id)
    ]

    tables_by_qry = {
        i["id"]: [
            match
            for match in re.findall(PATTERN, i["query"])
            if match in schema_tables or len(schema_tables) == 0
        ]
        for i in queries
        if re.search(PATTERN, i["query"])
    }

    return tables_by_qry


def print_summary(tables_by_qry):
    """Builds a summary showing table names and count of queries that reference them."""

    summary = {
        t: sum([1 for tables in tables_by_qry.values() if t in tables])
        for t in itertools.chain(*tables_by_qry.values())
    }

    align = max([len(t) for t in summary.keys()])

    print("\n")
    print(f"{'table':>{align}} | {'number of queries':>17}")
    print("-" * align + " | " + "-" * 17)

    for t, num in sorted(summary.items(), key=lambda item: item[1], reverse=True):
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
    "--detail", is_flag=True, help="Prints out all table/query pairs?"
)
def main(url, key, data_source_id, detail):
    """Find table names referenced in queries against DATA_SOURCE_ID"""

    data = find_table_names(url, key, data_source_id)

    if detail:
        print_details(data)
    else:
        print_summary(data)


if __name__ == "__main__":
    main()
