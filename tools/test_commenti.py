"""The comment rule of CLAUDE.md, checked by a machine instead of a reviewer."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import commenti  # noqa: E402


def lines(source, path="backend/astrolog/x.py"):
    return [line for line, _ in commenti.problems(source, path)]


def test_two_comment_lines_pass_three_do_not():
    assert lines("# one\n# two\nx = 1\n") == []
    assert lines("# one\n# two\n# three\nx = 1\n") == [1]


def test_directive_comments_do_not_count_toward_a_block():
    source = "# why one\n# why two\n# noqa: E501\n# pyright: ignore\nx = 1\n"
    assert lines(source) == []


def test_a_trailing_comment_is_not_a_block():
    assert lines("x = 1  # a\ny = 2  # b\nz = 3  # c\n") == []


def test_a_long_docstring_is_reported():
    source = 'def f():\n    """One.\n    Two.\n    Three."""\n'
    assert lines(source) == [2]


def test_a_route_docstring_is_the_contract_and_may_be_long():
    source = '@router.get("/x")\ndef f():\n    """One.\n\n    Two.\n    Three."""\n'
    assert lines(source) == []


def test_a_model_docstring_reaches_the_openapi_and_may_be_long():
    source = 'class Out(BaseModel):\n    """One.\n\n    Two.\n    Three."""\n'
    assert lines(source) == []


def test_a_subclass_of_a_model_in_a_models_file_is_contract_too():
    source = 'class Night(WeatherOut):\n    """One.\n\n    Two.\n    Three."""\n'
    assert lines(source, "backend/astrolog/api/models_nights.py") == []
    assert lines(source, "backend/astrolog/spine/nights.py") == [2]


def test_dates_and_names_are_history_not_comments():
    assert lines("# fixed on 2026-10-05\nx = 1\n") == [1]
    assert lines("# asked by Marco\nx = 1\n") == [1]
    assert lines('def f():\n    """Since 3/9/2026."""\n') == [2]


def test_a_date_inside_code_is_not_a_comment():
    assert lines('x = "2026-10-05"\n') == []


def test_the_backend_follows_the_rule_today():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert commenti.check_tree(os.path.join(root, "backend", "astrolog"), root) == []
