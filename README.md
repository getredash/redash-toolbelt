redash-toolbelt - The official API client and utilities to manage a Redash instance


- [INSTALLATION](#installation)
- [EXAMPLE SCRIPTS](#example-scripts)


## INSTALLATION

To install it you will need Python 3.6 or above. We recommend that you use a [virtual environment].


```bash
pip install --upgrade redash-toolbelt
```

This command will update `redash-toolbelt` if you have already installed it.

[virtual environment]: https://pythonbasics.org/virtualenv/


## EXAMPLE SCRIPTS

With `redash-toolbelt` installed you will have access to several example CLI scripts within your terminal.

```text

gdpr-scrub                  Search for a string term in  your Redash queries
                            and query results. The script returns a list of
                            URLs in your instance that contain references to
                            the search term you provide
find-tables                 Search the text of queries against a data source
                            to see which table names are used in queries of
                            that source. This script relies on regex that is
                            tested against ANSI SQL.
clone-dashboard-and-queries Completely duplicate a dashboard by copying all 
                            its queries and visualizations.
export-queries              Export all the queries of your Redash instance
                            as text files.
redash-migrate              Move data from one instance of Redash to another.
                            See docs/redash-migrate/README.md for more info
```
