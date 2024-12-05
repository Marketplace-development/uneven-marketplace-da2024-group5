from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Pas op van hoofdletters!
class User(db.Model):
    __tablename__ = 'User'  # Let op hoofdlettergebruik
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    #profile_pic = db.Column(db.String(255), nullable = True, default='static/images/default.jpg') #default pic.
    create_date = db.Column(db.DateTime, default=datetime.utcnow)
    wallet_balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)  # Add this line
    preferences = db.Column(db.JSON, default=lambda: {"natuur": 0, "cultuur": 0, "avontuur": 0})


    # Relaties
    listings = db.relationship('Listing', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)



class Listing(db.Model):
    __tablename__ = 'Listing'  # Let op hoofdlettergebruik
    listing_id = db.Column(db.Integer, primary_key=True)
    listing_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price_listing = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    url = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    place = db.Column(db.String(100), nullable=True)  # New field for place as a string
    listing_categorie = db.Column(db.String(255))


    # Relaties
    transactions = db.relationship('Transaction', backref='listing', lazy=True)
    reviews = db.relationship('Review', backref='listing', lazy=True)
    notifications = db.relationship('Notification', backref='listing', lazy=True)
    likes = db.relationship('Like', backref='listing', lazy=True)



class Transaction(db.Model):
    __tablename__ = 'Transaction'
    transaction_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    price_transaction = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Boolean, default=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('Listing.listing_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)


class Review(db.Model):
    __tablename__ = 'Review'
    review_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('Listing.listing_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    rating = db.Column(db.Integer, nullable = False)


class Notification(db.Model):
    __tablename__ = 'Notification'
    notification_id = db.Column(db.Integer, primary_key=True)
    viewed = db.Column(db.Boolean, default=False)
    time_of_notification = db.Column(db.DateTime, default=datetime.utcnow)
    listing_id = db.Column(db.Integer, db.ForeignKey('Listing.listing_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)


class Like(db.Model):
    __tablename__ = 'Like'
    like_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('Listing.listing_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

   