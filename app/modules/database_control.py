"""File with class that work with database"""
import os
from datetime import timedelta
import sqlalchemy as db
from dateutil.parser import parse
from sqlalchemy import Column, Integer, String, ForeignKey
from modules.classes import Post, Media


def convert_date(time) -> str:
    """
    Converts a date into correct format

    :param time: string that will be converted
    :return: return date in correct format
    """
    return time.split('T')[0] + " " + time.split('T')[1].split('.')[0]


class Database:
    """Class that handles database operations"""

    def __init__(self, database_location):
        self.engine = db.create_engine("sqlite:///" + database_location)
        self.connection = self.engine.connect()
        self.people_table = db.Table('PEOPLE', db.MetaData(),
                                     Column('ID', Integer, primary_key=True),
                                     Column('HANDLE', String))
        self.post_table = db.Table('POSTS', db.MetaData(),
                                   Column('ID', Integer, primary_key=True),
                                   Column('TEXT', String),
                                   Column('TIME_TO_REMIND', String),
                                   Column('AUTHOR_REMIND', Integer, ForeignKey(self.people_table.c.ID)),
                                   Column('AUTHOR_POST', Integer, ForeignKey(self.people_table.c.ID)),
                                   Column('EVERY_N_SECONDS', Integer),
                                   Column('TIME_SEND_REQUEST', String))
        self.person_mention_post = db.Table('PERSON_POST_MENTION', db.MetaData(),
                                            Column('ID', Integer, primary_key=True),
                                            Column('POST_ID', Integer, ForeignKey(self.post_table.c.ID)),
                                            Column('PERSON_ID', Integer, ForeignKey(self.post_table.c.ID)))
        self.media_table = db.Table('MEDIA', db.MetaData(),
                                    Column('ID', Integer, primary_key=True),
                                    Column('PATH', String),
                                    Column('ALT', String),
                                    Column('IS_FOREIGN', String),
                                    Column('TITLE', String),
                                    Column('POST_ID', Integer, ForeignKey(self.post_table.c.ID)))
        self.facets_table = db.Table('FACETS', db.MetaData(),
                                     Column('ID', Integer, primary_key=True),
                                     Column('BYTE_START', Integer),
                                     Column('BYTE_END', Integer),
                                     Column('TYPE', String),
                                     Column('URI', String),
                                     Column('POST_ID', Integer, ForeignKey(self.post_table.c.ID)))
        self.post_table.create(self.engine, checkfirst=True)
        self.people_table.create(self.engine, checkfirst=True)
        self.person_mention_post.create(self.engine, checkfirst=True)
        self.media_table.create(self.engine, checkfirst=True)
        self.facets_table.create(self.engine, checkfirst=True)

    def find_person(self, handle: str) -> int:
        """
        Find person from a database

        :param handle: handle of a person which needs to be found
        :return: id of a person in a database or -1 if person was not found
        """
        stmt = db.select(self.people_table).where(self.people_table.c.HANDLE == handle)
        for row in self.connection.execute(stmt):
            return row.ID
        return -1

    def insert_person(self, handle: str) -> int:
        """
        Inserts person into a database

        :param handle: handle of a person which will be put into a database
        :return: id of an inserted person
        """
        stmt = db.insert(self.people_table).values(HANDLE=handle)
        result = self.connection.execute(stmt)
        self.connection.commit()
        return result.inserted_primary_key[0]

    def find_person_or_insert(self, handle: str) -> int:
        """
        Find a person's id in a database or inserts them to a database

       :param handle: handle of a person
       :return: id of a person in a database
       """

        ind = self.find_person(handle)
        if ind == -1:
            ind = self.insert_person(handle)
        return ind

    def insert_person_post_mention(self, post_ind: int, post: Post) -> None:
        """
        Inserts mentions from a post into a database

        :param post_ind: id of a post
        :param post: inserted post
        :return:
         """

        if not post.people_remind:
            post.people_remind = [post.author_remind]
        for person in post.people_remind:
            ind = self.find_person(person)
            if ind == -1:
                ind = self.insert_person(person)
            stmt = db.insert(self.person_mention_post).values(POST_ID=post_ind, PERSON_ID=ind)
            self.connection.execute(stmt)
            self.connection.commit()

    def insert_post(self, post_insert: Post) -> int:
        """
        Inserts post into a database

        :param post_insert: post that will be inserted
        :return: id of an inserted post
        """

        date = convert_date(post_insert.time_send_request)
        time_to_remind = post_insert.time_to_remind
        author_post = self.find_person_or_insert(post_insert.author_post)
        author_remind = self.find_person_or_insert(post_insert.author_remind)
        stmt = db.insert(self.post_table).values(TEXT=post_insert.text, AUTHOR_REMIND=author_remind, TIME_SEND_REQUEST=date,
                                                 AUTHOR_POST=author_post, TIME_TO_REMIND=time_to_remind,
                                                 EVERY_N_SECONDS=post_insert.every_n_seconds)
        result = self.connection.execute(stmt)
        self.insert_person_post_mention(result.inserted_primary_key[0], post_insert)
        self.connection.commit()
        return result.inserted_primary_key[0]

    def delete_post(self, post_delete: Post, media_path) -> None:
        """
        Deletes a post from a database

        :param media_path: path to media folder
        :param post_delete: post that will be deleted
        :return:
        """
        date = convert_date(post_delete.time_send_request)
        author_remind = self.find_person_or_insert(post_delete.author_remind)
        stmt = db.select(self.post_table).where(
            self.post_table.c.AUTHOR_REMIND == author_remind, self.post_table.c.TIME_SEND_REQUEST == date)
        result = self.connection.execute(stmt).fetchone()
        self.delete_post_by_id(result.ID, media_path)
        self.connection.commit()

    def insert_media(self, media: Media) -> None:
        """
        Inserts media into a database

        :param media: media that will be inserted
        :return:
        """
        stmt = db.insert(self.media_table).values(PATH=media.path, ALT=media.alt, POST_ID=media.post_id, IS_FOREIGN=media.foreign,
                                                  TITLE=media.title)
        self.connection.execute(stmt)
        self.connection.commit()

    def insert_facets(self, index, facet_type, uri, post_id) -> None:
        """
        Inserts facets into a database

        :param index: indexes of a facet
        :param facet_type: type of facet
        :param uri: uri of facet
        :param post_id: id of post that facets are from
        :return:
        """
        stmt = db.insert(self.facets_table).values(BYTE_START=index[0], BYTE_END=index[1], TYPE=facet_type, URI=uri, POST_ID=post_id)
        self.connection.execute(stmt)
        self.connection.commit()

    def get_mentions(self, post_id):
        """
        Gets all mentions from post

        :param post_id: id of a post
        :return:
        """
        stmt = db.select(self.person_mention_post).where(self.person_mention_post.c.POST_ID == post_id)
        return self.connection.execute(stmt).fetchall()

    def get_person_handle(self, person_id):
        """
        Gets persons handle by id

        :param person_id: person's id
        :return:
        """
        stmt = db.select(self.people_table).where(self.people_table.c.ID == person_id)
        person = self.connection.execute(stmt).fetchone()
        return person.HANDLE

    def delete_post_by_id(self, post_id, media_path) -> None:
        """
        Deletes post by id

        :param post_id: id of a post
        :return:
        """
        stmt = db.delete(self.post_table).where(self.post_table.c.ID == post_id)
        self.connection.execute(stmt)
        stmt = db.select(self.media_table).where(self.media_table.c.POST_ID == post_id)
        for media in self.connection.execute(stmt):
            if not media.IS_FOREIGN:
                os.remove(media_path + '/' + media.PATH)
        stmt = db.delete(self.media_table).where(self.media_table.c.POST_ID == post_id)
        self.connection.execute(stmt)
        stmt = db.delete(self.facets_table).where(self.facets_table.c.POST_ID == post_id)
        self.connection.execute(stmt)
        stmt = db.delete(self.person_mention_post).where(self.person_mention_post.c.POST_ID == post_id)
        self.connection.execute(stmt)
        self.connection.commit()

    def update_post_time_remind(self, post_record) -> None:
        """
        Updates time remind in a post

        :param post_record: database record of a post
        :return:
        """
        date_ret = parse(post_record.TIME_TO_REMIND) + timedelta(seconds=int(post_record.EVERY_N_SECONDS))
        stmt = db.update(self.post_table).where(self.post_table.c.ID == post_record.ID).values(
            TIME_TO_REMIND=date_ret.strftime('%Y-%m-%d %H:%M'))
        self.connection.execute(stmt)
        self.connection.commit()

    def get_facets_by_post_id(self, post_id):
        """
        Returns all facets from a post

        :param post_id: id of a post
        :return: rows of a table
        """
        stmt = db.select(self.facets_table).where(self.facets_table.c.POST_ID == post_id)
        return self.connection.execute(stmt).fetchall()

    def get_media_by_post_id(self, post_id):
        """
        Get media by post_id

        :param post_id: id of a post
        :return:
        """
        stmt = db.select(self.media_table).where(self.media_table.c.POST_ID == post_id)
        return self.connection.execute(stmt).fetchall()

    def get_posts_by_time_to_remind(self, time_to_remind):
        """
        Get posts by time_to_remind attribute

        :param time_to_remind: time to remind
        :return:
        """
        stmt = db.select(self.post_table).where(self.post_table.c.TIME_TO_REMIND == time_to_remind)
        return self.connection.execute(stmt).fetchall()

    def get_notifications_db(self, notification) -> bool:
        """
        Returns if notification is not in a database

        :param notification: notification that must be checked
        :return: True (notification was not database) or False (notification is in the database)
        """
        notification_table = db.Table('NOTIFICATIONS', db.MetaData(),
                                      Column('ID', Integer, primary_key=True),
                                      Column('CID', String))
        notification_table.create(self.engine, checkfirst=True)
        stmt = db.select(notification_table).where(notification.cid == notification_table.c.CID)
        result = self.connection.execute(stmt).fetchall()
        if not result:
            stmt = db.insert(notification_table).values(CID=notification.cid)
            self.connection.execute(stmt)
            self.connection.commit()
            return True
        return False

    def stop(self) -> None:
        """
        Stops connection

        :return:
        """
        self.connection.close()
        self.engine.dispose()
