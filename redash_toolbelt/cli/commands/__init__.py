"""commands."""

from click_help_colors import HelpColorsCommand, HelpColorsGroup

from click_didyoumean import DYMGroup

COLOR_FOR_COMMAND_GROUPS = "white"
COLOR_FOR_WRITING_COMMANDS = "red"
COLOR_FOR_HEADERS = "yellow"
COLOR_FOR_OPTIONS = "green"


# pylint: disable=too-many-ancestors
class CustomGroup(HelpColorsGroup, DYMGroup):
    """Wrapper click.Group class to have a single extension point.

    Currently wrapped click extensions and additional group features:#
    - click-help-colors: https://github.com/click-contrib/click-help-colors
    """

    def __init__(self, *args, **kwargs):
        """Init a custom click command group."""
        # set default colors
        kwargs.setdefault("help_headers_color", COLOR_FOR_HEADERS)
        kwargs.setdefault("help_options_color", COLOR_FOR_OPTIONS)
        kwargs.setdefault(
            "help_options_custom_colors",
            {
                "bootstrap": COLOR_FOR_WRITING_COMMANDS,
                "showcase": COLOR_FOR_WRITING_COMMANDS,
                "delete": COLOR_FOR_WRITING_COMMANDS,
                "upload": COLOR_FOR_WRITING_COMMANDS,
                "import": COLOR_FOR_WRITING_COMMANDS,
                "create": COLOR_FOR_WRITING_COMMANDS,
                "execute": COLOR_FOR_WRITING_COMMANDS,
                "io": COLOR_FOR_WRITING_COMMANDS,
                "install": COLOR_FOR_WRITING_COMMANDS,
                "uninstall": COLOR_FOR_WRITING_COMMANDS,
                "reload": COLOR_FOR_WRITING_COMMANDS,
                "update": COLOR_FOR_WRITING_COMMANDS,
                "admin": COLOR_FOR_COMMAND_GROUPS,
                "config": COLOR_FOR_COMMAND_GROUPS,
                "dataset": COLOR_FOR_COMMAND_GROUPS,
                "graph": COLOR_FOR_COMMAND_GROUPS,
                "project": COLOR_FOR_COMMAND_GROUPS,
                "query": COLOR_FOR_COMMAND_GROUPS,
                "vocabulary": COLOR_FOR_COMMAND_GROUPS,
                "workflow": COLOR_FOR_COMMAND_GROUPS,
                "workspace": COLOR_FOR_COMMAND_GROUPS,
                "cache": COLOR_FOR_COMMAND_GROUPS,
            }
        )
        super().__init__(*args, **kwargs)


class CustomCommand(HelpColorsCommand):
    """Wrapper click.Command class to have a single extension point.

    Currently wrapped click extensions and additional group features:#
    - click-help-colors: https://github.com/click-contrib/click-help-colors
    """

    def __init__(self, *args, **kwargs):
        """Init a custom click command.."""
        kwargs.setdefault('help_headers_color', COLOR_FOR_HEADERS)
        kwargs.setdefault('help_options_color', COLOR_FOR_OPTIONS)
        super().__init__(*args, **kwargs)
