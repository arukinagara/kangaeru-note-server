import pytest
import json
from datetime import datetime
from flask import g, session
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_refresh_token_required, get_jwt_identity
)
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
def test_index(app, client, auth, query_parameter, res_payload):
    response = client.get('/')

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']

        index_response = client.get('/' + query_parameter,
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
        )

        assert index_response.status_code == 200
        assert json.loads(index_response.data) == res_payload


# ノート作成 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    ({'kind': '', 'sentence': '観察'}, {'message': 'Kind is required.'}),
    ({'kind': 1, 'sentence': ''}, {'message': 'Sentence is required.'}),
    ({'root_note_id': 1, 'kind': 2, 'sentence': '仮説'}, {'message': 'Not related note.'}), # kind重複
    ({'root_note_id': 5, 'kind': 3, 'sentence': '実験'}, {'message': 'Not related note.'}), # kind飛び
    ({'root_note_id': 6, 'kind': 2, 'sentence': '仮説'}, {'message': 'Not related note.'}), # 他人のノート
    ({'root_note_id': 7, 'kind': 2, 'sentence': '仮説'}, {'message': 'Not related note.'}), # 存在しない
))
def test_create_validate_input(app, client, auth, req_payload, res_payload):
    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']

        create_response = client.post('/',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
            data = json.dumps(req_payload),
        )

        assert create_response.status_code == 400
        assert json.loads(create_response.data) == res_payload


# ノート作成 正常系
@pytest.mark.parametrize(('req_payload', 'res_payload', 'will_insert_note'), (
    ({'kind': 1, 'sentence': '観察'}, {'id': 7},
        {'id': 7, 'author_id': 1, 'root_note_id': 7, 'kind': 1, 'sentence': '観察'}),
    ({'root_note_id': 5, 'kind': 2, 'sentence': '仮説'}, {'id': 7},
        {'id': 7, 'author_id': 1, 'root_note_id': 5, 'kind': 2, 'sentence': '仮説'}),
))
def test_create(app, client, auth, req_payload, res_payload, will_insert_note):
    response = client.post('/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload)
    )

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']

        create_response = client.post('/',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
            data = json.dumps(req_payload),
        )

        assert create_response.status_code == 201
        assert json.loads(create_response.data) == res_payload

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
    ({'id': '', 'sentence': '観察'}, {'message': 'Id is required.'}),
    ({'id': 1, 'sentence': ''}, {'message': 'Sentence is required.'}),
    ({'id': 6, 'sentence': '変更された観察'}, {'message': 'Note not found.'}), # 他人のノート
    ({'id': 7, 'sentence': '変更された観察'}, {'message': 'Note not found.'}), # 存在しない
))
def test_update_validate_input(app, client, auth, req_payload, res_payload):
    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']
        update_response = client.put('/',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
            data = json.dumps(req_payload),
        )

        assert update_response.status_code == 400
        assert json.loads(update_response.data) == res_payload


# ノート更新 正常系
@pytest.mark.parametrize(('req_payload', 'will_update_note'), (
    ({'id': 1, 'sentence': '変更された観察'},
        {'id': 1, 'author_id': 1, 'root_note_id': 1,'created': '2019-01-01 00:00:00',
            'kind': 1, 'sentence': '変更された観察'}),
))
def test_update(app, client, auth, req_payload, will_update_note):
    response = client.put('/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload)
    )

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']

        update_response = client.put('/',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
            data = json.dumps(req_payload),
        )

        assert update_response.status_code == 204

        with app.app_context():
            updated_note = get_db().execute(
                'SELECT * FROM note WHERE id = ?',
                (json.loads(json.dumps(req_payload))['id'],)
            ).fetchone()

            assert updated_note['sentence'] == will_update_note['sentence']
            assert updated_note['created'] == datetime.strptime(will_update_note['created'], '%Y-%m-%d %H:%M:%S')
            assert updated_note['updated'] > datetime.strptime(will_update_note['created'], '%Y-%m-%d %H:%M:%S')


# ノート削除 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    ({'id': ''}, {'message': 'Id is required.'}),
    ({'id': 6}, {'message': 'Note not found.'}), # 他人のノート
    ({'id': 7}, {'message': 'Note not found.'}), # 存在しない
))
def test_update_validate_input(app, client, auth, req_payload, res_payload):
    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']
        delete_response = client.delete('/',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
            data = json.dumps(req_payload),
        )

        assert delete_response.status_code == 400
        assert json.loads(delete_response.data) == res_payload


# ノート削除 正常系
@pytest.mark.parametrize(('req_payload', 'will_remain_note'), (
    ({'id': 1}, []),
    ({'id': 2}, [{'id': 1, 'author_id': 1, 'root_note_id': 1,
                  'created': datetime(2019, 1, 1, 0, 0), 'updated': datetime(2019, 1, 1, 0, 0),
                  'kind': 1, 'sentence': '観察'}]),
))
def test_update_validate_input(app, client, auth, req_payload, will_remain_note):
    response = client.delete('/',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload)
    )

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    with app.app_context():
        jwt = JWTManager(app)

        @jwt.user_loader_callback_loader
        def user_load_callback(identity):
            return {'id': 1}

        login_response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({'username': 'test', 'password': 'test'}),
        )

        access_token = json.loads(login_response.data)['access_token']

        delete_response = client.delete('/',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
            data = json.dumps(req_payload),
        )

        assert delete_response.status_code == 204

        with app.app_context():
            remained_note = get_db().execute(
                'SELECT * FROM note WHERE root_note_id = 1'
            ).fetchall()

            assert remained_note == will_remain_note
