from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'  # Let op hoofdlettergebruik
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    create_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaties
    providers = db.relationship('Provider', backref='User', lazy=True)
    customers = db.relationship('Customer', backref='User', lazy=True)
    listings = db.relationship('Listing', backref='ProviderUser', lazy=True)

class Listing(db.Model):
    __tablename__ = 'Listing'  # Let op hoofdlettergebruik
    id = db.Column(db.Integer, primary_key=True)
    listing_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    provider_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    pdfUrl = db.Column(db.String(255), nullable=False)

    # Relaties
    transactions = db.relationship('Transaction', backref='Listing', lazy=True)

class Provider(db.Model):
    __tablename__ = 'Provider'
    id = db.Column(db.Integer, primary_key=True)
    unbound_local_errorser_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'Transaction'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    price_transaction = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Boolean, default=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('Listing.id'), nullable=False)

class Review(db.Model):
    __tablename__ = 'Review'
    review_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)

class Notification(db.Model):
    __tablename__ = 'Notification'
    notification_id = db.Column(db.Integer, primary_key=True)
    viewed = db.Column(db.Boolean, default=False)
    time_of_notification = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
