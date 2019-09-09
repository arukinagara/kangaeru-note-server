import functools
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_refresh_token_required,
    get_jwt_identity
)
from werkzeug.security import check_password_hash, generate_password_hash
from api.db import db_session
from api.model import User

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['POST'])
def register():
    username = request.get_json().get('username')
    password = request.get_json().get('password')
    message = None

    if not username:
        message = 'Username is required.'
    elif not password:
        message = 'Password is required.'
    elif User.query.filter(User.username == username).first() is not None:
        message = 'User {} is already registered.'.format(username)

    if message is None:
        user = User(username, generate_password_hash(password))
        db_session.add(user)
        db_session.commit()
        inserted_user = User.query.filter(User.username == username).first()

        return jsonify({
            'id': inserted_user.id
        }), 201

    return jsonify({
        'message': message
    }), 400


@bp.route('/login', methods=['POST'])
def login():
    username = request.get_json().get('username')
    password = request.get_json().get('password')
    message = None

    user = User.query.filter(User.username == username).first()

    if user is None:
        message = 'Incorrect username or password.'
    elif not check_password_hash(user.password, password):
        message = 'Incorrect username or password.'

    if message is None:
        # flask_jwt_extendedを使ってユーザ名からアクセス/リフレッシュトークンを生成する
        ret = {
            'access_token': create_access_token(identity = username),
            'refresh_token': create_refresh_token(identity = username)
        }
        return jsonify(ret), 200

    return jsonify({
        'message': message
    }), 401


# アクセストークンが切れた場合、リフレッシュトークンでこのURIにアクセスし、アクセストークンを更新する
@bp.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    username = get_jwt_identity()
    access_token = create_access_token(identity = username)
    return jsonify(access_token = access_token), 200
