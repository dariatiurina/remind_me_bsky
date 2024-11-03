"""Tests for get_posts"""
import modules.bot_get_posts as bot


def test_get_every_from_post():
    """Tests getting how often post must be reminded"""
    test = 'every 20 minutes'
    assert bot.get_every_from_post(test) == 1200
    test = 'every 2 minutes'
    assert bot.get_every_from_post(test) == 120
    assert bot.get_every_from_post(test) != 1200


def test_get_period():
    """Tests getting period from text"""
    test = 'remind me this In 23 days'
    assert bot.get_period(test, 'in') == '23 days'
    assert bot.get_period(test, 'IN') == '23 days'
    assert bot.get_period(test, 'every') == ''


def test_count_remind():
    """Tests counting time when will be reminded"""
    test_date = '2024-05-22 15:30:00'
    assert bot.count_remind('1 hour', test_date) == '2024-05-22 16:30:00'
    assert bot.count_remind('1 hours', test_date) == '2024-05-22 16:30:00'
    assert bot.count_remind('1 month', test_date) == '2024-06-22 15:30:00'
    assert bot.count_remind('1 years', test_date) == '2025-05-22 15:30:00'


def test_get_time_to_remind_from_post():
    """Tests getting time to remind post"""
    test_date = '2024-05-22T15:30:00.107Z'
    assert bot.get_time_to_remind_from_post('in 1 hour', test_date) == '2024-05-22 16:30:00'
    assert bot.get_time_to_remind_from_post('in 1 days', test_date) == '2024-05-23 15:30:00'
    assert bot.get_time_to_remind_from_post('in 1 year', test_date) == '2025-05-22 15:30:00'
