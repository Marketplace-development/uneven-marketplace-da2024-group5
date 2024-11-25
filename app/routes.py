# app/routes.py

from flask import Blueprint, request, redirect, url_for, render_template, session
from .models import db, User, Listing

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id']) # haalt alle info op van user aan de hand van user_id
        listings = Listing.query.filter_by(user_id=user.id).all()  # Fetch listings for logged-in user
        return render_template('index.html', username=user.username, listings=listings)
    return render_template('index.html', username=None)

#Nee, alle informatie over de gebruiker wordt niet opgeslagen in de sessie. Wat jouw code doet, is alleen de primary key (user_id) opslaan in de sessie. 
#De sessie wordt hier gebruikt als een manier om een referentie te bewaren naar de ingelogde gebruiker. 
# Wanneer je vervolgens informatie over de gebruiker nodig hebt, wordt deze opgehaald uit de database aan de hand van die user_id. 
# Dit bespaart geheugen en maakt de applicatie efficiënter.

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first() is None:
            new_user = User(username=username)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect(url_for('main.index'))
        return 'Username already registered'
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
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

@main.route('/delete-listing/<int:listing_id>', methods=['POST'])
def delete_listing(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if listing.user_id != session['user_id']:
        return 'Unauthorized', 403
    
    db.session.delete(listing)
    db.session.commit()
    return redirect(url_for('main.listings'))

@main.route('/start-transaction/<int:listing_id>', methods=['POST'])
def start_transaction(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if not listing:
        return 'Listing not found', 404
    
    new_transaction = Transaction(
        listing_id=listing_id,
        buyer_id=session['user_id'],
        status='INITIATED'
    )
    db.session.add(new_transaction)
    db.session.commit()
    return redirect(url_for('main.transaction_history'))

@main.route('/add-review/<int:listing_id>', methods=['GET', 'POST'])
def add_review(listing_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        review = Review(
            user_id=session['user_id'],
            listing_id=listing_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        return redirect(url_for('main.listing_details', listing_id=listing_id))
    
    return render_template('add_review.html', listing_id=listing_id)

@main.route('/reviews/<int:listing_id>')
def reviews(listing_id):
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    return render_template('reviews.html', reviews=reviews)

@main.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get(user_id)
    listings = Listing.query.filter_by(user_id=user_id).all()
    transactions = Transaction.query.filter_by(buyer_id=user_id).all()
    return render_template('profile.html', user=user, listings=listings, transactions=transactions)


@main.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = Listing.query.filter(
        Listing.listing_name.ilike(f'%{query}%') | Listing.description.ilike(f'%{query}%')
    ).all()
    return render_template('search_results.html', results=results)



@main.route('/complete-transaction/<int:transaction_id>', methods=['POST'])
def complete_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    transaction = Transaction.query.get(transaction_id)
    if transaction.buyer_id != session['user_id']:
        return 'Unauthorized', 403
    
    transaction.status = True
    db.session.commit()
    return redirect(url_for('main.transaction_history'))



@main.route('/cancel-transaction/<int:transaction_id>', methods=['POST'])
def cancel_transaction(transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    transaction = Transaction.query.get(transaction_id)
    if transaction.buyer_id != session['user_id'] and transaction.listing.user_id != session['user_id']:
        return 'Unauthorized', 403
    
    transaction.status = False
    db.session.commit()
    return redirect(url_for('main.transaction_history'))

@main.route('/category/<string:category_name>')
def category_listings(category_name): 
    listings = Listing.query.filter_by(category=category_name).all()
    return render_template('category_listings.html', category=category_name, listings=listings)

