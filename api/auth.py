import functools

from flask import (
    Blueprint, g, request, session, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash

from api.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


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
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        message = 'Incorrect username.'
    elif not check_password_hash(user['password'], password):
        message = 'Incorrect password.'

    if message is None:
        session.clear()
        session['user_id'] = user['id']
        return jsonify(), 204

    return jsonify({
        'message': message
    }), 401


@bp.route('/logout')
def logout():
    session.clear()

    return jsonify(), 204


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()


def login_required(view):
    message = None
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return jsonify({
                'message': 'login required.'
            }), 401

        return view(**kwargs)

    return wrapped_view
