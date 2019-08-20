import functools

from flask import Flask, current_app, Blueprint, g, request, session, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from api.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# blueprint内でappを使用するための設定
app = Flask(__name__)
# 使用する時はwith句内で、current_appとして使う
with app.app_context():
    current_app.config['JWT_SECRET_KEY'] = 'super-secret'
    jwt = JWTManager(current_app)


@bp.route('/register', methods=['POST'])
def register():
    username = request.get_json().get('username')
    password = request.get_json().get('password')
    db = get_db()
    message = None

    if not username:
        message = 'Username is required.'
    elif not password:
        message = 'Password is required.'
    elif db.execute(
        'SELECT id FROM user WHERE username = ?', (username,)
    ).fetchone() is not None:
        message = 'User {} is already registered.'.format(username)

    if message is None:
        db.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        inserted_user = db.execute(
            'SELECT id FROM user WHERE username = ?',
            (username,)
        ).fetchone()
        db.commit()

        return jsonify({
            'id': inserted_user['id']
        }), 201

    return jsonify({
        'message': message
    }), 400


@bp.route('/login', methods=['POST'])
def login():
    username = request.get_json().get('username')
    password = request.get_json().get('password')
    db = get_db()
    message = None

    user = db.execute(
        'SELECT * FROM user WHERE username = ?',
        (username,)
    ).fetchone()

    if user is None:
        message = 'Incorrect username.'
    elif not check_password_hash(user['password'], password):
        message = 'Incorrect password.'

    if message is None:
        # flask_jwt_extendedを使ってユーザ名からアクセストークンを生成する
        access_token = create_access_token(identity = username)
        return jsonify(access_token = access_token), 200


@bp.route('/logout')
def logout():
    session.clear()

    return jsonify(), 204

# get_current_userがコールされると(ここではnote.pyで使用している)、以下のメソッドが呼ばれる
# identityはユーザ名で、ユーザオブジェウトが返却されるように作っている
@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE username = ?',
        (identity,)
    ).fetchone()

    return user
