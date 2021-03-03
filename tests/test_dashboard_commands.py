"""Tests for dashboard commands"""

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
    assert_is_instance,
)
from . import print_start_stop, run, run_asserting_error, run_completion, FIXTURE_DIR


@print_start_stop
def _setup():
    pass


@print_start_stop
def _teardown():
    pass


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_dashboard_list():
    expected_dashboard_count = 1
    eq_(
        run("dashboard", "list", "--id-only").line_count,
        expected_dashboard_count,
        "there should be one dashboard id here",
    )
    eq_(
        run("dashboard", "list").line_count,
        expected_dashboard_count + 2,
        "there should be one dashboard id and 2 table header rows here",
    )
    assert_in("Demo1", run("dashboard", "list").stdout)
    assert_is_instance(
        json.loads(run("dashboard", "list", "--raw").stdout),
        list,
        "raw output should be a json list",
    )


@with_setup(setup=_setup, teardown=_teardown)
@print_start_stop
def test_dashboard_completion():
    eq_(run_completion(["dashboard", "open"], ""), ["demo1"])
    eq_(run_completion(["dashboard", "open"], "DEM"), ["demo1"])
    eq_(run_completion(["dashboard", "open"], "o1"), ["demo1"])
