from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from werkzeug.exceptions import abort
from datetime import datetime
from api.db import db
from api.model import User, Note
from sqlalchemy import asc, desc

bp = Blueprint('note', __name__)


@bp.route('/', methods=['GET'])
@jwt_required
def index():
    root_note_id :int = request.args.get('root')
    kind :int = request.args.get('kind')

    if root_note_id:
        notes = Note.query.filter(Note.root_note_id == root_note_id,
                                  Note.author_id == get_current_user().id)\
                          .order_by(asc(Note.kind))\
                          .all()
    elif kind:
        notes = Note.query.filter(Note.kind == 1,
                                  Note.author_id == get_current_user().id)\
                          .order_by(desc(Note.updated))\
                          .all()
    else:
        notes = Note.query.filter(Note.author_id == get_current_user().id)\
                          .order_by(asc(Note.id))\
                          .all()

    ret = [note.as_dict() for note in notes]

    return jsonify({
        'notes': ret
    }), 200


@bp.route('/', methods=['POST'])
@jwt_required
def create():
    root_note_id = request.get_json().get('root_note_id')
    kind = request.get_json().get('kind')
    sentence = request.get_json().get('sentence')
    message = None

    if not kind:
        message = 'Kind is required.'
    elif not sentence:
        message = 'Sentence is required.'
    elif root_note_id and Note.query.filter(Note.root_note_id == root_note_id,
                                            Note.kind == kind)\
                                    .first() is not None:
        message = 'Not related note.'
    elif root_note_id and Note.query.filter(Note.root_note_id == root_note_id,
                                            Note.author_id == get_current_user().id,
                                            Note.kind == kind - 1)\
                                    .first() is None:
        message = 'Not related note.'


    if message is None:
        note = Note(get_current_user().id, root_note_id, None, None, kind, sentence)
        db.session.add(note)
        db.session.commit()
        inserted_note = Note.query.filter(Note.author_id == get_current_user().id)\
                                  .order_by(desc(Note.id))\
                                  .first()

        if root_note_id is None:
            note.root_note_id = inserted_note.id
            db.session.commit()

        return jsonify({
            'id': inserted_note.id
        }), 201

    return jsonify({
        'message': message
    }), 400


@bp.route('/', methods=['PUT'])
@jwt_required
def update():
    id = request.get_json().get('id')
    sentence = request.get_json().get('sentence')
    message = None

    if not id:
        message = 'Id is required.'
    elif not sentence:
        message = 'Sentence is required.'
    elif Note.query.filter(Note.id == id,
                           Note.author_id == get_current_user().id)\
                   .first() is None:
        message = 'Note not found.'

    if message is None:
        note = Note.query.filter(Note.id == id,
                                 Note.author_id == get_current_user().id)\
                         .first()
        note.sentence = sentence
        note.updated = datetime.now()
        db.session.commit()

        return jsonify(), 204

    return jsonify({
        'message': message
    }), 400


@bp.route('/', methods=['DELETE'])
@jwt_required
def destroy():
    id = request.get_json().get('id')
    message = None

    if not id:
        message = 'Id is required.'

    note = Note.query.filter(Note.id == id,
                             Note.author_id == get_current_user().id)\
                     .first()

    if note is None:
        message = 'Note not found.'

    if message is None:
        Note.query.filter(Note.root_note_id == id,
                          Note.author_id == get_current_user().id,
                          Note.kind >= note.kind)\
                  .delete()
        db.session.commit()

        return jsonify(), 204

    return jsonify({
        'message': message
    }), 400
