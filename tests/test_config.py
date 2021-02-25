"""Tests for config commands"""

import os
from nose.tools import (
    eq_,
    with_setup
)
from . import (
    print_start_stop,
    run,
    run_asserting_error,
    run_completion,
    FIXTURE_DIR
)

CURRENT_DIR = os.getcwd()

MULTIPLE_INI = os.path.join(FIXTURE_DIR, "config/multiple.ini")


@print_start_stop
def _setup():
    os.chdir(os.path.join(FIXTURE_DIR, "config"))


@print_start_stop
def _teardown():
    os.chdir(CURRENT_DIR)
    if 'RTB_CONFIG_FILE' in os.environ:
        del os.environ['RTB_CONFIG_FILE']


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_config():
    eq_(
        run("--config-file", MULTIPLE_INI, "config", "list").stdout,
        "example.eccenca.com\nsecond.eccenca.com\nthird.eccenca.com\n"
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_config_from_env():
    os.environ["RTB_CONFIG_FILE"] = MULTIPLE_INI
    eq_(
        run("config", "list").stdout,
        "example.eccenca.com\nsecond.eccenca.com\nthird.eccenca.com\n"
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_config_fail():
    run_asserting_error("-c", "ttt", "query", "list")
    run_asserting_error("--config-file", "not-there", "-c", "query", "list")
    run_asserting_error("--config-file", MULTIPLE_INI, "query", "list")


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_config_completion():
    # set config file - complete connection
    eq_(
        run_completion(["--config-file", MULTIPLE_INI, "-c"], "example"),
        ["example.eccenca.com"]
    )
    eq_(
        run_completion(["--config-file", MULTIPLE_INI, "-c"], "ond"),
        ["second.eccenca.com"]
    )
    # set config file via env - complete connection
    os.environ["RTB_CONFIG_FILE"] = MULTIPLE_INI
    eq_(
        run_completion(["-c"], "ird"),
        ["third.eccenca.com"]
    )
    eq_(
        run_completion(["--config-file"], ""),
        ['multiple.ini', 'online.ini']
    )
