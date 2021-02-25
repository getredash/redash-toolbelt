"""Utility functions for CLI interface."""

import os


def is_completing():
    """Test for environment which indicates that we are in completion mode.

    Returns true if in completion mode, otherwise false.

    Returns: boolean
    """
    comp_words = os.getenv("COMP_WORDS", default=None)
    is_complete = os.getenv("_RTB_COMPLETE", default=None)
    if comp_words is not None:
        return True
    if is_complete is not None:
        return True
    return False
