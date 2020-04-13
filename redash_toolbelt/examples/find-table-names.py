import itertools, json, re
import click
import pytest
from redash_toolbelt import Redash


def find_table_names(url, key, data_source_id):

    client = Redash(url, key)

    schema_tables = [
        token.get("name")
        for token in client._get(f"api/data_sources/{data_source_id}/schema")
        .json()
        .get("schema", [])
    ]

    queries = [
        query
        for query in client.paginate(client.queries)
        if query.get("data_source_id", None) == int(data_source_id)
    ]

    tables_by_qry = {
        query["id"]: [
            table
            for table in extract_table_names(query["query"])
            if table in schema_tables or len(schema_tables) == 0
        ]
        for query in queries
    }

    return tables_by_qry


def extract_table_names(str_sql):

    # This regex captures three groups:
    #
    #   0. A FROM or JOIN statement
    #   1. The whitespace character(s) between FROM/JOIN and table name
    #   2. The table name
    PATTERN = re.compile(
        r"(?:FROM|JOIN)(?:\s+)([^\s\(\)]+)", flags=re.IGNORECASE | re.UNICODE
    )

    return [re.sub(r'[\[\]\"\`]', '', match) for match in re.findall(PATTERN, str_sql)]


def print_summary(tables_by_qry):
    """Builds a summary showing table names and count of queries that reference them."""

    summary = {
        table_name: sum(
            [1 for tables in tables_by_qry.values() if table_name in tables]
        )
        for table_name in itertools.chain(*tables_by_qry.values())
    }

    align = max([len(table_name) for table_name in summary.keys()])

    print("\n")
    print(f"{'table':>{align}} | {'number of queries':>17}")
    print("-" * align + " | " + "-" * 17)

    for t, num in sorted(summary.items(), key=lambda item: item[1], reverse=True):
        print(f"{t:>{align}} | {num:>17}")

    print("\n")


def print_details(tables_by_qry):
    """Prints out (query_id, tablename) tuples"""

    details = [
        [(query, table) for table in tables] for query, tables in tables_by_qry.items()
    ]

    for row in itertools.chain(*details):
        print(",".join([str(i) for i in row]))


@click.command()
@click.argument("url",)
@click.argument("key",)
@click.argument("data_source_id")
@click.option("--detail", is_flag=True, help="Prints out all table/query pairs?")
def main(url, key, data_source_id, detail):
    """Find table names referenced in queries against DATA_SOURCE_ID"""

    data = find_table_names(url, key, data_source_id)

    if detail:
        print_details(data)
    else:
        print_summary(data)


if __name__ == "__main__":
    main()


def test_1():

    sql = """
    SELECT field FROM table0 LEFT JOIN table1 ON table0.field = table1.field
    """

    tables = extract_table_names(sql)

    assert tables == ["table0", "table1"]


def test_2():

    sql = """
    SELECT field FROM table0 as a LEFT JOIN table1 as b ON a.field = b.field
    """

    tables = extract_table_names(sql)

    assert tables == ["table0", "table1"]


def test_3():

    sql = """
    SELECT field FROM table0 a LEFT JOIN table1 b ON a.field = b.field
    """

    tables = extract_table_names(sql)

    assert tables == ["table0", "table1"]


def test_4():

    sql = """
    SELECT field FROM schema.table0 a LEFT JOIN schema.table1 b ON a.field = b.field
    """

    tables = extract_table_names(sql)

    assert tables == ["schema.table0", "schema.table1"]


def test_5():

    sql = """
    SELECT field
    FROM
        table0
    LEFT JOIN
        table1
    """

    tables = extract_table_names(sql)

    assert tables == ["table0", "table1"]


def test_6():

    sql = """
    SELECT field FROM table1,table0
    WHERE table0.field = table1.field
    """

    tables = extract_table_names(sql)

    assert tables == ["schema.table0", "schema.table1"]
def test_7():

    sql = """
    SELECT field FROM [table0] LEFT JOIN [table1] ON [table0].field = [table1].field
    """

    tables = extract_table_names(sql)

    assert tables == ["table0", "table1"]
