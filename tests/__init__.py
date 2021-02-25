import os
import time
from nose.tools import (
    make_decorator,
    eq_,
    assert_greater_equal
)
from click.testing import CliRunner
from click._bashcomplete import get_choices
from redash_toolbelt.cli import cli


CURRENT_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.join(CURRENT_FILE_PATH, "..")
FIXTURE_DIR = os.path.join(CURRENT_FILE_PATH, "fixtures")

CLI_RUNNER = CliRunner()


def print_start_stop(function):
    """decorator to output visible marks for better log viewing"""
    @make_decorator(function)
    def wrap(*args):
        print(">>>>>>>>>> " + function.__name__ + " started")
        print(">")
        print(">")
        start_time = time.time()
        return_value = function(*args)
        end_time = time.time()
        print(">")
        print(">")
        print(
            ">>>>>>>>>> {:s} finished (took {:.3f} ms)"
            .format(function.__name__, (end_time - start_time) * 1000.0)
        )
        return return_value
    return wrap


def run_completion(args, incomplete):
    """Executes cli and gets completion as flat structure.

    see https://github.com/pallets/click/issues/1453
    """
    print(">>> rtb completion started")
    print(">>> COMPLETION Array: {}  << {}".format(str(args), incomplete))
    print(">>> COMPLETION String: 'rtb {} {}'".format(" ".join(args), incomplete))
    completions = get_choices(cli, 'rtb', args, incomplete)
    print(completions)
    return [c[0] for c in completions]


def _run(*argv):
    """wraps the CliRunner"""
    command = []
    for arg in argv:
        command.append(arg)
    print(">>> rtb started")
    print(">>> RUN Array: {}".format(str(command)))
    print(">>> RUN String: 'rtb {}'".format(" ".join(command)))
    result = CLI_RUNNER.invoke(cli, command)
    # prepare list of lines
    result.lines = result.stdout.splitlines()
    # count the output lines
    result.line_count = len(result.lines)
    print(result.stdout)
    return result


def run(*argv):
    """wraps the CliRunner, asserting exit 0"""
    result = _run(*argv)
    eq_(
        result.exit_code,
        0,
        "exit code should be 0 (but was {})".format(result.exit_code))
    return result


def run_without_assertion(*argv):
    """wraps the CliRunner but does not assert anything"""
    return _run(*argv)


def run_asserting_error(*argv):
    """wraps the CliRunner, asserting exit 1 or more"""
    result = _run(*argv)
    assert_greater_equal(
        result.exit_code,
        1,
        "exit code should be 1 or more (but was {})".format(result.exit_code)
    )
    return result


def assert_line_count(output, expected_count):
    """Asserts that output contains an expected number of lines."""
    if output.line_count != expected_count:
        raise AssertionError(
            "Expected {} lines in {}".format(expected_count, output.stdout)
        )
