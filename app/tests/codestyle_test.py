"""Tests for modules codestyle."""
import inspect
import statistics
import main
import modules
from pylint.lint import Run
from pylint.reporters import CollectingReporter


def codestyle_module(src_file) -> int:
    """Returns codestyle score of a module within a given location.

    :param src_file: Source file.
    :return codestyle_score
    """
    rep = CollectingReporter()
    r = Run(['--disable=C0301,C0103', '-sn', src_file], reporter=rep, exit=False)
    score = r.linter.stats.global_note
    return score


def test_codestyle():
    """Tests all modules"""
    assert codestyle_module(inspect.getfile(main)) == 10
    assert codestyle_module(inspect.getfile(statistics)) == 10
    assert codestyle_module(inspect.getfile(modules.bot_send_posts)) == 10
    assert codestyle_module(inspect.getfile(modules.classes)) == 10
    assert codestyle_module(inspect.getfile(modules.database_control)) == 10
