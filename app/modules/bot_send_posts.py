"""Sending reminders when it is time"""
from datetime import datetime, timezone
from time import sleep
import atproto_client.exceptions
from atproto import Client, client_utils, models
from modules import database_control

SEND_POST_DELAY_SEC = 10


class SendPost:
    """Class that handles sending posts back when its time"""
    def __init__(self, database_path: str, media_path: str, client: Client):
        self.database_path = database_path
        self.media_path = media_path
        self.client = client

    def send_partial_post(self, post_root, post_ref, text_builder):
        """
        Sends a part of a post

        :param post_root: root post
        :param post_ref: reference post
        :param text_builder: text_builder that will build post
        :return: tuple with a new root post and post ref
        """
        if not post_root:
            post_root = models.create_strong_ref(self.client.send_post(text_builder))
        else:
            if post_ref is None:
                post_ref = post_root
            post_ref = models.create_strong_ref(
                self.client.send_post(text_builder, reply_to=models.AppBskyFeedPost.ReplyRef(parent=post_ref, root=post_root)))
        return [post_root, post_ref]

    def send_all_mentions_from_a_post(self, mentions: list[str], char_count, text_builder, refs):
        """

        :param refs: references to previous posts in a thread
        :param text_builder: text_builder that will build post
        :param char_count: number of characters to send per post
        :param mentions: list of mentions
        :return: tuple with char_count text builder and refs
        """
        for mention in mentions:
            if char_count + len(mention) + 2 > 300:
                refs[0], refs[1] = self.send_partial_post(refs[0], refs[1], text_builder)
                char_count = 0
                text_builder = client_utils.TextBuilder()
            try:
                text_builder.mention(text=('@' + mention + ' '), did=self.client.resolve_handle(mention).did)
            except atproto_client.exceptions.BadRequestError:
                text_builder.text(str('@' + mention + ' '))
            char_count += len('@' + mention + ' ')
        return [char_count, text_builder, refs]

    def post_remind_title(self, author_post: str, author_remind: str, mentions: list[str]):
        """
        Creates post that will be a title of a reminder post

        :param author_post: author of an original post
        :param author_remind: author of a reminder
        :param mentions: mentions from a reminder
        :return:
        """
        post_root = None
        post_ref = None
        char_count = 0
        text_builder = client_utils.TextBuilder()
        text_builder.text("Hi! Here's a reminder for you! ")
        char_count += len("Hi! Here's a reminder for you! ")
        char_count, text_builder, [post_root, post_ref] = self.send_all_mentions_from_a_post(mentions, char_count,
                                                                                             text_builder,
                                                                                             [post_root, post_ref])
        if char_count + len("\nAnd this reminder is brought to you by: ") > 300:
            post_root, post_ref = self.send_partial_post(post_root, post_ref, text_builder)
            char_count = 0
            text_builder = client_utils.TextBuilder()
        text_builder.text("\nAnd this reminder is brought to you by: ")
        char_count += len("\nAnd this reminder is brought to you by: ")
        if char_count + len('@' + author_remind) > 300:
            post_root, post_ref = self.send_partial_post(post_root, post_ref, text_builder)
            char_count = 0
            text_builder = client_utils.TextBuilder()
        try:
            text_builder.mention(text=('@' + author_remind), did=self.client.resolve_handle(author_remind).did)
        except atproto_client.exceptions.BadRequestError:
            text_builder.text(str('@' + author_remind))
        char_count += len('@' + author_remind)
        if char_count + len("\nOriginal post was created by: ") > 300:
            post_root, post_ref = self.send_partial_post(post_root, post_ref, text_builder)
            char_count = 0
            text_builder = client_utils.TextBuilder()
        text_builder.text("\nOriginal post was created by: ")
        char_count += len("\nOriginal post was created by: ")
        if char_count + len('@' + author_post) > 300:
            post_root, post_ref = self.send_partial_post(post_root, post_ref, text_builder)
            char_count = 0
            text_builder = client_utils.TextBuilder()
        try:
            text_builder.mention(text=('@' + author_post), did=self.client.resolve_handle(author_post).did)
        except atproto_client.exceptions.BadRequestError:
            text_builder.text(str('@' + author_post))
        char_count += len('@' + author_post)
        if post_root is None:
            post_root = post_ref
        if post_root is None:
            post_ref = models.create_strong_ref(self.client.send_post(text_builder))
        else:
            post_ref = models.create_strong_ref(
                self.client.send_post(text_builder, reply_to=models.AppBskyFeedPost.ReplyRef(parent=post_ref, root=post_root)))
        if not post_root:
            post_root = post_ref
        return tuple([post_ref, post_root])

    def post_remind(self, post_ref, post_record) -> None:
        """
        Posts a reminder

        :param post_record: post that will be reminded
        :param post_ref: references to posts
        :return:
        """
        database = database_control.Database(self.database_path)
        facets = self.resolve_facets(post_record.ID)
        media_result = database.get_media_by_post_id(post_record.ID)
        if not facets:
            facets = None
        if not media_result:
            self.client.send_post(text=post_record.TEXT, reply_to=models.AppBskyFeedPost.ReplyRef(parent=post_ref[0], root=post_ref[1]),
                                  facets=facets)
        else:
            images = []
            if media_result[0].IS_FOREIGN == '':
                for media in media_result:
                    with open(self.media_path + '/' + media.PATH, 'rb') as f:
                        upload = self.client.com.atproto.repo.upload_blob(f.read())
                        images.append(models.AppBskyEmbedImages.Image(alt=media.ALT, image=upload.blob))
                self.client.send_post(text=post_record.TEXT, reply_to=models.AppBskyFeedPost.ReplyRef(parent=post_ref[0], root=post_ref[1]),
                                      embed=models.AppBskyEmbedImages.Main(images=images), facets=facets)
            else:
                self.client.send_post(text=post_record.TEXT, reply_to=models.AppBskyFeedPost.ReplyRef(parent=post_ref[0], root=post_ref[1]),
                                      embed=models.AppBskyEmbedExternal.Main(
                                          external=models.AppBskyEmbedExternal.External(description=media_result[0].ALT,
                                                                                        uri=media_result[0].IS_FOREIGN,
                                                                                        title=media_result[0].TITLE)), facets=facets)

    def resolve_mentions(self, post_id) -> list[str]:
        """
        Resolves mentions from a post

        :param post_id: id of a post
        :return: list of handles of people mentioned
        """

        handle_mentions = []
        for mention in database_control.Database(self.database_path).get_mentions(post_id):
            handle_mentions.append(database_control.Database(self.database_path).get_person_handle(mention.PERSON_ID))
        return handle_mentions

    def send_reminder(self, post_record) -> None:
        """
        Sends a reminder

        :param post_record: database record of a post
        :return:
        """

        database = database_control.Database(self.database_path)
        title_post = self.post_remind_title(database.get_person_handle(post_record.AUTHOR_POST),
                                            database.get_person_handle(post_record.AUTHOR_REMIND),
                                            self.resolve_mentions(post_record.ID))
        self.post_remind([title_post[0], title_post[1]], post_record)
        if post_record.EVERY_N_SECONDS == 0:
            database_control.Database(self.database_path).delete_post_by_id(post_record.ID, self.media_path)
        else:
            database_control.Database(self.database_path).update_post_time_remind(post_record)

    def resolve_facets(self, post_id) -> list[models.AppBskyRichtextFacet]:
        """
        Converts all facets from a post into a list of models

        :param post_id: id of a post
        :return:
        """
        ret = []
        for facet in database_control.Database(self.database_path).get_facets_by_post_id(post_id):
            if facet.TYPE == 'mention':
                ret.append(models.AppBskyRichtextFacet.Main(features=[models.AppBskyRichtextFacet.Mention(did=facet.URI)],
                                                            index=models.AppBskyRichtextFacet.ByteSlice(byte_end=facet.BYTE_END,
                                                                                                        byte_start=facet.BYTE_START)))
            if facet.TYPE == 'tag':
                ret.append(models.AppBskyRichtextFacet.Main(features=[models.AppBskyRichtextFacet.Tag(tag=facet.URI)],
                                                            index=models.AppBskyRichtextFacet.ByteSlice(byte_end=facet.BYTE_END,
                                                                                                        byte_start=facet.BYTE_START)))
            if facet.TYPE == 'link':
                ret.append(models.AppBskyRichtextFacet.Main(features=[models.AppBskyRichtextFacet.Link(uri=facet.URI)],
                                                            index=models.AppBskyRichtextFacet.ByteSlice(byte_end=facet.BYTE_END,
                                                                                                        byte_start=facet.BYTE_START)))
        return ret


def send_main(app_handle, app_password, database_path, media_path) -> None:
    """
    Main function that checks time and gets all reminder that must be sent in that minute

    :param database_path: path to a database
    :param media_path: path to media folder
    :param app_handle: handle of a program
    :param app_password: password of a program
    :return:
    """

    client = Client()
    client.login(app_handle, app_password)
    send_post = SendPost(database_path, media_path, client)
    while True:
        for record in database_control.Database(database_path).get_posts_by_time_to_remind(
                datetime.now().astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")):
            send_post.send_reminder(record)
        sleep(SEND_POST_DELAY_SEC)
