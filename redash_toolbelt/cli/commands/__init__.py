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
                "config": COLOR_FOR_COMMAND_GROUPS,
                "dashboard": COLOR_FOR_COMMAND_GROUPS,
                "query": COLOR_FOR_COMMAND_GROUPS,
                "source": COLOR_FOR_COMMAND_GROUPS,
                "user": COLOR_FOR_COMMAND_GROUPS,
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
