"""Tests for query commands"""

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
def test_query_list():
    expected_query_count = 3
    eq_(
        run("query", "list", "--id-only").line_count,
        expected_query_count,
        "there should be 3 query ids here"
    )
    eq_(
        run("query", "list").line_count,
        expected_query_count + 2,
        "there should be 3 query ids and 2 table header rows here"
    )
    assert_in(
        "Products",
        run("query", "list").stdout
    )
    assert_in(
        "Value",
        run("query", "list").stdout
    )
    assert_is_instance(
        json.loads(run("query", "list", "--raw").stdout),
        list,
        "raw output should be a json list"
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_query_completion():
    eq_(
        run_completion(["query", "open"], ""),
        ["3", "1", "2"]
    )
    eq_(
        run_completion(["query", "open"], "val"),
        ["1"]
    )
    eq_(
        run_completion(["query", "open"], "cts"),
        ["3", "2"]
    )
    eq_(
        run_completion(["query", "open"], "category"),
        ["2"]
    )
