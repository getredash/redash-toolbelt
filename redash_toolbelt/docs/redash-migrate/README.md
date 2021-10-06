redash-migrate - Move data from one instance of Redash to another


- [INSTALLATION](#installation)
- [DESCRIPTION](#description)
- [METAFILE](#meta.json)
  - [SETTINGS](#settings)
- [COMMANDS](#commands)
  - [RUNNING COMMANDS](#running-commands)
- [FAQ](#faq)
- [DEVELOPER INSTRUCTIONS]
- [BUGS]
- [COPYRIGHT](#copyright)

## INSTALLATION

To install it you will need Python 3.6 or above. We recommend that you use a [virtual environment](https://pythonbasics.org/virtualenv/). The `redash-migrate` command is part of our Python API wrapper, called `redash-toolbelt`.

```bash
pip install --upgrade redash-toolbelt
```

This command will update `redash-toolbelt` if you have already installed it. See the [PyPi page](https://pypi.org/project/redash-toolbelt/) for more information. The `redash-migrate` command will now be available.

```bash
redash-migrate --version
```

This command will verify your installation.

## DESCRIPTION

**redash-migrate** is a command-line program to move data from one Redash instance to another . It requires the Python interpreter, version 3.6+, and it is not platform specific. It should work on your Unix box, on Windows or on macOS. It is released to the public domain, which means you can modify it, redistribute it or use it however you like.

```bash
redash-migrate [COMMAND]
```
## METAFILE

`redash-migrate` uses a file called `meta.json` to track its state between command executions. And it updates `meta.json` after each command executes. 

```bash
redash-migrate init
```

This command creates a `meta.json` file in your working directory. Before you run further commands, you must fill-in the `settings` object:

```json
"settings": {
    "origin_url": "",
    "origin_admin_api_key": "",
    "destination_url": "",
    "destination_admin_api_key": "",
    "preserve_invite_links": true
}
```

**⚠️&nbsp;&nbsp;Warning**:  Do not share your `meta.json` file with anyone. It contains administrator API keys for your Redash instance. This information is private. If you do share it, reset the admin API keys for your Redash instances immediately.


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

## COMMANDS
You can run `redash-migrate --help` to see the available commands. 

```text
init                  Create a meta.json template file in your working directory. You must 
                      populate the `settings` object within meta.json before proceeding.
data_sources          Create stubs of your origin data sources in your destination instance
check_data_sources    Compare the data sources in your origin and destination instances
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
disable_users         Disable users in the destination instance that are disabled in the
                      origin instance.
```

### RUNNING COMMANDS

Commands are always listed in the correct order. For example, you must import users before you import groups. You must import alert destinations before you import alerts.

With exception of `init` and `check_data_sources`, each command will insert new data into your destination instance. _The origin instance is never modified_. The script only emits GET requests to the origin instance. It emits both GET and POST requests to the destination instance.

![Diagram that shows redash-migrate making GET requests to the origin instance and POST requests to the destination instance](redash-migrate-data-flow.png)

Commands are idempotent. The same query, dashboard, visualization etc. will not be imported twice. If you run `redash-migrate queries` repeatedly, the command will only attempt to import queries that were not successfully migrated during a previous execution.

## FAQ

### Is there a video that shows how to run redash-migrate

Not yet. But we're making one. It will be linked here as soon as it's ready.

### I found a different script online, why should I use redash-migrate instead?

redash-migrate is the officially supported migration tool. We wrote it because the previous migration script did not  work reliably with newer versions of Redash (since V7). But you can use any tool you want. Or fork this one and modify it for your needs.

## COPYRIGHT
redash-migrate is released into the public domain by the copyright holders.

This README file was originally written by Jesse Whitehouse and is likewise released to the public domain. This README file is based on the work of Daniel Bolton for youtube-dl with deep gratitude for that effort.