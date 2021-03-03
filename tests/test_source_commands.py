"""Tests for source commands"""

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
def test_source_list():
    expected_source_count = 2
    eq_(
        run("source", "list", "--id-only").line_count,
        expected_source_count,
        "there should be 2 source ids here"
    )
    eq_(
        run("source", "list").line_count,
        expected_source_count + 2,
        "there should be 2 source ids and 2 table header rows here"
    )
    assert_in(
        "postgres-northwind-1",
        run("source", "list").stdout
    )
    assert_in(
        "pg",
        run("source", "list").stdout
    )
    assert_is_instance(
        json.loads(run("source", "list", "--raw").stdout),
        list,
        "raw output should be a json list"
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_query_completion():
    eq_(
        run_completion(["source", "open"], ""),
        ["1", "2"]
    )
    eq_(
        run_completion(["source", "open"], "north"),
        ["1", "2"]
    )
    eq_(
        run_completion(["source", "open"], "d-2"),
        ["2"]
    )
