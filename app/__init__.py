# app/__init__.py
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config
from .models import db, User, Transaction

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
                wallet_balance = user.wallet_balance if user.wallet_balance is not None else 0
                return {'username': user.username, 'wallet_balance': wallet_balance}
        return {'username': None, 'wallet_balance': 0}


    @app.context_processor
    def utility_functions():
        def transaction_exists(user_id, listing_id):
            return Transaction.query.filter_by(user_id=user_id, listing_id=listing_id).first() is not None
        return dict(transaction_exists=transaction_exists)


    return app
