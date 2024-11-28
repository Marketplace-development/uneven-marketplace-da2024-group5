# app/routes.py

from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User, Listing, Transaction, Review, Notification

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])  # Haal user info op via user_id
        listings = Listing.query.filter_by(user_id=User.user_id).all()  # Fetch listings for logged-in user
        return render_template('index.html', username=user.username, listings=listings)
    return render_template('index.html', username=None)

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
        
        flash('User not found. Would you like to register?', 'error')
        return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/account')
def account():
    if 'user_id' not in session:
        flash('You need to log in to access your account.', 'warning')
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    return render_template('account.html', user=user)

@main.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        # Verwijder de user_id uit de sessie
        session.pop('user_id', None)
        # Redirect naar de homepagina na succesvolle logout
        return redirect(url_for('main.index'))  # Verwijs naar de homepagina

    # Bij een GET-verzoek tonen we een bevestigingspagina
    return render_template('logout.html')  # Toon de logout-pagina met een boodschap


@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        listing_name = request.form['listing_name']
        price = float(request.form['price'])
        new_listing = Listing(listing_name=listing_name, price_listing=price, user_id=session['user_id'])
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
        listing.price_listing = float(request.form['price'])
        db.session.commit()
        return redirect(url_for('main.listings'))
    
    return render_template('edit_listing.html', listing=listing)

@main.route('/listing/<int:listing_id>', methods=['GET', 'POST'])
def view_listing(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        transaction = Transaction(user_id=session['user_id'], listing_id=listing_id,price_transaction=listing.price_listing)
        db.session.add(transaction)
        db.session.commit()
        flash('Purchase successful!', 'success')
        return redirect(url_for('main.listings'))
    
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    return render_template('view_listing.html', listing=listing, reviews=reviews)

@main.route('/add-review/<int:listing_id>', methods=['GET', 'POST'])
def add_review(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    if request.method == 'POST':
        content = request.form['review_text']
        new_review = Review( user_id=session['user_id'],listing_id=listing_id,content=content)
        db.session.add(new_review)
        db.session.commit()
        flash('Review added successfully!', 'success')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    return render_template('add_review.html', listing=listing)

@main.route('/reviews/<int:listing_id>')
def view_reviews(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    return render_template('view_reviews.html', listing=listing, reviews=reviews)

@main.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('query')
    if query:
        listings = Listing.query.filter(Listing.listing_name.ilike(f'%{query}%')).all()
    else:
        listings = Listing.query.all()
    return render_template('listings.html', listings=listings)

@main.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    user_transactions = Transaction.query.filter_by(user_id=session['user_id']).all()
    return render_template('transactions.html', transactions=user_transactions)

@main.route('/filter', methods=['GET'])
def filter_listings():
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    # Let op: de 'category'-kolom lijkt niet meer te bestaan in de huidige structuur,
    # dus we verwijderen die filteroptie. Laat het weten als je deze wilt toevoegen.

    query = Listing.query

    if min_price:
        query = query.filter(Listing.price_listing >= min_price)  # Aangepast naar 'price_listing'
    if max_price:
        query = query.filter(Listing.price_listing <= max_price)

    listings = query.all()
    return render_template('listings.html', listings=listings)


