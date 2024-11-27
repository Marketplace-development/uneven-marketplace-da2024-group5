# app/routes.py

from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, User, Listing, Provider, Customer, Transaction, Review, Notification

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id']) # haalt alle info op van user aan de hand van user_id
        listings = Listing.query.filter_by(provider_id=User.user_id).all()  # Fetch listings for logged-in user
        return render_template('index.html', username=user.username, listings=listings)
    return render_template('index.html', username=None)

#Nee, alle informatie over de gebruiker wordt niet opgeslagen in de sessie. Wat jouw code doet, is alleen de primary key (user_id) opslaan in de sessie. 
#De sessie wordt hier gebruikt als een manier om een referentie te bewaren naar de ingelogde gebruiker. 
# Wanneer je vervolgens informatie over de gebruiker nodig hebt, wordt deze opgehaald uit de database aan de hand van die user_id. 
# Dit bespaart geheugen en maakt de applicatie efficiënter.

@main.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.index'))  # Gebruiker is al ingelogd
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        date_of_birth = request.form['date_of_birth']
        phone_number = request.form['phone_number']
        
        # Controleer of de username of email al bestaan
        if User.query.filter_by(username=username).first() is not None:
            return 'Username already registered'
        if User.query.filter_by(email=email).first() is not None:
            return 'Email already registered'
        
        # Maak een nieuwe gebruiker aan
        new_user = User(
            username=username,
            email=email,
            date_of_birth=date_of_birth,
            phone_number=phone_number
        )
        
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.user_id  # Gebruik user_id om sessie op te slaan
        return redirect(url_for('main.index'))

    return render_template('register.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))  # Gebruiker is al ingelogd

    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        
        if user:
            session['user_id'] = user.user_id  # Bewaar user_id in de sessie
            return redirect(url_for('main.index'))
        return 'User not found'
    return render_template('login.html')


@main.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('main.index'))

@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        listing_name = request.form['listing_name']
        price = float(request.form['price'])
        new_listing = Listing(listing_name=listing_name, price=price, user_id=session['user_id'])
        db.session.add(new_listing)
        db.session.commit()
        return redirect(url_for('main.listings'))

    return render_template('add_listing.html')

@main.route('/listings')
def listings():
    all_listings = Listing.query.all()
    return render_template('listings.html', listings=all_listings)

@main.route('/edit-listing/<int:listing_id>', methods=['GET', 'POST'])
def edit_listing(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if listing.user_id != session['user_id']:
        return 'Unauthorized', 403  # Alleen de eigenaar mag bewerken
    
    if request.method == 'POST':
        listing.listing_name = request.form['listing_name']
        listing.price = float(request.form['price'])
        db.session.commit()
        return redirect(url_for('main.listings'))
    
    return render_template('edit_listing.html', listing=listing)
