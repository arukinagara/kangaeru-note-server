import pytest
import json
from datetime import datetime
from api.db import db
from api.model import User, Note

# ノート取得 正常系
@pytest.mark.parametrize(('query_parameter', 'res_payload'), (
    ('?root=1',
        {'notes': [
            {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 2, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 2, 'sentence': '仮説'},
            {'id': 3, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 3, 'sentence': '実験'},
            {'id': 4, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 4, 'sentence': '考察'}
        ]}),
    ('?kind=1',
        {'notes': [
            {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 5, 'author_id': 1, 'root_note_id': 5, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 7, 'author_id': 1, 'root_note_id': 7, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 9, 'author_id': 1, 'root_note_id': 9, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'}
        ]}),
    ('',
        {'notes': [
            {'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 2, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 2, 'sentence': '仮説'},
            {'id': 3, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 3, 'sentence': '実験'},
            {'id': 4, 'author_id': 1, 'root_note_id': 1, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 4, 'sentence': '考察'},
            {'id': 5, 'author_id': 1, 'root_note_id': 5, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 7, 'author_id': 1, 'root_note_id': 7, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 8, 'author_id': 1, 'root_note_id': 7, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 2, 'sentence': '仮説'},
            {'id': 9, 'author_id': 1, 'root_note_id': 9, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 1, 'sentence': '観察'},
            {'id': 10, 'author_id': 1, 'root_note_id': 9, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 2, 'sentence': '仮説'},
            {'id': 11, 'author_id': 1, 'root_note_id': 9, 'created': 'Tue, 01 Jan 2019 00:00:00 GMT', 'updated': 'Tue, 01 Jan 2019 00:00:00 GMT', 'kind': 3, 'sentence': '実験'}
        ]}),
))
def test_index(client, query_parameter, res_payload):
    response = client.get('/notes')

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']

    index_response = client.get('/notes' + query_parameter,
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
def test_create_validate_input(client, req_payload, res_payload):
    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']

    create_response = client.post('/notes',
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(access_token)},
        data = json.dumps(req_payload),
    )

    assert create_response.status_code == 400
    assert json.loads(create_response.data) == res_payload


# ノート作成 正常系
@pytest.mark.parametrize(('req_payload', 'res_payload', 'will_insert_note'), (
    (                   {'kind': 1, 'sentence': '観察'}, {'id': 12}, {'id': 12, 'author_id': 1, 'root_note_id': 12, 'kind': 1, 'sentence': '観察'}),
    ({'root_note_id': 5, 'kind': 2, 'sentence': '仮説'}, {'id': 12}, {'id': 12, 'author_id': 1, 'root_note_id': 5, 'kind': 2, 'sentence': '仮説'}),
    ({'root_note_id': 7, 'kind': 3, 'sentence': '実験'}, {'id': 12}, {'id': 12, 'author_id': 1, 'root_note_id': 7, 'kind': 3, 'sentence': '実験'}),
    ({'root_note_id': 9, 'kind': 4, 'sentence': '考察'}, {'id': 12}, {'id': 12, 'author_id': 1, 'root_note_id': 9, 'kind': 4, 'sentence': '考察'}),
))
def test_create(app, client, req_payload, res_payload, will_insert_note):
    response = client.post('/notes',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload)
    )

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']

    create_response = client.post('/notes',
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(access_token)},
        data = json.dumps(req_payload),
    )

    assert create_response.status_code == 201
    assert json.loads(create_response.data) == res_payload

    with app.app_context():
        inserted_note = Note.query.filter(Note.id == res_payload['id']).one()

        assert inserted_note.author_id == will_insert_note['author_id']
        assert inserted_note.root_note_id == will_insert_note['root_note_id']
        assert inserted_note.kind == will_insert_note['kind']
        assert inserted_note.sentence == will_insert_note['sentence']


# ノート更新 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    ({'id': '', 'sentence': '観察'}, {'message': 'Id is required.'}),
    ({'id': 1, 'sentence': ''}, {'message': 'Sentence is required.'}),
    ({'id': 6, 'sentence': '変更された観察'}, {'message': 'Note not found.'}), # 他人のノート
    ({'id': 12, 'sentence': '変更された観察'}, {'message': 'Note not found.'}), # 存在しない
))
def test_update_validate_input(app, client, req_payload, res_payload):
    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']
    update_response = client.put('/notes',
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(access_token)},
        data = json.dumps(req_payload),
    )

    assert update_response.status_code == 400
    assert json.loads(update_response.data) == res_payload


# ノート更新 正常系
@pytest.mark.parametrize(('req_payload', 'will_update_note'), (
    ({'id': 1, 'sentence': '変更された観察'}, {'id': 1, 'author_id': 1, 'root_note_id': 1,'created': '2019-01-01 00:00:00', 'kind': 1, 'sentence': '変更された観察'}),
))
def test_update(app, client, req_payload, will_update_note):
    response = client.put('/notes',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload)
    )

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']

    update_response = client.put('/notes',
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(access_token)},
        data = json.dumps(req_payload),
    )

    assert update_response.status_code == 204

    with app.app_context():
        updated_note = Note.query.filter(Note.id == json.loads(json.dumps(req_payload))['id']).one()

        assert updated_note.sentence == will_update_note['sentence']
        assert updated_note.created == datetime.strptime(will_update_note['created'], '%Y-%m-%d %H:%M:%S')
        assert updated_note.updated > datetime.strptime(will_update_note['created'], '%Y-%m-%d %H:%M:%S')


# ノート削除 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    ({'id': ''}, {'message': 'Id is required.'}),
    ({'id': 6}, {'message': 'Note not found.'}), # 他人のノート
    ({'id': 12}, {'message': 'Note not found.'}), # 存在しない
))
def test_update_validate_input(client, req_payload, res_payload):
    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']
    delete_response = client.delete('/notes',
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
    ({'id': 2}, [{'id': 1, 'author_id': 1, 'root_note_id': 1, 'created': datetime(2019, 1, 1, 0, 0), 'updated': datetime(2019, 1, 1, 0, 0), 'kind': 1, 'sentence': '観察'}]),
))
def test_update_validate_input(app, client, req_payload, will_remain_note):
    response = client.delete('/notes',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload)
    )

    assert response.status_code == 401
    assert json.loads(response.data) == {'message': 'Missing Authorization Header'}

    login_response = client.post('/auth/login',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps({'username': 'test', 'password': 'test'}),
    )

    access_token = json.loads(login_response.data)['access_token']

    delete_response = client.delete('/notes',
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(access_token)},
        data = json.dumps(req_payload),
    )

    assert delete_response.status_code == 204

    with app.app_context():
        remained_note = Note.query.filter(Note.root_note_id == 1).all()

        if not remained_note:
            assert remained_note == will_remain_note
        else:
            assert remained_note[0].as_dict() == will_remain_note[0]
