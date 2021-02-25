"""The main command line interface."""

import sys
import traceback

import click

from redash_toolbelt.cli import completion
from redash_toolbelt.cli.commands import (
    config,
    query
)
from redash_toolbelt.cli.context import CONTEXT
from redash_toolbelt.cli.exceptions import (
    InvalidConfiguration
)
from redash_toolbelt.cli.utils import is_completing
from redash_toolbelt.cli.commands import CustomGroup

try:
    from redash_toolbelt.cli.version import VERSION
except ImportError:
    VERSION = "SNAPSHOT"

PYTHON_VERSION = "{}.{}.{}".format(
    sys.version_info.major,
    sys.version_info.minor,
    sys.version_info.micro
)
PYTHON_EXPECTED = "3.7"
PYTHON_GOT = "{}.{}".format(
    sys.version_info.major,
    sys.version_info.minor
)
if PYTHON_EXPECTED != PYTHON_GOT:
    # test for environment which indicates that we are in completion mode
    if not is_completing():
        CONTEXT.echo_warning(
            "Warning: Your are running this software under a "
            "non-tested python environment (expected {}, got {})"
            .format(PYTHON_EXPECTED, PYTHON_GOT)
        )

# https://github.com/pallets/click/blob/master/examples/complex/complex/cli.py
CONTEXT_SETTINGS = dict(
    auto_envvar_prefix='RTB',
    help_option_names=['-h', '--help']
)


@click.group(cls=CustomGroup, context_settings=CONTEXT_SETTINGS)
@click.option(
    '-c', '--connection',
    type=click.STRING,
    autocompletion=completion.connections,
    help='Use a specific connection from the config file.'
)
@click.option(
    '--config-file',
    autocompletion=completion.ini_files,
    type=click.Path(
        readable=True,
        allow_dash=False,
        dir_okay=False
    ),
    default=CONTEXT.config_file_default,
    show_default=True,
    help='Use this config file instead of the default one.'
)
@click.option(
    '-q', '--quiet',
    is_flag=True,
    help='Suppress any non-error info messages.'
)
@click.option(
    '-d', '--debug',
    is_flag=True,
    help='Output debug messages and stack traces after errors.'
)
@click.version_option(
    version=VERSION,
    message="%(prog)s, version %(version)s, "
            "running under python {}".format(PYTHON_VERSION)
)
@click.pass_context
def cli(ctx, debug, quiet, config_file, connection):  # noqa: D403
    """rtb - redash toolbelt command line client.

    rtb is a command line client to administrate redash instances.
    """
    ctx.obj = CONTEXT
    ctx.obj.set_quiet(quiet)
    ctx.obj.set_debug(debug)
    ctx.obj.set_config_file(config_file)
    try:
        ctx.obj.set_connection(connection)
    except InvalidConfiguration as error:
        # if config is broken still allow for "config edit"
        # means: do not forward this exception if "config edit"
        if " ".join(sys.argv).find("config edit") == -1:
            raise error


cli.add_command(config.config)
cli.add_command(query.query)


def main():
    """Start the command line interface."""
    try:
        cli()  # pylint: disable=no-value-for-parameter
    except (
            ValueError,
            IOError,
            NotImplementedError,
            KeyError
    ) as error:
        if is_completing():
            # if currently autocompleting -> silently die with exit 1
            sys.exit(1)
        CONTEXT.echo_error(type(error).__name__ + ": " + str(error))
        CONTEXT.echo_debug(traceback.format_exc())
        sys.exit(1)
