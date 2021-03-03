"""Tests for group commands"""

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
def test_group_list():
    expected_group_count = 2
    eq_(
        run("group", "list", "--id-only").line_count,
        expected_group_count,
        "there should be 2 group ids here"
    )
    eq_(
        run("group", "list").line_count,
        expected_group_count + 2,
        "there should be 2 group ids and 2 table header rows here"
    )
    assert_in(
        "admin",
        run("group", "list").stdout
    )
    assert_in(
        "default",
        run("group", "list").stdout
    )
    assert_is_instance(
        json.loads(run("group", "list", "--raw").stdout),
        list,
        "raw output should be a json list"
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_group_completion():
    eq_(
        run_completion(["group", "open"], ""),
        ["1", "2"]
    )
    eq_(
        run_completion(["group", "open"], "de"),
        ["2"]
    )
    eq_(
        run_completion(["group", "open"], "min"),
        ["1"]
    )
