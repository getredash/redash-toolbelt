"""Configuration commands."""
import click

from redash_toolbelt.cli.commands import CustomCommand, CustomGroup


@click.command(cls=CustomCommand, name="list")
@click.pass_obj
def list_command(app):
    """List configured connections.

    This command lists all configured redash
    connections from the currently used config file.

    The connection identifier can be used with the --connection option
    in order to use a specific redash instance.
    """
    for section_string in sorted(app.config, key=str.casefold):
        if section_string != "DEFAULT":
            app.echo_result(section_string)


@click.command(cls=CustomCommand, name="edit")
@click.pass_obj
def edit_command(app):
    """Edit the user-scope configuration file."""
    app.echo_info("Open editor for config file " + app.config_file)
    click.edit(filename=app.config_file)


@click.group(cls=CustomGroup)
def config():
    u"""List and edit configurations.

    Configurations are identified by the section identifier in the
    config file. Each configuration represent a Redash deployment.

    A minimal configuration has the following entries:

    \b
    [example.org]
    REDASH_BASE_URL=https://redash.example.org/
    REDASH_API_TOKEN=token
    """


config.add_command(list_command)
config.add_command(edit_command)
