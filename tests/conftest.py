import os
import tempfile

import pytest
from api import create_app

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql.functions import current_timestamp


with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix = '.sqlite')

    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path
    })

    db = SQLAlchemy(app)
    class User(db.Model):
        __tablename__ = 'user'
        id = db.Column(Integer, primary_key=True)
        username = db.Column(String(64), unique=False, nullable=False)
        password = db.Column(String(64), unique=False, nullable=False)

    class Note(db.Model):
        __tablename__ = 'note'
        id = db.Column(Integer, primary_key=True)
        author_id = db.Column(Integer, unique=False, nullable=False)
        root_note_id = db.Column(Integer, unique=False, nullable=True)
        created = db.Column(DateTime, unique=False, nullable=False, server_default=current_timestamp())
        updated = db.Column(DateTime, unique=False, nullable=False, server_default=current_timestamp())
        kind = db.Column(Integer, unique=False, nullable=False)
        sentence = db.Column(Text, unique=False, nullable=False)

    with app.app_context():
        db.create_all()
        db.engine.execute("""INSERT INTO user (username, password) VALUES """\
                          """('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'), """\
                          """('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79')""")
        db.engine.execute("""INSERT INTO note (author_id, root_note_id, created, updated, kind, sentence) VALUES """\
                          """(1, 1, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 1, '観察'), """\
                          """(1, 1, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 2, '仮説'), """\
                          """(1, 1, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 3, '実験'), """\
                          """(1, 1, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 4, '考察'), """\
                          """(1, 5, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 1, '観察'), """\
                          """(2, 6, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 1, '観察'), """\
                          """(1, 7, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 1, '観察'), """\
                          """(1, 7, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 2, '仮説'), """\
                          """(1, 9, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 1, '観察'), """\
                          """(1, 9, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 2, '仮説'), """\
                          """(1, 9, '2019-01-01 00:00:00', '2019-01-01 00:00:00', 3, '実験')""")

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
