"""Processing of notifications of a bot"""
import re
import shutil
import datetime
from time import sleep
import atproto_client.exceptions
import requests
from atproto import Client, models
from dateutil.parser import parse
from modules import database_control
from modules.classes import Post, Media

FETCH_NOTIFICATIONS_DELAY_SEC = 3


def count_remind(date: str, time_start: str) -> str:
    """
    Counts date from a starting date

    :param date: number of days, month and so on which must be added
    :param time_start: starting date
    :return: new date in string format
    """
    date_ret = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if date.split()[1] in ['day', 'days']:
        date_ret = parse(time_start) + datetime.timedelta(days=int(date.split()[0]))
    if date.split()[1] in ['month', 'months']:
        new_month = parse(time_start).month + int(date.split()[0])
        if new_month < 12:
            date_ret = parse(time_start).replace(month=new_month)
        else:
            date_ret = parse(time_start).replace(month=(new_month % 12 + 1), year=parse(time_start).year + (new_month // 12))
    if date.split()[1] in ['year', 'years']:
        date_ret = parse(time_start).replace(year=parse(time_start).year + int(date.split()[0]))
    if date.split()[1] in ['minute', 'minutes']:
        date_ret = parse(time_start) + datetime.timedelta(minutes=int(date.split()[0]))
    if date.split()[1] in ['hour', 'hours']:
        date_ret = parse(time_start) + datetime.timedelta(hours=int(date.split()[0]))
    if date.split()[1] in ['week', 'weeks']:
        date_ret = parse(time_start) + datetime.timedelta(weeks=int(date.split()[0]))
    return date_ret.strftime("%Y-%m-%d %H:%M:%S")


def get_period(text_origin: str, word: str) -> str:
    """
    Gets a period from a given text origin.

    :param text_origin: text from which must be found period
    :param word: which word must be before period
    :return: period
    """
    punc = '''!()-[]{};:'"\\, <>./?@#$%^&*_~'''
    text = text_origin
    for i in punc:
        text = text.replace(i, ' ')
    text = re.sub(' +', ' ', text)
    text_split = text.split(' ')
    if text.lower().find(word.lower()) != -1:
        for (i, elem) in enumerate(text_split):
            if elem.lower() == word.lower() and i + 1 in range(len(text_split)):
                time = text_split[i + 1]
                try:
                    int(time)
                except ValueError:
                    return "1 day"
                item = 'day'
                if i + 2 in range(len(text_split)):
                    item = text_split[i + 2]
                    if item.lower() not in ['day', 'days', 'month', 'months', 'year', 'years',
                                            'minute', 'minutes', 'hour', 'hours', 'week', 'weeks']:
                        item = 'day'
                return str(time) + " " + item
    return ''


def get_time_to_remind_from_post(text: str, time_send: str) -> str:
    """
    Returns date when post must be reminded

    :param text: post message where will be found a period
    :param time_send: time when post was sent
    :return: date when post must be reminded
    """
    if get_period(text, 'in') != '':
        return count_remind(get_period(text, 'in'), database_control.convert_date(time_send))
    try:
        time_send_1 = datetime.datetime.strptime(database_control.convert_date(time_send), '%Y-%m-%d %H:%M:%S')
        parse_time = parse(text, fuzzy=True, default=time_send_1, dayfirst=True).strftime('%Y-%m-%d %H:%M:%S')
        return parse_time
    except ValueError:
        return count_remind('1 day', database_control.convert_date(time_send))


def get_every_from_post(text: str) -> int:
    """
    Gets how often post must be reminded

    :param text: post text from which will be found period
    :return: period in seconds how often post must be reminded
    """
    ret = 0
    try:
        if get_period(text, 'every'):
            text = get_period(text, 'every')
            if text.split()[1] in ['day', 'days']:
                ret = int(text.split()[0]) * 24 * 60 * 60
            if text.split()[1] in ['month', 'months']:
                ret = int(text.split()[0]) * 24 * 60 * 60 * 30
            if text.split()[1] in ['year', 'years']:
                ret = int(text.split()[0]) * 24 * 60 * 60 * 365
            if text.split()[1] in ['minute', 'minutes']:
                ret = int(text.split()[0]) * 60
            if text.split()[1] in ['hour', 'hours']:
                ret = int(text.split()[0]) * 60 * 60
            if text.split()[1] in ['week', 'weeks']:
                ret = int(text.split()[0]) * 24 * 60 * 60 * 7
    except ValueError:
        ret = 0
    return ret


class GetPosts:
    """Class that handles getting and processes posts"""

    def __init__(self, client, database_path, media_path):
        self.client = client
        self.database_path = database_path
        self.media_path = media_path

    def reply_to_post_delete(self, post_reply_to) -> None:
        """
        Replies to a post after deleting a reminder.

        :param post_reply_to: post to which reply will be sent
        :return:
        """
        root_post_ref = models.create_strong_ref(post_reply_to)
        self.client.send_post(
            text='Okay, I deleted this reminder from my mind. :)',
            reply_to=models.AppBskyFeedPost.ReplyRef(parent=root_post_ref, root=root_post_ref),
        )

    def reply_to_post_error(self, post_reply_to, error="") -> None:
        """
        Replies to a given post with a specific error message or an ordinary reply.

        :param post_reply_to: post which will be replied to
        :param error: error message
        :return: None
        """
        root_post_ref = models.create_strong_ref(post_reply_to)
        if error == '':
            self.client.send_post(
                text='I am sorry. Error occurred. I cannot remind you this :(',
                reply_to=models.AppBskyFeedPost.ReplyRef(parent=root_post_ref, root=root_post_ref),
            )
        else:
            self.client.send_post(
                text=error,
                reply_to=models.AppBskyFeedPost.ReplyRef(parent=root_post_ref, root=root_post_ref),
            )

    def download_photo(self, author_did: str, image_id: str, post_id: int) -> None:
        """
        Downloads a photo from a given author.

        :param author_did: did of photo's author (the user who posted the photo)
        :param image_id: id of an image
        :param post_id: id of a post
        :return: None
        """
        url = "https://cdn.bsky.app/img/feed_fullsize/plain/" + author_did + "/" + image_id.link
        res = requests.get(url, stream=True, timeout=5)
        if res.status_code == 200:
            with open(self.media_path + '/' + str(post_id) + "_" + image_id.link + ".jpg", 'wb') as f:
                shutil.copyfileobj(res.raw, f)
        else:
            print("Error! Media couldn't be retrieved")

    def add_gif(self, url: str, alt: str, post_id: int, title: str) -> None:
        """
        Adds gif to a database

        :param title: media title
        :param url: url of a gif
        :param alt: alt description of a gif
        :param post_id: id of a post in which gif is
        :return: None
        """
        media = Media()
        media.set_post_id(post_id)
        media.set_alt(alt)
        media.set_foreign(url)
        media.set_title(title)
        database_control.Database(self.database_path).insert_media(media)

    def reply_to_post_ok(self, post_reply_to, time_to_remind) -> None:
        """
        Replies to a given post with an ok message.

        :param post_reply_to: post which will be replied to
        :param time_to_remind: time when post will be reminded
        :return: None
        """

        remind_date = datetime.datetime.strptime(time_to_remind, '%Y-%m-%d %H:%M:%S')
        root_post_ref = models.create_strong_ref(post_reply_to)
        self.client.send_post(
            text=f"I will remind you this on {str(remind_date.strftime('%d-%m-%Y'))} at {str(remind_date.strftime('%H:%M'))}! :)\nBeware! "
                 f'Date of the reminder is in UTC-0 time!',
            reply_to=models.AppBskyFeedPost.ReplyRef(parent=root_post_ref, root=root_post_ref),
        )

    def get_mentions_post(self, post, app_handle) -> list[str]:
        """
        Gets a list of mentions from a post.

        :param app_handle: handle of a current program
        :param post: post from which must be got mentions
        :return: list of user handle who where mentioned without bot's handle
        """

        ret_mentions = []
        for mention in post.value.facets:
            if mention.features[0].did != self.client.resolve_handle(app_handle).did:
                ret_mentions.append(self.client.get_profile(mention.features[0].did).handle)
        return ret_mentions

    def get_any_media(self, parent_post, post_id):
        """
        Downloads or gets url of any media in post

        :param parent_post: post from which media will be downloaded
        :param post_id: id of a reply post which was added to a database previously
        :return:
        """
        try:
            for img in parent_post.record.embed.images:
                self.download_photo(author_did=parent_post.author.did, image_id=img.image.ref, post_id=post_id)
                media = Media()
                media.set_post_id(post_id)
                media.set_alt(img.alt)
                media.set_path(str(post_id) + "_" + img.image.ref.link + ".jpg")
                database_control.Database(self.database_path).insert_media(media)
        except AttributeError:
            print("Post doesn't have images")

        try:
            self.add_gif(url=parent_post.record.embed.external.uri, alt=parent_post.record.embed.external.description,
                         post_id=post_id, title=parent_post.record.embed.external.title)
        except AttributeError:
            print("Post doesn't have any gif")

    def get_any_facets(self, post, post_id):
        """
        Function gets any facets from the post

        :param post: given post from which facets will be added to a database
        :param post_id: id of a post in a database
        :return:
        """
        try:
            for facet in post.record.facets:
                facet_type = ''
                uri = ''
                if hasattr(facet.features[0], 'did'):
                    facet_type = 'mention'
                    uri = facet.features[0].did
                if hasattr(facet.features[0], 'tag'):
                    facet_type = 'tag'
                    uri = facet.features[0].tag
                if hasattr(facet.features[0], 'uri'):
                    facet_type = 'link'
                    uri = facet.features[0].uri
                database_control.Database(self.database_path).insert_facets([facet.index.byte_start, facet.index.byte_end], facet_type, uri,
                                                                            post_id)
        except TypeError:
            pass

    def get_new_notifications(self, response):
        """
        Gets new notifications

        :param response: response with all notifications
        :return: list of unprocessed notifications
        """
        new_mentions = []
        for notification in response.notifications:
            if notification.reason == 'mention' and database_control.Database(self.database_path).get_notifications_db(notification):
                new_mentions.append(notification)
        return new_mentions


def get_notifications(app_handle, app_password, database_path, media_path) -> None:
    """
    Gets and processes notifications

    :return: None
    """
    client = Client()
    client.login(app_handle, app_password)
    get_post = GetPosts(client, database_path, media_path)

    while True:
        last_seen_at = client.get_current_time_iso()
        try:
            response = client.app.bsky.notification.list_notifications()
        except (atproto_client.exceptions.InvokeTimeoutError, atproto_client.exceptions.NetworkError, atproto_client.exceptions.AtProtocolError):
            client.login(app_handle, app_password)
            response = client.app.bsky.notification.list_notifications()

        client.app.bsky.notification.update_seen({'seen_at': last_seen_at})

        for notification in get_post.get_new_notifications(response):
            post = client.get_post(post_rkey=notification.uri.split('/')[-1], profile_identify=notification.author.did)
            if notification.author.did == client.resolve_handle(app_handle):
                continue
            time_to_remind = get_time_to_remind_from_post(text=post.value.text, time_send=post.value.created_at)
            if datetime.datetime.strptime(time_to_remind, '%Y-%m-%d %H:%M:%S').replace(
                    tzinfo=datetime.timezone.utc) < datetime.datetime.now().astimezone(datetime.timezone.utc):
                get_post.reply_to_post_error(post,
                                             error="You want me to remind on a date that is in the past. I don't have time machine yet. "
                                                   "I am really sorry :(")
                continue
            try:
                post_parent = client.get_posts(uris=[post.value.reply.parent.uri]).posts[0]
                new_post = Post()
                if post.value.text.find('delete') != -1 and post_parent.record.text.find('@' + app_handle) != -1:
                    new_post.set_author_remind(notification.author.handle)
                    new_post.set_time_send_request(post_parent.record.created_at)
                    database_control.Database(database_path).delete_post(new_post, media_path)
                    get_post.reply_to_post_delete(post)
                    continue
                if post.value.text.find('delete') != -1 and post_parent.record.text.find('@' + app_handle) == -1:
                    get_post.reply_to_post_error(post,
                                                 error="I'm sorry. I don't find this post in my memory. Maybe you meant the one I answered to?")
                    continue

                new_post.set_text(post_parent.record.text)
                new_post.set_time_to_remind(time_to_remind)
                new_post.set_author_remind(notification.author.handle)
                new_post.set_author_post(post_parent.author.handle)
                new_post.set_time_send_request(post.value.created_at)
                new_post.set_people_remind(get_post.get_mentions_post(post, app_handle))
                new_post.set_every_n_seconds(get_every_from_post(text=post.value.text))
                post_id = database_control.Database(database_path).insert_post(new_post)

                get_post.get_any_media(post_parent, post_id)
                get_post.get_any_facets(post_parent, post_id)
                get_post.reply_to_post_ok(post, time_to_remind)
            except AttributeError as e:
                print("Error:", e)
                get_post.reply_to_post_error(post, error="Your message is not a reply. I am sorry :(")

        sleep(FETCH_NOTIFICATIONS_DELAY_SEC)
