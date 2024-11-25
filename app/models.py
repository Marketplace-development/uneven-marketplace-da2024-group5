from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    phonenumber = db.Column(db.String(15), nullable=True)
    create_date = db.Column(db.DateTime, server_default=db.func.now())

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True, db.ForeignKey('user.id')) #foutmelding bij foreign key
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, db.ForeignKey('user.id'))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    price_transaction = db.Column(db.Numeric(10, 2))
    status = db.Column(db.Boolean, default=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))

class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    content = db.Column(db.Text, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

class Notification(db.Model):
    notification_id = db.Column(db.Integer, primary_key=True)
    viewed = db.Column(db.Boolean, default=False)
    time_of_notification = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))