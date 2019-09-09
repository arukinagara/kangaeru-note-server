import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from api.db import init_app, db_session
from api.model import User

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'api.sqlite'),
        # flask_jwt_extended用の定義
        JWT_SECRET_KEY='super-secret',
        JWT_ERROR_MESSAGE_KEY='message',
    )

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    # enable CORS
    CORS(app, resources={r'/*': {'origins': '*'}})

    # flask_jwt_extendedを初期化
    jwt = JWTManager(app)
    @jwt.user_loader_callback_loader
    def user_loader_callback(identity):
        current_user = User.query.filter(User.username == identity).first()
        return current_user

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # sanity check route
    @app.route('/hello', methods=['GET'])
    def hello():
        return jsonify('Hello, World!!')

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import note
    app.register_blueprint(note.bp)

    return app
