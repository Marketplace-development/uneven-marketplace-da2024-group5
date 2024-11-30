# app/__init__.py
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .models import db, User

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .routes import main
        app.register_blueprint(main)
        
    # Adding the context processor to make `username` available globally
    @app.context_processor
    def inject_user():
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user:
                return {'username': user.username}
        return {'username': None}


    return app
