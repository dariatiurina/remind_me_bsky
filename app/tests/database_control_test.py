"""Tests for database_control.py"""
import os
from modules.database_control import Database, convert_date
from modules.classes import Post, Media


def create_test_post() -> Post:
    """Creates a test post"""
    test_post = Post()
    test_post.set_author_post('test_handle_1')
    test_post.set_author_remind('test_handle_2')
    test_post.set_every_n_seconds('60')
    test_post.set_text('test post that should be okay')
    test_post.set_time_to_remind('2023-12-01 15:34:12')
    test_post.set_time_send_request('2022-05-19T13:28:41.107Z')
    test_post.set_people_remind(['test_handle_3', 'test_handle_4', 'test_handle_5'])
    return test_post


def test_convert_date():
    """Test of convert_date function"""
    assert convert_date('2024-05-19T13:28:41.107Z') == '2024-05-19 13:28:41'
    assert convert_date('2024-05-19T13:27:25.756Z') != '2024-05-19 13:28:41'


def test_insert_person():
    """Test of inserting people"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    database = Database('test.db')
    database.insert_person('test_handle_1')
    database.insert_person('test_handle_2')
    assert database.find_person('test_handle_1') == 1
    assert database.find_person('test_handle_2') == 2
    assert database.find_person('test_handle_3') == -1
    database.stop()
    os.remove('test.db')


def test_find_or_insert_person():
    """Test of looking up people in database even in case if they are not there"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    database = Database('test.db')
    assert database.find_person_or_insert('test_handle_1') == 1
    assert database.find_person_or_insert('test_handle_2') == 2
    assert database.find_person('test_handle_2') == 2
    assert database.find_person('test_handle_3') == -1
    database.stop()
    os.remove('test.db')


def test_insert_post():
    """Test of inserting posts"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    test_post = create_test_post()
    database = Database('test.db')
    assert database.insert_post(test_post) == 1
    database.stop()
    os.remove('test.db')


def test_delete_post_by_id():
    """Test of deleting post by id"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    test_post = create_test_post()
    database = Database('test.db')
    database.insert_post(test_post)
    database.delete_post_by_id(1, '')
    database.get_posts_by_time_to_remind(test_post.time_to_remind)
    database.stop()
    os.remove('test.db')


def test_delete_post():
    """Test of deleting post using Post class"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    test_post = create_test_post()
    database = Database('test.db')
    database.insert_post(test_post)
    database.delete_post(test_post, "")
    assert len(database.get_posts_by_time_to_remind(test_post.time_to_remind)) == 0
    database.stop()
    os.remove('test.db')


def test_get_media_by_post():
    """Test getting media using post they are in"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    test_post = create_test_post()
    test_media = Media()
    database = Database('test.db')
    test_media.set_post_id(database.insert_post(test_post))
    test_media.set_title('something')
    database.insert_media(test_media)
    assert database.get_media_by_post_id(1)[0].TITLE == 'something'
    database.stop()
    os.remove('test.db')


def test_update_time_remind():
    """Test of updating remind time"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    test_post = create_test_post()
    database = Database('test.db')
    database.insert_post(test_post)
    database.update_post_time_remind(database.get_posts_by_time_to_remind(test_post.time_to_remind)[0])
    assert len(database.get_posts_by_time_to_remind(test_post.time_to_remind)) == 0
    assert len(database.get_posts_by_time_to_remind('2023-12-01 15:35')) == 1
    database.stop()
    os.remove('test.db')


def test_insert_facets():
    """Test of inserting facets into database"""
    if os.path.exists('test.db'):
        os.remove('test.db')
    test_post = create_test_post()
    database = Database('test.db')
    post_id = database.insert_post(test_post)
    database.insert_facets(index=[0, 10], facet_type='link', uri='https://example.com', post_id=post_id)
    assert database.get_facets_by_post_id(post_id)[0].URI == 'https://example.com'
    database.stop()
    os.remove('test.db')
