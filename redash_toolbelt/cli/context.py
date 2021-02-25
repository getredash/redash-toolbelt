"""The main command line interface."""
import configparser
from datetime import datetime
import json
from os import getenv
from os import makedirs, path

import click

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name

from tabulate import tabulate

from redash_toolbelt import Redash

from redash_toolbelt.cli.exceptions import InvalidConfiguration
from redash_toolbelt.cli.utils import is_completing

KNOWN_CONFIG_KEYS = ("REDASH_BASE_URL", "REDASH_API_TOKEN")

KNOWN_SECRET_KEYS = "REDASH_API_TOKEN"


class ApplicationContext:
    """Context of the command line interface."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, debug=False, quiet=False):
        """Initialize main context."""
        self.app_name = "rtb"
        self.debug = self.set_debug(debug)
        self.quiet = self.set_quiet(quiet)
        self.config_dir = click.get_app_dir(self.app_name)
        if not path.exists(self.config_dir):
            makedirs(self.config_dir)
        self.config_file_default = path.join(self.config_dir, "config.ini")
        self.config_file = None
        self.config = None
        self.connection_string = None
        self.connection = None
        self.__foo = None

    def set_debug(self, debug=False):
        """Set debug state."""
        self.debug = debug
        return self.debug

    def set_quiet(self, quiet=False):
        """Set quiets state."""
        self.quiet = quiet
        return self.quiet

    def set_config_file(self, config_file):
        """Set and return the context config file."""
        if config_file is None:
            config_file = self.config_file_default
            if getenv("RDT_CONFIG_FILE") is not None:
                config_file = getenv("RDT_CONFIG_FILE")
        self.echo_debug("Set config to " + config_file)
        self.config_file = config_file
        return self.config_file

    def set_connection_string(self, connection_string):
        """Set and return the connection string."""
        self.echo_debug("Set connection string to " + str(connection_string))
        self.connection_string = connection_string
        return self.connection_string

    def set_connection_from_args(self, args):
        """Set connection and config by manually checking args (completion)."""
        # look for environment and load config
        self.set_config_file(getenv("RTB_CONFIG_FILE", self.config_file))
        # look for config file in arguments and load config
        found_config_file = False
        for arg in args:
            if found_config_file is True:
                self.set_config_file(arg)
                break
            if arg == "--config-file":
                found_config_file = True
        self.config = self.get_config()
        # look for connection in environment and set connection string
        self.set_connection_string(getenv("RTB_CONNECTION", ""))
        # look for connection in arguments and set connection
        found_connection = False
        for arg in args:
            if found_connection is True:
                self.set_connection_string(arg)
                return
            if arg in ("-c", "--connection"):
                found_connection = True
        return

    def set_connection(self, section_string):
        """Set connection config section based on section string."""
        self.config = self.get_config()
        available_connections = self.config.sections()
        self.connection = None
        if section_string is None or section_string == "":
            self.echo_debug("No connection string given, try to take the first one.")
            if len(available_connections) == 0:
                raise InvalidConfiguration(
                    "There is no connection configured in config file {}. "
                    "Please add one with the config edit command.".format(
                        self.config_file
                    )
                )
            if len(available_connections) == 1:
                section_string = available_connections[0]
            else:
                section_string = available_connections[0]
                self.echo_warning(
                    "No explicit connection given - "
                    "will use the first one: {}".format(section_string)
                )
        if section_string not in self.config:
            raise InvalidConfiguration(
                "There is no connection '{}' configured in config '{}'.".format(
                    section_string, self.config_file
                )
            )
        self.echo_debug("Use connection config: " + section_string)
        self.connection = self.config[section_string]
        self.configure_api(self.connection)
        return self.connection

    def configure_api(self, connection):
        """Initialize the redash toolbelt API."""
        api = Redash(
            redash_url=connection["REDASH_BASE_URL"],
            api_key=connection["REDASH_API_TOKEN"],
        )
        if api.test_credentials():
            self.echo_debug("Credentials successfully tested.")
        else:
            raise InvalidConfiguration("Credentials not successfully tested.")
        self.__foo = api

    def get_api(self) -> Redash:
        """Return initialized Redash API object."""
        self.set_connection(self.connection_string)
        self.configure_api(self.connection)
        return self.__foo

    def get_config_file(self):
        """Check the connection config file."""
        if not path.exists(self.config_file):
            self.echo_warning("Empty config created: {}".format(self.config_file))
            open(self.config_file, "a").close()
        self.echo_debug("Config loaded: " + self.config_file)
        return self.config_file

    def set_config(self):
        """Setup config object based on current configuration."""
        self.config = self.get_config()

    def get_config(self):
        """Parse the app connections config."""
        try:
            config = configparser.RawConfigParser()
            config_file = self.get_config_file()
            # https://stackoverflow.com/questions/1648517/
            config.read(config_file, encoding="utf-8")
        except configparser.Error as error:
            raise InvalidConfiguration(
                "The following config parser error needs to be fixed with "
                "your config file:\n{}\nYou can use the 'config edit' command "
                "to fix this.".format(str(error))
            ) from error
        return config

    @staticmethod
    def echo_warning(message, nl=True):
        """Output a warning message."""
        # pylint: disable=invalid-name
        if is_completing():
            return
        click.secho(message, fg="yellow", err=True, nl=nl)

    @staticmethod
    def echo_error(message, nl=True, err=True):
        """Output an error message."""
        # pylint: disable=invalid-name
        click.secho(message, fg="red", err=err, nl=nl)

    def echo_debug(self, message):
        """Output a debug message if --debug is enabled."""
        # pylint: disable=invalid-name
        if self.debug:
            click.secho(
                "[{}] {}".format(str(datetime.now()), message), err=True, dim=True
            )

    def echo_info(self, message, nl=True, fg=""):
        """Output an info message, if not suppressed by --quiet."""
        # pylint: disable=invalid-name
        if not self.quiet:
            click.secho(message, nl=nl, fg=fg)

    def echo_info_json(self, object_):
        """Output a formatted and highlighted json as info message."""
        # pylint: disable=invalid-name
        message = highlight(
            json.dumps(object_, indent=2),
            get_lexer_by_name("json"),
            get_formatter_by_name("terminal"),
        )
        self.echo_info(message)

    def echo_info_table(self, table, headers):
        """Output a formatted and highlighted table as info message."""
        # generate the un-colored table output
        lines = tabulate(table, headers).splitlines()
        # First two lines are header, output colored
        header = "\n".join(lines[:2])
        self.echo_info(header, fg="yellow")
        # after the second line, the body starts
        row_count = len(lines[2:])
        if row_count > 0:
            body = "\n".join(lines[2:])
            self.echo_info(body)

    def echo_success(self, message, nl=True):
        """Output success message, if not suppressed by --quiet."""
        # pylint: disable=invalid-name
        self.echo_info(message, fg="green", nl=nl)

    @staticmethod
    def echo_result(message, nl=True):
        """Output result message, can NOT be suppressed by --quiet."""
        # pylint: disable=invalid-name
        click.echo(message, nl=nl)


CONTEXT = ApplicationContext()
