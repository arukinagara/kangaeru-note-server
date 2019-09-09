from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql.functions import current_timestamp
from api.db import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=False, nullable=False)
    password = Column(String(64), unique=False, nullable=False)

    def __init__(self, username = None, password = None):
        self.username = username
        self.password = password

    def __repr__(self):
        return 'User(id = {0}, username = {1})'.format(self.id, self.username)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Note(Base):
    __tablename__ = 'note'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, unique=False, nullable=False)
    root_note_id = Column(Integer, unique=False, nullable=True)
    created = Column(DateTime, unique=False, nullable=False, server_default=current_timestamp())
    updated = Column(DateTime, unique=False, nullable=False, server_default=current_timestamp())
    kind = Column(Integer, unique=False, nullable=False)
    sentence = Column(Text, unique=False, nullable=False)

    def __init__(self, author_id = None, root_note_id = None,
                 created = None, updated = None, kind = None, sentence = None):
        self.author_id = author_id
        self.root_note_id = root_note_id
        self.created = created
        self.updated = updated
        self.kind = kind
        self.sentence = sentence

    def __repr__(self):
        return ('Note(id = {0}, author_id = {1}, root_note_id = {2}, '\
                'created = {3}, updated = {4}, kind = {5}, sentence ={6})'
                  .format(
                    self.id,
                    self.author_id,
                    self.root_note_id,
                    self.created,
                    self.updated,
                    self.kind,
                    self.sentence
                  ))

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
