from flask import (
    Blueprint, request, session, jsonify
)
from werkzeug.exceptions import abort
from datetime import datetime

from api.db import get_db
from api.auth import login_required

bp = Blueprint('note', __name__)


@bp.route('/', methods=['GET'])
@login_required
def index():
    root_note_id :int = request.args.get('root')
    kind :int = request.args.get('kind')
    notes = []

    db = get_db()
    if root_note_id:
        notes = db.execute(
            'SELECT n.id, author_id, root_note_id, created, updated, kind, sentence'
            ' FROM note n JOIN user u ON n.author_id = u.id'
            ' WHERE root_note_id = ? ORDER BY kind ASC',
            (root_note_id)
        ).fetchall()
    elif kind:
        notes = db.execute(
            'SELECT n.id, author_id, root_note_id, created, updated, kind, sentence'
            ' FROM note n JOIN user u ON n.author_id = u.id'
            ' WHERE kind = ? ORDER BY updated DESC',
            (kind)
        ).fetchall()
    else:
        notes = db.execute(
            'SELECT n.id, author_id, root_note_id, created, updated, kind, sentence'
            ' FROM note n JOIN user u ON n.author_id = u.id'
        ).fetchall()

    return jsonify({
        'notes': notes
    }), 200


@bp.route('/', methods=['POST'])
@login_required
def create():
    author_id = request.get_json().get('author_id')
    root_note_id = request.get_json().get('root_note_id')
    kind = request.get_json().get('kind')
    sentence = request.get_json().get('sentence')
    db = get_db()
    message = None

    if not author_id:
        message = 'author_id is required.'
    elif not kind:
        message = 'kind is required.'
    elif not sentence:
        message = 'sentence is required.'

    if message is None:
        db.execute(
            'INSERT INTO note (author_id, root_note_id, kind, sentence) VALUES (?, ?, ?, ?)',
            (author_id, root_note_id, kind, sentence)
        )
        inserted_note = db.execute(
            'SELECT id FROM note WHERE author_id = ? ORDER BY created DESC',
            (author_id,)
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
@login_required
def update():
    id = request.get_json().get('id')
    sentence = request.get_json().get('sentence')
    db = get_db()
    message = None

    if not id:
        message = 'id is required.'
    elif not sentence:
        message = 'sentence is required.'

    if message is None:
        db.execute(
            'UPDATE note SET sentence = ?, updated = ? WHERE id = ?',
            (sentence, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id)
        )
        db.commit()

        return jsonify(), 204

    return jsonify({
        'message': message
    }), 400


@bp.route('/', methods=['DELETE'])
@login_required
def destroy():
    id = request.get_json().get('id')
    db = get_db()
    message = None

    if not id:
        message = 'id is required.'

    deleted_note = db.execute(
        'SELECT * FROM note WHERE id = ?', (id,)
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
