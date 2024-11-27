# app/routes.py

from flask import Blueprint, request, redirect, url_for, render_template, session, flash
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
            flash('Username already registered. You will be redirected to login.', 'error')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already registered. You will be redirected to login.', 'error')
            return redirect(url_for('main.register'))
        
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
        
        # Gebruiker bestaat niet: toon melding en een knop naar registratie
        flash('User not found. Would you like to register?', 'error')
        return redirect(url_for('main.login'))  # Herlaad login-pagina met melding

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

#This route will allow users to view more details about a specific listing and proceed with a purchase if they want
@main.route('/listing/<int:listing_id>', methods=['GET', 'POST'])
def view_listing(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    # Handle purchase (this is just a placeholder for actual transaction logic)
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        # Simulate a transaction (you can add actual transaction logic here)
        transaction = Transaction(
            buyer_id=session['user_id'],
            listing_id=listing_id,
            amount=listing.price
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Purchase successful!', 'success')
        return redirect(url_for('main.listings'))
    
    # Get reviews for the listing
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    return render_template('view_listing.html', listing=listing, reviews=reviews)

#Users should be able to leave reviews for listings they have purchased (or perhaps just viewed, depending on your business logic).
@main.route('/add-review/<int:listing_id>', methods=['GET', 'POST'])
def add_review(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    if request.method == 'POST':
        review_text = request.form['review_text']
        rating = int(request.form['rating'])
        
        # Create a new review
        new_review = Review(
            user_id=session['user_id'],
            listing_id=listing_id,
            review_text=review_text,
            rating=rating
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Review added successfully!', 'success')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    return render_template('add_review.html', listing=listing)

#To allow users to view reviews of a listing before purchasing, you can display all the reviews related to the listing.
@main.route('/reviews/<int:listing_id>')
def view_reviews(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    return render_template('view_reviews.html', listing=listing, reviews=reviews)

#Allow users to search for listings based on certain criteria
@main.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query')
    if query:
        listings = Listing.query.filter(Listing.listing_name.ilike(f'%{query}%')).all()
    else:
        listings = Listing.query.all()
    return render_template('listings.html', listings=listings)

#Users should be able to filter listings by criteria like price or category
@main.route('/filter', methods=['GET'])
def filter_listings():
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    category = request.args.get('category')

    query = Listing.query

    if min_price:
        query = query.filter(Listing.price >= min_price)
    if max_price:
        query = query.filter(Listing.price <= max_price)
    if category:
        query = query.filter(Listing.category.ilike(f'%{category}%'))

    listings = query.all()
    return render_template('listings.html', listings=listings)

#You can create a page where users can view their transaction history (i.e., the listings they have bought).
@main.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    transactions = Transaction.query.filter_by(buyer_id=session['user_id']).all()
    return render_template('transactions.html', transactions=transactions)
