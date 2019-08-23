import pytest
import json
import datetime
import time
from flask import Flask, g, session
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token, jwt_required,
    jwt_refresh_token_required, get_jwt_identity, decode_token
)
from api.db import get_db


# ユーザ登録 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    ({'username': '', 'password': ''}, {'message': 'Username is required.'}),
    ({'username': 'user', 'password': ''}, {'message': 'Password is required.'}),
    ({'username': 'test', 'password': 'password'}, {'message': 'User test is already registered.'}),
))
def test_register_validate_input(client, req_payload, res_payload):
    response = client.post('/auth/register',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload),
    )
    assert response.status_code == 400
    assert json.loads(response.data) == res_payload


# ユーザ登録 正常系
@pytest.mark.parametrize(('req_payload'), (
    ({'username': 'user', 'password': 'password'}),
))
def test_register(client, app, req_payload):
    response = client.post('/auth/register',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload),
    )
    assert response.status_code == 201
    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM user WHERE username = 'user'",
        ).fetchone() is not None


# ログイン 異常系
@pytest.mark.parametrize(('req_payload', 'res_payload'), (
    ({'username': '', 'password': ''}, {'message': 'Username is required.'}),
    ({'username': 'user', 'password': ''}, {'message': 'Password is required.'}),
))
def test_login_validate_input(client, req_payload, res_payload):
    response = client.post('/auth/register',
        headers = {'Content-Type': 'application/json'},
        data = json.dumps(req_payload),
    )
    assert response.status_code == 400
    assert json.loads(response.data) == res_payload


# ログイン 正常系
@pytest.mark.parametrize(('req_payload'), (
    ({'username': 'test', 'password': 'test'}),
))
def test_login(app, client, req_payload):
    with app.app_context():
        jwt = JWTManager(app)

        access_token = create_access_token(req_payload['username'])
        refresh_token = create_refresh_token(req_payload['username'])

        response = client.post('/auth/login',
            headers = {'Content-Type': 'application/json'},
            data = json.dumps(req_payload),
        )

        res_access_token = json.loads(response.data)['access_token']
        res_refresh_token = json.loads(response.data)['refresh_token']

        assert response.status_code == 200
        assert decode_token(res_access_token)['identity'] == req_payload['username']
        assert decode_token(res_refresh_token)['identity'] == req_payload['username']


# リフレッシュトークン
@pytest.mark.parametrize(('req_payload'), (
    ({'username': 'test', 'password': 'test'}),
))
def test_refresh(app, client, req_payload):
    with app.app_context():
        # テスト用にアクセストークンの有効期限を1秒に設定する
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(seconds=1)
        jwt = JWTManager(app)

        # 認証確認用の一時的なURI
        @app.route('/protected', methods=['GET'])
        @jwt_required
        def access_protected():
            return 'ok'

        access_token = create_access_token(req_payload['username'])
        refresh_token = create_refresh_token(req_payload['username'])

        response = client.get('/protected',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
        )
        assert response.status_code == 200

        time.sleep(2)

        response = client.get('/protected',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(access_token)},
        )
        assert response.status_code == 401

        refresh_response = client.post('/auth/refresh',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(refresh_token)},
        )

        refresh_access_token = json.loads(refresh_response.data)['access_token']
        response = client.get('/protected',
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {}'.format(refresh_access_token)},
        )
        assert response.status_code == 200
