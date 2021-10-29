redash-migrate - Move data from one instance of Redash to another


- [INSTALLATION](#installation)
- [DESCRIPTION](#description)
- [METAFILE](#meta.json)
  - [SETTINGS](#settings)
  - [READING THE METAFILE](#reading-the-metafile)
  - [FIRST USER](#first-user)
  - [DATA SOURCES](#data-sources)
- [COMMANDS](#commands)
  - [RUNNING COMMANDS](#running-commands)
- [FAQ](#faq)
- [DEVELOPING THIS SCRIPT](#developing-this-script)
- [BUGS](#bugs)
- [COPYRIGHT](#copyright)

## INSTALLATION

To install it you will need Python 3.6 or above. We recommend that you use a [virtual environment].
The `redash-migrate` command is part of our Python API wrapper, called `redash-toolbelt`.

[virtual environment]: https://pythonbasics.org/virtualenv/

```bash
pip install --upgrade redash-toolbelt
```

This command will update `redash-toolbelt` if you have already installed it. See the [PyPi page] for
more information. The `redash-migrate` command will now be available.

[PyPi page]: https://pypi.org/project/redash-toolbelt/

```bash
redash-migrate --version
```

This command will verify your installation.

## DESCRIPTION

**redash-migrate** is a command-line program to move data from one instance of Redash V10 instance
to another . It requires the Python interpreter, version 3.6+, and it is not platform specific. It
should work on your Unix box, on Windows or on macOS. It is released to the public domain, which
means you can modify it, redistribute it or use it however you like.

```bash
redash-migrate [COMMAND]
```
## METAFILE

redash-migrate uses a file called `meta.json` to track its state between command executions. And
it updates `meta.json` after each command executes.  

```bash
redash-migrate init
```

Run this command before you begin the  migration process. It will create the `meta.json` file in
your working directory and then prompt you to answer several questions about how to authenticate
against your origin and destination instances. Once finished, you can check the settings the
`meta.json` file to ensure the correct information is provided. Basic settings are covered below:


**⚠️&nbsp;&nbsp;Warning**:  Do not share your `meta.json` file with anyone. It contains
administrator API keys for your Redash instance. This information is private. If you do share it,
reset the admin API keys for your Redash instances immediately.

### SETTINGS
```text
origin_url              The base URL for your origin Redash instance. For example:
                        https://app.redash.io/acme
origin_admin_api_key    The api key for an admin user on your origin instance.
destination_url         The base URL for your destination Redash instance. For example:
                        http://localhost
preserve_invite_links   Whether or not to write user invitation links into meta.json. If false,
                        users logging-in to the destination instance for the first time will need
                        to click the "I forgot my password" link to receive an email. If true,
                        invite links will be written to meta.json. These links can be used to set a
                        new password directly without using the forgotten password workflow. The
                        default value is true.
```
### READING THE METAFILE

If you examine `meta.json` you will see it contains mappings for different object types: `users`,
`queries`, `visualizations`, `dashboards`, `alerts`, `flags`, `data_sources`, `groups`,  and
`destinations`. In each of these mappings, the key comes from the origin and the value comes from
the destination.

```json
// example meta.json
"queries": {
    "108171": 6,
    "219541": 7,
    "381761": 8
},
```

This indicates that origin query 10817 copied to the destination as query 6.

### FIRST USER

redash-migrate assumes your destination is a fresh instance of Redash. But the destination cannot
be entirely blank because you need at least one admin user to already exist at the destination. As
part of the `init` command, you will be asked to provide the user id for your admin user at both the
origin and the destination instance.

Additionally, if you created any users in the destination instance before using redash-migrate,
you must manually add them to `meta.json` so that it can associate their id at the
origin instance with their id at the destination. 

If you don't do this, you will potentially create a duplicate user at the destination.

### DATA SOURCES

When you run the `data-sources` command, redash-migrate creates "stub" data sources at your
destination instance. Stub data sources mirror the name, type, any other non-secret fields
from your origin. But the secret fields _will be blank on the destination instance_. This
includes passwords, key files, and auth tokens. In all likelihood, you will not be able to
run queries on your destination instance until you fill in any missing secret fields with
the UI.

This step is necessary because redash-migrate uses the Redash REST API which never sends
secret data source fields in plain text. It's a security measure to prevent exfiltration
of your organisation's database credentials should a hostile party obtain an admin API key.

## COMMANDS
You can run `redash-migrate --help` to see the available commands. 

```text
init                  Create a meta.json template file in your working directory. You will be
                      prompted to enter authentication information for your origin and desti-
                      nation instances.
data-sources          Create stubs of your origin data sources in your destination instance
check-data-sources    Compare the data sources in your origin and destination instances
users                 Duplicate user names, emails, and enabled/disabled status from the
                      origin instance into the destination instance.
groups                Duplicate group names, member lists, and data source permissions from
                      the origin instance into the destination instance.
queries               Duplicate queries from the origin instance to the destination instance.
                      Skips queries with an unknown destination data source or user.
visualizations        Duplicate visualizations from the origin instance to the destination
                      instance. Only duplicates visualizations for queries moved by the
                      `queries` command.
dashboards            Duplicate dashboards from the origin instance to the destination
                      instance. Skips any dashboard widget whose visualization was not moved
                      using the `visualizations` command.
destinations          Create stubs of your origin alert destinations in your destination
                      instance
alerts                Duplicate alert definitions from the origin instance to the destination
                      instance. Skips alerts that point to queries that were not migrated by
                      the `queries` command. Run the `destinations` command first.
favorites             Duplicate favorite flags on queries and dashboards from the origin
                      instance to the destination instance.
disable-users         Disable users in the destination instance that are disabled in the
                      origin instance.
fix-qrds-refs         Replace references to origin query id's in query results data source
                      (QRDS) queries with their new id at the destination. Does nothing if
                      the destination has no QRDS sources.
fix-csv-queries       Reformat queries against app.redash.io's csvurl data source so they are
                      compatible with OSS Redash's csv data source. Do not use this command if
                      you did not migrate from app.redash.io.

```
## RUNNING COMMANDS

The order you run commands is important. For example, you must import users before groups,
destinations before alerts, and queries before visualizations. For best results, use the order that
commands are shown in the output of the `--help` option.

With exception of `init` and `check-data-sources`, each command modifies the destination instance.
_The origin instance is never modified_. The script only emits GET requests to the origin instance.
It only emits POST requests to the destination instance.


```text
┌───────────────────┐                                                          ┌───────────────────┐
│                   │                                                          │                   │
│                   │                                                          │                   │
│   Origin Redash   │                   .─────────────────.                    │Destination Redash │
│     Instance      │◀───────GET───────(  redash-migrate   )───────POST───────▶│     Instance      │
│                   │                   `─────────────────'                    │                   │
│                   │                                                          │                   │
└───────────────────┘                                                          └───────────────────┘
````

Commands are idempotent. The same query, dashboard, visualization etc. will not be imported twice.
If you run `redash-migrate queries` repeatedly, the command will only attempt to import queries that
were not successfully migrated during a previous execution.

**Note**: due to the volume of network requests it creates, redash-migrate may trip the rate limit
on your destination Redash instance. We recommend you disable rate limiting at the destination 
for the duration of your migration. On Redash V10 this can be disabled by setting an environment
variable named `REDASH_RATELIMIT_ENABLED=false`.

## FAQ

### Who should use redash-migrate?

Customers of Hosted Redash moving their accounts to Open Source (OSS) Redash. Also, anyone needing
to move from one instance to another who does not have access to the origin and destination
databases (this is rare).
### Who _shouldn't_ use redash-migrate?

Don't use redash-migrate to move between major versions of Redash.  Because redash-migrate uses the
REST API to duplicate objects, it depends on the origin and destination instances using the exact
same API. If you need to move from Redash V8 -> V10, for example, you should upgrade your V8
instance to V10 and then use redash-migrate to move your data.

You don't need to use redash-migrate if you have access to the origin and destination databases. In
these cases you can simply dump the origin database and copy it to the destination server.

### Is there a video that shows how to run redash-migrate

Not yet. But we're making one. It will be linked here as soon as it's ready.

### I found a different script online, why should I use redash-migrate instead?

redash-migrate is the officially supported migration tool. We wrote it because the previous
migration script did not  work reliably with newer versions of Redash (since V7). But you can use
any tool you want. Or fork this one and modify it for your needs.

### Can I use redash-migrate on Redash versions older than V10?

We test redash-migrate on Redash V10 and newer. It will probably work on V9 but no earlier.

### Can I use redash-migrate to move between versions?

No. See [who _shouldn't_ use redash-migrate](#who-shouldnt-use-redash-migrate) above.


## DEVELOPING THIS SCRIPT

To develop modifications to this script you should do the following:

```shell
# Clone redash-toolbelt to your disk
git clone https://github.com/getredash/redash-toolbelt.git

# Create a Python virtual environment using version 3.6+
python3 -m virtualenv ${env_name}

# Activate your virtual environment
. ${env_name}/bin/activate # macOS
${env_name}\scripts\activate # Windows

# We use Poetry to build redash-toolbelt for distribution on PyPi
pip install poetry

# Make your changes to the script. When it's time to test your changes.

# Build the package with Poetry. This will create a .tar.gz file in the /dist directory
poetry build

# Use to pip to install the .tar.gz archive created in the previous step
pip install dist/redash_toolbelt-x.x.x.tar.gz

# If everything works, please open a PR.
```

## BUGS

If you encounter issues with this script, please open an issue on our Github: 

https://github.com/getredash/redash-toolbelt
## COPYRIGHT
redash-migrate is released into the public domain by the copyright holders.

This README file was originally written by Jesse Whitehouse and is likewise released to the public
domain. This README file is based on the work of Daniel Bolton for youtube-dl with deep gratitude
for that effort.
