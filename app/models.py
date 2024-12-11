from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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
    preferences = db.Column(db.JSON, default=lambda: {"Adventure": 0, "Nature": 0, "Culture": 0, "Sport & Active": 0, "Family": 0,
        "Wellness & Relaxation": 0, "Romantic": 0, "City Trips": 0,
        "Festivals & Events": 0, "Budget & Backpacking": 0, "Roadtrip & Multi-Destination": 0})
    password = db.Column(db.String(255), nullable=True)

    #Helper method to set password hash
    def set_password(self,password):
        self.password = generate_password_hash(password)

    #Helper method to check password
    def check_password(self,password):
        return check_password_hash(self.password,password)


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
    picture = db.Column(db.String, nullable=True)



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

   