import pytest
import json
from flask import g, session
from api.db import get_db


# ユーザ登録 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    (json.dumps({'username': '', 'password': ''}), {'message': 'Username is required.'}),
    (json.dumps({'username': 'user', 'password': ''}), {'message': 'Password is required.'}),
    (json.dumps({'username': 'test', 'password': 'password'}), {'message': 'User test is already registered.'}),
))
def test_register_validate_input(client, req_payload, res_payload):
    response = client.post('/auth/register',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 400
    assert json.loads(response.data) == res_payload


# ユーザ登録 正常系
@pytest.mark.parametrize(('req_payload'), (
    (json.dumps({'username': 'user', 'password': 'password'})),
))
def test_register(client, app, req_payload):
    response = client.post('/auth/register',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 201
    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'user'",
        ).fetchone() is not None


# ログイン 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    (json.dumps({'username': 'user', 'password': 'test'}), {'message': 'Incorrect username.'}),
    (json.dumps({'username': 'test', 'password': 'password'}), {'message': 'Incorrect password.'}),
))
def test_login_validate_input(client, req_payload, res_payload):
    response = client.post('/auth/login',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 401
    assert json.loads(response.data) == res_payload


# ログイン/ログアウト 正常系
@pytest.mark.parametrize(('req_payload'), (
    (json.dumps({'username': 'test', 'password': 'test'})),
))
def test_login_and_logout(client, app, req_payload):
    response = client.post('/auth/login',
        data = req_payload,
        content_type = 'application/json'
    )
    assert response.status_code == 204
    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'

    response = client.get('/auth/logout')
    assert response.status_code == 204
    with client:
        client.get('/')
        assert 'user_id' not in session
