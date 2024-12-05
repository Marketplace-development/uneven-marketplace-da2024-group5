# app/routes.py

from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User, Listing, Transaction, Review, Notification, Like
from supabase import create_client, Client
from .config import Config
from flask import jsonify, request
import re
from flask import render_template, request, redirect, flash, session, url_for
from .models import db, User
"""
request geeft je toegang tot inkomende HTTP-verzoeken die door een gebruiker naar je server worden gestuurd.
Hiermee kun je gegevens ophalen die door een gebruiker naar je route zijn verzonden, bijvoorbeeld bestanden, formulierdata, of queryparameters.
"""
main = Blueprint('main', __name__)

@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])  # Haal user info op via user_id
        
        # Check of de gebruiker voorkeuren heeft ingesteld
        if user.preferences and any(user.preferences.values()):
            # Bepaal de voorkeur met de hoogste score
            top_preference = max(user.preferences, key=user.preferences.get)
            # Filter de listings op basis van deze voorkeur
            listings = Listing.query.filter(Listing.listing_categorie.contains(top_preference), Listing.user_id != user.user_id).all()
        else:
            # Haal listings op die niet van de gebruiker zijn als er geen voorkeuren zijn ingesteld
            listings = Listing.query.filter(Listing.user_id != user.user_id).all()
    else:
        # Als gebruiker niet is ingelogd, toon alle listings
        listings = Listing.query.all()

    # Voeg aantal likes toe en rond prijzen af
    for listing in listings:
        listing.price_listing = round(listing.price_listing, 2)
        listing.like_count = len(listing.likes)  # Tel aantal likes met de relatie

    return render_template('index.html', username=user.username if 'user_id' in session else None, listings=listings)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.index'))  # Gebruiker is al ingelogd
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        date_of_birth = request.form['date_of_birth']
        phone_number = request.form['phone_number']
        
        # Validatie van e-mail met accenten
        email_pattern = r"^[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç._%-]+@[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+\.[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+$"
        if not re.match(email_pattern, email):
            flash('Invalid email address. Please enter a valid email.', 'register')
            return redirect(url_for('main.register'))
        
        # Start met de basisvoorkeuren
        preferences = {"natuur": 0, "cultuur": 0, "avontuur": 0}

        # Update voorkeuren op basis van keuze in de eerste vraag
        preference_choice = request.form.get('preference')
        if preference_choice == "cultuur":
            preferences["cultuur"] += 1
        elif preference_choice == "natuur":
            preferences["natuur"] += 1

        # Update voorkeuren op basis van keuze in de tweede vraag (fotokeuze)
        photo_preference = request.form.get('photo_preference')
        if photo_preference == "natuur":
            preferences["natuur"] += 1
        elif photo_preference == "avontuur":
            preferences["avontuur"] += 1
        elif photo_preference == "cultuur":
            preferences["cultuur"] += 1

        # Controleer of de username of email al bestaan
        if User.query.filter_by(username=username).first() is not None:
            flash('Username already registered. Please login.', 'register')
            return redirect(url_for('main.login'))  # Redirect naar de login-pagina
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already registered. Please login.', 'register')
            return redirect(url_for('main.login'))  # Redirect naar de login-pagina
        
        # Maak een nieuwe gebruiker aan
        new_user = User(
            username=username,
            email=email,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            preferences=preferences
        )
        
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.user_id  # Gebruik user_id om sessie op te slaan
        return redirect(url_for('main.index'))  # Succesvolle registratie, ga naar index

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
            place = request.form.get('place', '').strip()
            file = request.files.get('file')
            listing_categorie = request.form.get('listing_categorie', '').strip()  # Nieuwe categorie veld

            # Validate form inputs
            if not listing_name or not description or not price or not place or not listing_categorie:
                flash("All fields are required (name, description, price,place, category).", "error")
                return redirect(request.url)
            
             # Check if place is in the format "place, country"
            if ',' not in place:
                flash("Invalid place format. Please select a valid place from the suggestions.", "error")
                return redirect(request.url)
            # Validate the place with GeoNames API
            username = 'bertdr1'  # Replace with your GeoNames username
            validation_url = f'http://api.geonames.org/searchJSON?username=bertdr1&q={place}&maxRows=1'
            validation_response = requests.get(validation_url)
            if validation_response.status_code != 200 or not validation_response.json().get('geonames'):
                flash("Invalid place. Please select a valid place from the suggestions.", "error")
                return redirect(request.url)
            
            if not file:
                flash("A file is required.", "error")
                return redirect(request.url)

            try:
                price = float(price)  # Convert price to a float
                if price < 0:   #Check if price is negative
                    flash("Price cannot be negative.","error")
                    return redirect(request.url)
                price = round(price,2)  #Round price to two decimal places
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
                place=place,
                listing_categorie = listing_categorie,
                user_id=session['user_id']
            )
            db.session.add(new_listing)  # Add the listing to the session
            db.session.commit()  # Commit the changes to the database

            flash("Listing added successfully.", "success")
            return redirect(url_for('main.add_listing'))

        except Exception as e:
            db.session.rollback()  # Roll back any database changes if an error occurs
            flash(f"An error occurred while adding the listing: {str(e)}", "error")
            return redirect(request.url)

    return render_template('add_listing.html')


@main.route('/my_listings')
def my_listings():
    if 'user_id' not in session:
        flash('You need to log in to view your listings.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user_listings = Listing.query.filter_by(user_id=user_id).all()

    for listing in user_listings:
        listing.price_listing = f"{round(listing.price_listing, 2):.2f}"  # Format price to 2 decimal places
        listing.like_count = len(Like.query.filter_by(listing_id=listing.listing_id).all())  # Count likes

    return render_template('my_listings.html', listings=user_listings)


@main.route('/listings')
def listings():
    all_listings = Listing.query.all()
    for listing in all_listings:
        listing.price_listing = round(listing.price_listing,2)
        listing.like_count = len(listing.likes)
    return render_template('listings.html', listings=all_listings)

import requests

@main.route('/search_places', methods=['GET'])
def search_places():
    query = request.args.get('q', '')
    username = 'bertdr1'  # Replace with your GeoNames username
    if not query:
        return jsonify([])

    url = f'http://api.geonames.org/searchJSON?username=bertdr1&q={query}&maxRows=10'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # Extract relevant data
        suggestions = [
            {
                'name': place['name'],
                'country': place.get('countryName', ''),
                'lat': place.get('lat'),
                'lng': place.get('lng')
            }
            for place in data.get('geonames', [])
        ]
        return jsonify(suggestions)
    else:
        return jsonify({'error': 'Failed to fetch places from GeoNames'}), 500



@main.route('/transactions')
def transactions():
    if 'user_id' not in session:
        flash('You need to log in to view your transaction history.', 'warning')
        return redirect(url_for('main.login'))

    # Transactions where the user is the buyer
    purchased_transactions = Transaction.query.filter_by(user_id=session['user_id']).all()

    # Transactions where the user is the seller
    sold_transactions = Transaction.query.join(Listing).filter(Listing.user_id == session['user_id']).all()

    # Mark transactions as 'purchase' or 'sale'
    combined_transactions = [
        {'type': 'purchase', 'transaction': t} for t in purchased_transactions
    ] + [
        {'type': 'sale', 'transaction': t} for t in sold_transactions
    ]

    # Sort all transactions by date
    combined_transactions.sort(key=lambda x: x['transaction'].created_at, reverse=True)

    return render_template('combined_transactions.html', transactions=combined_transactions)


@main.route('/bought_transactions')
def bought_transactions():
    if 'user_id' not in session:
        flash('You need to log in to view your transaction history.', 'warning')
        return redirect(url_for('main.login'))

    user_transactions = Transaction.query.filter_by(user_id=session['user_id']).all()
    return render_template('bought_transactions.html', transactions=user_transactions)


@main.route('/sold-transactions')
def sold_transactions():
    if 'user_id' not in session:
        flash('You need to log in to view your sold listings.', 'warning')
        return redirect(url_for('main.login'))

    # Get listings where the logged-in user is the seller
    user_sold_transactions = Transaction.query.join(Listing).filter(Listing.user_id == session['user_id']).all()

    return render_template('sold_transactions.html', transactions=user_sold_transactions)



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
        listing.listing_categorie = request.form['listing_categorie']
        db.session.commit()
        return redirect(url_for('main.listings'))
    
    return render_template('edit_listing.html', listing=listing)



@main.route('/listing/<int:listing_id>', methods=['GET', 'POST'])
def view_listing(listing_id):
    # Haal de listing op
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))

    # Ronde de prijs naar twee decimalen
    listing.price_listing = round(listing.price_listing, 2)

    # Haal reviews op
    reviews = Review.query.filter_by(listing_id=listing_id).all()

    # Controleer of de gebruiker is ingelogd en of de listing al is gekocht
    transaction_exists = None
    if 'user_id' in session:
        transaction_exists = Transaction.query.filter_by(
            user_id=session['user_id'], 
            listing_id=listing_id, 
            status=True
        ).first()

    # Check if the user is trying to like their own listing
    can_like = True
    if 'user_id' in session and listing.user_id == session['user_id']:
        can_like = False  # Disable like if it's the user's own listing

    if request.method == 'POST':
        # Controleer of de gebruiker is ingelogd
        if 'user_id' not in session:
            flash("Please log in to purchase this listing.", 'error')
            return redirect(url_for('main.login'))

        # Haal koper en verkoper op
        buyer = User.query.get(session['user_id'])
        seller = User.query.get(listing.user_id)

        # Controleer of de gebruiker probeert zijn eigen listing te kopen
        if buyer.user_id == seller.user_id:
            flash("You cannot purchase your own listing.", 'error')
            return redirect(url_for('main.view_listing', listing_id=listing_id))

        # Controleer of de koper voldoende saldo heeft
        if buyer.wallet_balance < listing.price_listing:
            flash('Insufficient wallet balance to make this purchase.', 'danger')
            return redirect(url_for('main.view_listing', listing_id=listing_id))

        # Controleer of de listing al is gekocht
        if transaction_exists:
            flash('You have already purchased this listing.', 'info')
            return redirect(url_for('main.view_listing', listing_id=listing_id))

        # Trek saldo af bij koper en voeg toe bij verkoper
        buyer.wallet_balance -= listing.price_listing
        seller.wallet_balance += listing.price_listing

        # Registreer de transactie
        transaction = Transaction(
            user_id=buyer.user_id, 
            listing_id=listing_id, 
            price_transaction=listing.price_listing,
            status=True
        )
        db.session.add(transaction)

        # Commit de wijzigingen in de database
        db.session.commit()

        flash('Purchase successful! Your wallet has been debited.', 'success')
        return redirect(url_for('main.view_listing', listing_id=listing_id))

    return render_template('view_listing.html', listing=listing, reviews=reviews, transaction_exists=transaction_exists, can_like=can_like)





@main.route('/add-review/<int:listing_id>', methods=['GET', 'POST'])
def add_review(listing_id):
    if 'user_id' not in session:
        flash('You need to log in to leave a review.', 'warning')

        return redirect(url_for('main.login'))
    
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    transaction = Transaction.query.filter_by(
    user_id=session['user_id'],
    listing_id=listing_id
    ).first()
    
    if not transaction:
        flash('You can only review listings you have purchased.', 'error')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    if request.method == 'POST':
        content = request.form['review_text']
        new_review = Review( user_id=session['user_id'],listing_id=listing_id,content=content)
        db.session.add(new_review)
        db.session.commit()
        flash('Review added successfully!', 'success')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    return render_template('add_review.html', listing=listing)

def transaction_exists(user_id, listing_id):
    return Transaction.query.filter_by(user_id=user_id, listing_id=listing_id).first() is not None


@main.route('/reviews/<int:listing_id>')
def view_reviews(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    return render_template('view_reviews.html', listing_id=listing_id, reviews=reviews)

#@main.route('/search', methods=['GET', 'POST'])
#def search():
    query = request.args.get('query')
    if query:
        listings = Listing.query.filter(Listing.listing_name.ilike(f'%{query}%')).all()
    else:
        listings = Listing.query.all()
    return render_template('listings.html', listings=listings)


#@main.route('/filter', methods=['GET'])
#def filter_listings():
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
@main.route('/get_pdf/<int:listing_id>', methods=['GET'])
def get_pdf(listing_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You need to log in to access this PDF.', 'warning')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    
    # Check if the listing exists
    listing = Listing.query.get(listing_id)
    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.listings'))
    
    # Check if the user has purchased the listing
    transaction = Transaction.query.filter_by(user_id=user_id, listing_id=listing_id).first()
    if not transaction:
        flash('You need to purchase this listing to access its PDF.', 'warning')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    # Retrieve the PDF URL from the listing
    pdf_url = listing.url
    if not pdf_url:
        flash('This listing does not have an associated PDF.', 'error')
        return redirect(url_for('main.view_listing', listing_id=listing_id))
    
    # Redirect to the PDF URL
    return redirect(pdf_url)

@main.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('You need to log in to edit your profile.', 'warning')
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Haal de ingevoerde gegevens op
        username = request.form.get('username', user.username)
        email = request.form.get('email', user.email)
        phone_number = request.form.get('phone_number', user.phone_number)
        date_of_birth = request.form.get('date_of_birth', user.date_of_birth)

        # Validatie van e-mail met accenten
        email_pattern = r"^[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç._%-]+@[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+\.[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+$"
        if not re.match(email_pattern, email):
            flash('Invalid email address. Please enter a valid email.', 'error')
            return redirect(url_for('main.edit_profile'))

        # Update de gebruiker met de nieuwe gegevens
        user.username = username
        user.email = email
        user.phone_number = phone_number
        user.date_of_birth = date_of_birth
        
        db.session.commit()

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('main.account'))  # Of de gewenste pagina na succes

    return render_template('edit_profile.html', user=user)
@main.route('/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('You need to log in to delete your account.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    # Verwijder alle afhankelijkheden (bijv. listings, likes, reviews)
    Listing.query.filter_by(user_id=user_id).delete()
    Like.query.filter_by(user_id=user_id).delete()
    Review.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()

    session.pop('user_id', None)
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('main.index'))

@main.route('/like/<int:listing_id>', methods=['POST'])
def like_listing(listing_id):
    if 'user_id' not in session:
        flash('You need to log in to like a listing.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    existing_like = Like.query.filter_by(user_id=user_id, listing_id=listing_id).first()

    if existing_like:
        flash('You already liked this listing.', 'info')
        return redirect(url_for('main.view_listing', listing_id=listing_id))

    # Add a new like
    new_like = Like(user_id=user_id, listing_id=listing_id)
    db.session.add(new_like)
    # Update user preferences based on the listing category
    listing = Listing.query.get(listing_id)
    user = User.query.get(user_id)
    if listing and user:
        category = listing.listing_categorie
        if category:
            if user.preferences and category in user.preferences:
                user.preferences[category] += 1
            else:
                if user.preferences is None:
                    user.preferences = {}
                user.preferences[category] = 1


    db.session.commit()

    flash('You liked this listing!', 'success')
    return redirect(url_for('main.view_listing', listing_id=listing_id))


@main.route('/unlike/<int:listing_id>', methods=['POST'])
def unlike_listing(listing_id):
    if 'user_id' not in session:
        flash('You need to be logged in to unlike a listing.', 'error')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']

    # Zoek de like in de database
    like = Like.query.filter_by(user_id=user_id, listing_id=listing_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        flash('Listing unliked successfully.', 'success')
    else:
        flash('You have not liked this listing.', 'error')

    # Verwerk 'next' parameter
    next_page = request.args.get('next', url_for('main.index'))  # Default naar de homepagina
    return redirect(next_page)




@main.route('/liked-listings')
def liked_listings():
    if 'user_id' not in session:
        flash('You need to log in to view your liked listings.', 'warning')
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    liked_listings = Listing.query.join(Like).filter(Like.user_id == user_id).all()

    for listing in liked_listings:
        listing.like_count = len(listing.likes)
        listing.price_listing = round(listing.price_listing,2)

    return render_template('liked_listings.html', listings=liked_listings)



from flask import request, redirect, url_for, session

@main.before_request
def store_last_visited_url():
    # Store the current URL before processing the next request
    if request.endpoint != 'main.go_back':  # Avoid storing the 'go-back' route itself
        session['last_page'] = request.url

@main.route('/go-back', methods=['GET'])
def go_back():
    # Attempt to get the referrer first
    previous_page = request.referrer

    # Fallback to session-stored last visited page or index
    if not previous_page:
        previous_page = session.get('last_page', url_for('main.index'))

    return redirect(previous_page)

@main.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        user_id = session['user_id']
        user = User.query.get(user_id)
        user.preferences = {
            "natuur": int(request.form['natuur']),
            "cultuur": int(request.form['cultuur']),
            "avontuur": int(request.form['avontuur'])
        }
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('quiz.html')


@main.route('/filter_listings', methods=['GET', 'POST'])
def filter_listings():
    # Get filter and search parameters from the request
    search_query = request.args.get('search', '').strip()
    sort_by_price = request.args.get('filter-price')  # "low-to-high" or "high-to-low"
    sort_by_date = request.args.get('filter-date')  # "newest" or "oldest"

    # Base query
    query = Listing.query

    # Apply search query (if provided)
    if search_query:
        query = query.filter(Listing.listing_name.ilike(f"%{search_query}%"))

    # Apply sorting
    if sort_by_price:
        # Price sorting takes priority
        if sort_by_price == 'low-to-high':
            if sort_by_date == 'newest':
                query = query.order_by(Listing.price_listing.asc(), Listing.created_at.desc())
            elif sort_by_date == 'oldest':
                query = query.order_by(Listing.price_listing.asc(), Listing.created_at.asc())
            else:
                query = query.order_by(Listing.price_listing.asc())
        elif sort_by_price == 'high-to-low':
            if sort_by_date == 'newest':
                query = query.order_by(Listing.price_listing.desc(), Listing.created_at.desc())
            elif sort_by_date == 'oldest':
                query = query.order_by(Listing.price_listing.desc(), Listing.created_at.asc())
            else:
                query = query.order_by(Listing.price_listing.desc())
    elif sort_by_date:
        # Apply date sorting only if price sorting is not specified
        if sort_by_date == 'newest':
            query = query.order_by(Listing.created_at.desc())
        elif sort_by_date == 'oldest':
            query = query.order_by(Listing.created_at.asc())

    # Get the filtered listings
    filtered_listings = query.all()

    # Render the listings page with filtered results
    return render_template('index.html', listings=filtered_listings)



@main.route('/filter_listings2', methods=['GET'])
def filter_listings2():
    # Get filter parameters from the request
    search_query = request.args.get('search', '').strip()
    min_price = request.args.get('min-price', type=float)
    max_price = request.args.get('max-price', type=float)
    category = request.args.get('category', '').strip()

    # Base query
    query = Listing.query

    # Apply search query (if provided)
    if search_query:
        query = query.filter(Listing.listing_name.ilike(f"%{search_query}%"))

    # Apply minimum price filter (if provided)
    if min_price is not None:
        query = query.filter(Listing.price_listing >= min_price)

    # Apply maximum price filter (if provided)
    if max_price is not None:
        query = query.filter(Listing.price_listing <= max_price)

    # Apply category filter (if provided and not 'all')
    if category and category != 'all':
        query = query.filter(Listing.listing_categorie.ilike(f"%{category}%"))

    # Fetch the filtered listings
    filtered_listings = query.all()

    # Render the template with filtered results
    return render_template('listings.html', listings=filtered_listings)


supabase: Client = create_client(supabase_url, supabase_key)

@main.route('/view-pdf/<int:listing_id>')
def view_pdf(listing_id):
    listing = Listing.query.get(listing_id)
    if not listing:
        return "Listing not found.", 404

    pdf_url = listing.url  # Ensure this contains the correct public URL
    if not pdf_url:
        return "No PDF available for this listing.", 404

    return render_template('view_pdf.html', pdf_url=pdf_url)
