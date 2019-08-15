import pytest
import json
from datetime import datetime
from flask import g, session
from api.db import get_db


# ノート取得 正常系
@pytest.mark.parametrize(('query_parameter', 'res_payload'), (
    ('?root=1',
        {'notes': [
            {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 2, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 2, 'sentence': '仮説'},
            {'id': 3, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 3, 'sentence': '実験'},
            {'id': 4, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 4, 'sentence': '考察'}
        ]}),
    ('?kind=1',
        {'notes': [
            {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 5, 'author_id': 1, 'root_note_id': 5, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'}
        ]}),
    ('',
        {'notes': [
            {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 2, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 2, 'sentence': '仮説'},
            {'id': 3, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 3, 'sentence': '実験'},
            {'id': 4, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 4, 'sentence': '考察'},
            {'id': 5, 'author_id': 1, 'root_note_id': 5, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT',
                'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'}
        ]}),
))
def test_index(client, auth, query_parameter, res_payload):
    response = client.get('/')
    assert response.status_code == 401

    # ここではログイン処理はpytestのフィクスチャを使う
    auth.login()
    response = client.get('/' + query_parameter)
    assert response.status_code == 200
    assert json.loads(response.data) == res_payload


# ノート作成 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    (json.dumps({'kind': '', 'sentence': '観察'}), {'message': 'Kind is required.'}),
    (json.dumps({'kind': 1, 'sentence': ''}), {'message': 'Sentence is required.'}),
    (json.dumps({'root_note_id': 1, 'kind': 2, 'sentence': '仮説'}), {'message': 'Not related note.'}), # kind重複
    (json.dumps({'root_note_id': 5, 'kind': 3, 'sentence': '実験'}), {'message': 'Not related note.'}), # kind飛び
    (json.dumps({'root_note_id': 6, 'kind': 2, 'sentence': '仮説'}), {'message': 'Not related note.'}), # 他人のノート
    (json.dumps({'root_note_id': 7, 'kind': 2, 'sentence': '仮説'}), {'message': 'Not related note.'}), # 存在しない
))
def test_create_validate_input(client, auth, req_payload, res_payload):
    response = client.post('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401

    auth.login()
    response = client.post('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 400
    assert json.loads(response.data) == res_payload


# ノート作成 正常系
@pytest.mark.parametrize(('req_payload', 'res_payload', 'will_insert_note'), (
    (json.dumps({'kind': 1, 'sentence': '観察'}), {'id': 7},
        {'id': 7, 'author_id': 1, 'root_note_id': 7, 'kind': 1, 'sentence': '観察'}),
    (json.dumps({'root_note_id': 5, 'kind': 2, 'sentence': '仮説'}), {'id': 7},
        {'id': 7, 'author_id': 1, 'root_note_id': 5, 'kind': 2, 'sentence': '仮説'}),
))
def test_create(client, app, auth, req_payload, res_payload, will_insert_note):
    response = client.post('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401

    auth.login()
    response = client.post('/',
        data = req_payload,
        content_type = 'application/json'
    )

    assert response.status_code == 201
    assert json.loads(response.data) == res_payload
    with app.app_context():
        inserted_note = get_db().execute(
            'SELECT * FROM note WHERE id = ?',
            (res_payload['id'],)
        ).fetchone()
        assert inserted_note['author_id'] == will_insert_note['author_id']
        assert inserted_note['root_note_id'] == will_insert_note['root_note_id']
        assert inserted_note['kind'] == will_insert_note['kind']
        assert inserted_note['sentence'] == will_insert_note['sentence']


# ノート更新 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    (json.dumps({'id': '', 'sentence': '観察'}), {'message': 'Id is required.'}),
    (json.dumps({'id': 1, 'sentence': ''}), {'message': 'Sentence is required.'}),
    (json.dumps({'id': 6, 'sentence': '変更された観察'}), {'message': 'Note not found.'}), # 他人のノート
    (json.dumps({'id': 7, 'sentence': '変更された観察'}), {'message': 'Note not found.'}), # 存在しない
))
def test_update_validate_input(client, auth, req_payload, res_payload):
    response = client.put('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401

    auth.login()
    response = client.put('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 400
    assert json.loads(response.data) == res_payload


# ノート更新 正常系
@pytest.mark.parametrize(('req_payload', 'will_update_note'), (
    (json.dumps({'id': 1, 'sentence': '変更された観察'}),
        {'id': 1, 'author_id': 1, 'root_note_id': 1,'created': '2019-01-01 00:00:00',
            'kind': 1, 'sentence': '変更された観察'}),
))
def test_create(client, app, auth, req_payload, will_update_note):
    response = client.put('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401

    auth.login()
    response = client.put('/',
        data = req_payload,
        content_type = 'application/json'
    )

    assert response.status_code == 204
    with app.app_context():
        updated_note = get_db().execute(
            'SELECT * FROM note WHERE id = ?',
            (json.loads(req_payload)['id'],)
        ).fetchone()
        assert updated_note['sentence'] == will_update_note['sentence']
        assert updated_note['created'] == datetime.strptime(will_update_note['created'], '%Y-%m-%d %H:%M:%S')
        assert updated_note['updated'] > datetime.strptime(will_update_note['created'], '%Y-%m-%d %H:%M:%S')


# ノート削除 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    (json.dumps({'id': ''}), {'message': 'Id is required.'}),
    (json.dumps({'id': 6}), {'message': 'Note not found.'}), # 他人のノート
    (json.dumps({'id': 7}), {'message': 'Note not found.'}), # 存在しない
))
def test_update_validate_input(client, auth, req_payload, res_payload):
    response = client.delete('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401

    auth.login()
    response = client.delete('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 400
    assert json.loads(response.data) == res_payload


# ノート削除 正常系
@pytest.mark.parametrize(('req_payload', 'will_remain_note'), (
    (json.dumps({'id': 1}), []),
    (json.dumps({'id': 2}), [
        {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': datetime(2019, 1, 1, 0, 0),
            'updated': datetime(2019, 1, 1, 0, 0), 'kind': 1, 'sentence': '観察'}]),
))
def test_update_validate_input(client, app, auth, req_payload, will_remain_note):
    response = client.delete('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401

    auth.login()
    response = client.delete('/',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 204
    with app.app_context():
        remained_note = get_db().execute(
            'SELECT * FROM note WHERE root_note_id = 1'
        ).fetchall()
        assert remained_note == will_remain_note
