from flask import Blueprint, g, request, session, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from werkzeug.exceptions import abort
from datetime import datetime
from api.db import get_db

bp = Blueprint('note', __name__)


@bp.route('/', methods=['GET'])
@jwt_required
def index():
    root_note_id :int = request.args.get('root')
    kind :int = request.args.get('kind')
    notes = []
    db = get_db()

    select_statement = 'SELECT n.id, author_id, root_note_id, created, updated, kind, sentence'\
                       ' FROM note n JOIN user u ON n.author_id = u.id'

    if root_note_id:
        notes = db.execute(
            select_statement
            + ' WHERE root_note_id = ? AND author_id = ? ORDER BY kind ASC',
            (root_note_id, get_current_user()['id'])
        ).fetchall()
    elif kind:
        notes = db.execute(
            select_statement
            + ' WHERE kind = ? AND author_id = ? ORDER BY updated DESC',
            (kind, get_current_user()['id'])
        ).fetchall()
    else:
        notes = db.execute(
            select_statement
            + ' WHERE author_id = ? ORDER BY n.id ASC',
            (get_current_user()['id'],)
        ).fetchall()

    return jsonify({
        'notes': notes
    }), 200


@bp.route('/', methods=['POST'])
@jwt_required
def create():
    root_note_id = request.get_json().get('root_note_id')
    kind = request.get_json().get('kind')
    sentence = request.get_json().get('sentence')
    db = get_db()
    message = None

    if not kind:
        message = 'Kind is required.'
    elif not sentence:
        message = 'Sentence is required.'
    elif root_note_id and db.execute(
        'SELECT * FROM note '
        ' WHERE root_note_id = ? AND kind = ?',
        (root_note_id, kind)
    ).fetchone() is not None:
        message = 'Not related note.'
    elif root_note_id and db.execute(
        'SELECT * FROM note '
        ' WHERE id = ? AND author_id = ? AND kind = ?',
        (root_note_id, get_current_user()['id'], kind - 1)
    ).fetchone() is None:
        message = 'Not related note.'

    if message is None:
        db.execute(
            'INSERT INTO note (author_id, root_note_id, kind, sentence) VALUES (?, ?, ?, ?)',
            (get_current_user()['id'], root_note_id, kind, sentence)
        )
        inserted_note = db.execute(
            'SELECT id FROM note WHERE author_id = ? ORDER BY created DESC',
            (get_current_user()['id'],)
        ).fetchone()

        if root_note_id is None:
            db.execute(
                'UPDATE note SET root_note_id = ? WHERE id = ?',
                (inserted_note['id'], inserted_note['id'])
            )

        db.commit()

        return jsonify({
            'id': inserted_note['id']
        }), 201

    return jsonify({
        'message': message
    }), 400


@bp.route('/', methods=['PUT'])
@jwt_required
def update():
    id = request.get_json().get('id')
    sentence = request.get_json().get('sentence')
    db = get_db()
    message = None

    if not id:
        message = 'Id is required.'
    elif not sentence:
        message = 'Sentence is required.'
    elif db.execute(
        'SELECT * FROM note '
        ' WHERE id = ? AND author_id = ?',
        (id, get_current_user()['id'],)
    ).fetchone() is None:
        message = 'Note not found.'

    if message is None:
        db.execute(
            'UPDATE note SET sentence = ?, updated = ? WHERE id = ? AND author_id = ?',
            (sentence, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id, get_current_user()['id'])
        )
        db.commit()

        return jsonify(), 204

    return jsonify({
        'message': message
    }), 400


@bp.route('/', methods=['DELETE'])
@jwt_required
def destroy():
    id = request.get_json().get('id')
    db = get_db()
    message = None

    if not id:
        message = 'Id is required.'
    elif db.execute(
        'SELECT * FROM note '
        ' WHERE id = ? AND author_id = ?',
        (id, get_current_user()['id'])
    ).fetchone() is None:
        message = 'Note not found.'

    deleted_note = db.execute(
        'SELECT * FROM note WHERE id = ? AND author_id = ?',
        (id, get_current_user()['id'])
    ).fetchone()

    if message is None:
        db.execute(
            'DELETE FROM note WHERE root_note_id = ? AND kind >= ?',
            (deleted_note['root_note_id'], deleted_note['kind'])
        )
        db.commit()

        return jsonify(), 204

    return jsonify({
        'message': message
    }), 400
