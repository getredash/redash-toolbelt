# rtb - redash-toolbelt command line client reference

This document lists the help texts of all commands as a reference, to search for and through it.

## Command group: config

```
Usage: rtb config [OPTIONS] COMMAND [ARGS]...

  List and edit configurations.

  Configurations are identified by the section identifier in the config
  file. Each configuration represent a Redash deployment.

  A minimal configuration has the following entries:

  [example.org]
  REDASH_BASE_URL=https://redash.example.org/
  REDASH_API_TOKEN=token

Options:
  -h, --help  Show this message and exit.

Commands:
  edit  Edit the user-scope configuration file.
  list  List configured connections.
```

### Command: config edit

```
Usage: rtb config edit [OPTIONS]

  Edit the user-scope configuration file.

Options:
  -h, --help  Show this message and exit.
```

### Command: config list

```
Usage: rtb config list [OPTIONS]

  List configured connections.

  This command lists all configured redash connections from the currently
  used config file.

  The connection identifier can be used with the --connection option in
  order to use a specific redash instance.

Options:
  -h, --help  Show this message and exit.
```

## Command group: dashboard

```
Usage: rtb dashboard [OPTIONS] COMMAND [ARGS]...

  List and open dashboards.

  Dashboards arrange visualizations of queries on a grid. They are
  identified by their slug, which is unique string and part of the access
  URL.

Options:
  -h, --help  Show this message and exit.

Commands:
  list  List dashboards.
  open  Open dashboard in the browser.
```

### Command: dashboard list

```
Usage: rtb dashboard list [OPTIONS]

  List dashboards.

  This command lists all dashboards from a redash deployment.

Options:
  --id-only   Lists only dashboard identifier and no labels or other meta
              data. This is useful for piping the ids into other commands.

  --raw       Outputs raw JSON response of the API.
  -h, --help  Show this message and exit.
```

### Command: dashboard open

```
Usage: rtb dashboard open [OPTIONS] DASHBOARD_SLUGS...

  Open dashboard in the browser.

  With this command, you can open dashboards from in your browser (e.g. in
  order to change them). The command accepts multiple dashboard IDs.

Options:
  -h, --help  Show this message and exit.
```

## Command group: group

```
Usage: rtb group [OPTIONS] COMMAND [ARGS]...

  List and open user groups.

  User groups are identified with a unique integer.

Options:
  -h, --help  Show this message and exit.

Commands:
  list  List Groups.
  open  Open a user profile in the browser.
```

### Command: group list

```
Usage: rtb group list [OPTIONS]

  List Groups.

  This command lists all user groups from a redash deployment.

Options:
  --id-only   Lists only data source identifier and no labels or other meta
              data. This is useful for piping the ids into other commands.

  --raw       Outputs raw JSON response of the API.
  -h, --help  Show this message and exit.
```

### Command: group open

```
Usage: rtb group open [OPTIONS] GROUP_IDS...

  Open a user profile in the browser.

  With this command, you can open a user group in your browser The command
  accepts multiple user group IDs.

Options:
  -h, --help  Show this message and exit.
```

## Command group: query

```
Usage: rtb query [OPTIONS] COMMAND [ARGS]...

  List and open queries.

  Queries retrieve data from a data source based on a custom query string.
  They are identified with a unique integr

Options:
  -h, --help  Show this message and exit.

Commands:
  list  List queries.
  open  Open queries in the browser.
```

### Command: query list

```
Usage: rtb query list [OPTIONS]

  List queries.

  This command lists all queries from a redash deployment.

Options:
  --id-only   Lists only query identifier and no labels or other meta data.
              This is useful for piping the ids into other commands.

  --raw       Outputs raw JSON response of the API.
  -h, --help  Show this message and exit.
```

### Command: query open

```
Usage: rtb query open [OPTIONS] QUERY_IDS...

  Open queries in the browser.

  With this command, you can open queries from the query catalog in the
  query editor in your browser (e.g. in order to change them). The command
  accepts multiple query IDs.

Options:
  -h, --help  Show this message and exit.
```

## Command group: source

```
Usage: rtb source [OPTIONS] COMMAND [ARGS]...

  List and open data sources.

  Data sources configure data access to an external data provider. They are
  used run queries on them and are identified with a unique integer.

Options:
  -h, --help  Show this message and exit.

Commands:
  list  List data sources.
  open  Open data source in the browser.
```

### Command: source list

```
Usage: rtb source list [OPTIONS]

  List data sources.

  This command lists all data sources from a redash deployment.

Options:
  --id-only   Lists only data source identifier and no labels or other meta
              data. This is useful for piping the ids into other commands.

  --raw       Outputs raw JSON response of the API.
  -h, --help  Show this message and exit.
```

### Command: source open

```
Usage: rtb source open [OPTIONS] SOURCE_IDS...

  Open data source in the browser.

  With this command, you can open data sources from in your browser (e.g. in
  order to change them). The command accepts multiple data source IDs.

Options:
  -h, --help  Show this message and exit.
```

## Command group: user

```
Usage: rtb user [OPTIONS] COMMAND [ARGS]...

  List and open users.

  Users are identified with a unique integer.

Options:
  -h, --help  Show this message and exit.

Commands:
  list  List users.
  open  Open a user profile in the browser.
```

### Command: user list

```
Usage: rtb user list [OPTIONS]

  List users.

  This command lists all users from a redash deployment.

Options:
  --id-only   Lists only data source identifier and no labels or other meta
              data. This is useful for piping the ids into other commands.

  --raw       Outputs raw JSON response of the API.
  -h, --help  Show this message and exit.
```

### Command: user open

```
Usage: rtb user open [OPTIONS] USER_IDS...

  Open a user profile in the browser.

  With this command, you can open a user profile in your browser The command
  accepts multiple user IDs.

Options:
  -h, --help  Show this message and exit.
```

