"""Main script of a program that will run this as a service"""
import os
import threading
from dotenv import load_dotenv
from modules import bot_get_posts, bot_send_posts


def main_program():
    """Bot itself"""
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
    app_handle = os.getenv('APP_HANDLE')
    app_password = os.getenv('APP_PASSWORD')
    database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database/database.db')
    media_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
    send_post = threading.Thread(target=bot_send_posts.send_main, args=(app_handle, app_password, database_path, media_path))
    get_post = threading.Thread(target=bot_get_posts.get_notifications, args=(app_handle, app_password, database_path, media_path))
    send_post.start()
    get_post.start()


if __name__ == '__main__':
    main_program()
