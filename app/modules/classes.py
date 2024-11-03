"""Classes to work with database"""
import datetime


class Post:
    """Class representing a post"""

    def __init__(self):
        self.text = ""
        self.author_remind = ""
        self.time_send_request = ""
        self.author_post = ""
        self.time_to_remind = ""
        self.people_remind = ""
        self.every_n_seconds = ""

    def set_time_to_remind(self, time_to_remind: str):
        """
        Sets the time to remind

        :param time_to_remind: time to remind
        :return:
        """
        self.time_to_remind = datetime.datetime.strptime(time_to_remind, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M")

    def set_author_remind(self, author_remind: str):
        """
        Sets the author remind

        :param author_remind: handle of an author of a reminder
        :return:
        """
        self.author_remind = author_remind

    def set_author_post(self, author_post):
        """
        Sets the author post

        :param author_post: handle of an author of an original post
        :return:
        """
        self.author_post = author_post

    def set_time_send_request(self, time_send_request):
        """
        Set the time a request was sent

        :param time_send_request: time a request was sent
        :return:
        """
        self.time_send_request = time_send_request

    def set_people_remind(self, people_remind: list[str]):
        """
        Set a person remind attribute

        :param people_remind: list of handles of people who will be reminded
        :return:
        """
        self.people_remind = people_remind

    def set_every_n_seconds(self, every_n_seconds):
        """
        Set the every n seconds

        :param every_n_seconds: how often will post be reminded
        :return:
        """
        self.every_n_seconds = every_n_seconds

    def set_text(self, text):
        """
        Set a post text

        :param text: text of a post
        :return:
        """
        self.text = text


class Media:
    """Class representing a media"""

    def __init__(self):
        self.alt = ""
        self.path = ""
        self.post_id = ""
        self.foreign = ""
        self.title = ""

    def set_alt(self, alt):
        """
        Set alt attribute

        :param alt: alt
        :return:
        """
        self.alt = alt

    def set_path(self, path):
        """
        Set path attribute

        :param path: path
        :return:
        """
        self.path = path

    def set_post_id(self, post_id):
        """
        Set id of a post attribute

        :param post_id: if of a post
        :return:
        """
        self.post_id = post_id

    def set_foreign(self, foreign):
        """
        Set foreign attribute

        :param foreign: uri of media
        :return:
        """
        self.foreign = foreign

    def set_title(self, title):
        """
        Set title attribute

        :param title: title of a media
        :return:
        """
        self.title = title
