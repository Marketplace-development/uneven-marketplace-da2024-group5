# app/routes.py

from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User, Listing, Transaction, Review, Notification
from supabase import create_client
from .config import Config
from flask import jsonify, request
"""
request geeft je toegang tot inkomende HTTP-verzoeken die door een gebruiker naar je server worden gestuurd.
Hiermee kun je gegevens ophalen die door een gebruiker naar je route zijn verzonden, bijvoorbeeld bestanden, formulierdata, of queryparameters.
"""
main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])  # Haal user info op via user_id
        listings = Listing.query.filter(Listing.user_id != user.user_id).all()  # Fetch listings for logged-in user
        return render_template('index.html', username=user.username, listings=listings)
    # If not logged in, show all listings
    listings = Listing.query.all()
    return render_template('index.html', username=None, listings=listings)

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
            flash('Username already registered. You will be redirected to login.', 'register')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already registered. You will be redirected to login.', 'register')
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
        
        flash('User not found. Would you like to <a href="/register">register</a>?', 'error')
        return render_template('login.html')

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


from werkzeug.utils import secure_filename
import os

@main.route('/add-listing', methods=['GET', 'POST'])
def add_listing():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        try:
            # Collect form data
            listing_name = request.form.get('listing_name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price', '').strip()
            file = request.files.get('file')

            # Validate form inputs
            if not listing_name or not description or not price:
                flash("All fields are required (name, description, price).", "error")
                return redirect(request.url)
            
            if not file:
                flash("A file is required.", "error")
                return redirect(request.url)

            try:
                price = float(price)  # Convert price to a float
            except ValueError:
                flash("Price must be a valid number.", "error")
                return redirect(request.url)

            # Secure the file name
            filename = secure_filename(file.filename)

            # Upload the file to Supabase
            response = supabase.storage.from_("pdfs").upload(filename, file.stream.read())

            # Handle the response
            if hasattr(response, "raw_response") and response.raw_response.status_code != 200:
                flash(f"Error uploading file to Supabase: {response.raw_response.text}", "error")
                return redirect(request.url)

            # Get the public URL of the file
            file_url = f"{supabase_url}/storage/v1/object/public/pdfs/{filename}"

            # Save listing details to the database
            new_listing = Listing(
                listing_name=listing_name,
                description=description,
                price_listing=price,
                url=file_url,  # Save the file URL
                user_id=session['user_id']
            )
            db.session.add(new_listing)  # Add the listing to the session
            db.session.commit()  # Commit the changes to the database

            flash("Listing added successfully.", "success")
            return redirect(url_for('main.listings'))

        except Exception as e:
            db.session.rollback()  # Roll back any database changes if an error occurs
            flash(f"An error occurred while adding the listing: {str(e)}", "error")
            return redirect(request.url)

    return render_template('add_listing.html')



@main.route('/listings')
def listings():
    all_listings = Listing.query.all()
    return render_template('listings.html', listings=all_listings)

@main.route('/my-purchased-listings')
def my_purchased_listings():
    if 'user_id' not in session:
        flash('You need to log in to access your purchased listings.', 'warning')
        return redirect(url_for('main.login'))

    # Fetch transactions linked to the current user
    user_transactions = Transaction.query.filter_by(user_id=session['user_id']).all()
    
    # Get the listings related to those transactions
    purchased_listings = [transaction.listing for transaction in user_transactions]

    return render_template('my_purchased_listings.html', listings=purchased_listings)

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


# Stel de Supabase-client in
supabase_url = Config.SUPABASE_URL
supabase_key = Config.SUPABASE_KEY
supabase = create_client(supabase_url, supabase_key)

@main.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)  # Secure the file name

    try:
        # Upload the file directly to Supabase
        response = supabase.storage.from_("pdfs").upload(filename, file.stream.read())
        if response.get("error"):
            return jsonify({'error': response.get("error").get("message")}), 500
        
        # Get the public URL of the file
        file_url = f"{supabase_url}/storage/v1/object/public/pdfs/{filename}"
        return jsonify({'file_url': file_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main.route('/wallet', methods=['GET'])
def wallet():
    if 'user_id' not in session:
        flash('You need to log in to view your wallet.', 'warning')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('wallet.html', wallet_balance=user.wallet_balance)

from decimal import Decimal

@main.route('/wallet/recharge', methods=['GET'])
def recharge_page():
    if 'user_id' not in session:
        flash('You need to log in to recharge your wallet.', 'walleterror')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('recharge_wallet.html', wallet_balance=user.wallet_balance)

@main.route('/wallet/recharge', methods=['POST'])
def recharge_wallet():
    if 'user_id' not in session:
        flash('You need to log in to recharge your wallet.', 'walleterror')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    amount = request.form.get('amount', type=float)
    
    if not amount:
        flash('Invalid amount.', 'walleterror')
        return redirect(url_for('main.recharge_page'))
    
    if amount <= 0:
        flash('Invalid amount.', 'walleterror')
        return redirect(url_for('main.recharge_page'))

    user.wallet_balance += Decimal(str(amount))
    db.session.commit()
    flash('Wallet recharged successfully!', 'walletsuccess')
    return redirect(url_for('main.recharge_page'))

#i hate my life because this doesn't work
'''
@main.route('/update-profile-pic', methods=['POST'])
def update_profile_pic():
    if 'user_id' not in session:
        flash('You need to log in to update your profile picture.', 'error')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    profile_pic_url = request.form.get('profile_pic_url', '/static/images/male default pic.jpg')
    user.profile_pic = profile_pic_url
    db.session.commit()
    flash('Profile picture updated successfully.', 'success')
    return redirect(url_for('main.account'))

'''
