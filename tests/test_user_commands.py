"""Tests for user commands"""

import os
import json
from nose.tools import (
    eq_,
    assert_in,
    assert_not_in,
    assert_greater,
    assert_not_equal,
    assert_greater_equal,
    assert_less,
    with_setup,
    nottest,
    assert_is_instance
)
from . import (
    print_start_stop,
    run,
    run_asserting_error,
    run_completion,
    FIXTURE_DIR
)


@print_start_stop
def _setup():
    pass


@print_start_stop
def _teardown():
    pass


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_user_list():
    expected_user_count = 1
    eq_(
        run("user", "list", "--id-only").line_count,
        expected_user_count,
        "there should be one user id here"
    )
    eq_(
        run("user", "list").line_count,
        expected_user_count + 2,
        "there should be one user id and 2 table header rows here"
    )
    assert_in(
        "admin@example.org",
        run("user", "list").stdout
    )
    assert_is_instance(
        json.loads(run("user", "list", "--raw").stdout),
        list,
        "raw output should be a json list"
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_user_completion():
    eq_(
        run_completion(["user", "open"], ""),
        ["1"]
    )
    eq_(
        run_completion(["user", "open"], "ad"),
        ["1"]
    )
    eq_(
        run_completion(["user", "open"], "min"),
        ["1"]
    )
