# app/routes.py

from flask import Flask, Blueprint, request, redirect, url_for, render_template, session, flash
from flask import Blueprint, request, redirect, url_for, render_template, session, flash
from .models import db, User, Listing, Transaction, Review, Notification, Like
from supabase import create_client, Client
from .config import Config
from flask import jsonify, request
import re
from flask import render_template, request, redirect, flash, session, url_for
from werkzeug.utils import secure_filename
import os
import requests
from sqlalchemy import desc
from sqlalchemy.orm.attributes import flag_modified

#from datetime import datetime


main = Blueprint('main', __name__)


@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])  # Haal user info op via user_id

        # Check of de gebruiker voorkeuren heeft ingesteld
        if user.preferences and any(user.preferences.values()):
            top_preference = max(user.preferences, key=user.preferences.get)
            listings = Listing.query.filter(
                Listing.listing_categorie.contains(top_preference), 
                Listing.user_id != user.user_id
            ).all()
        else:
            listings = Listing.query.filter(Listing.user_id != user.user_id).all()
    else:
        listings = Listing.query.all()

    # Voeg aantal likes, gemiddelde rating en afgeronde prijzen toe
    for listing in listings:
        listing.price_listing = round(listing.price_listing, 2)
        listing.like_count = len(listing.likes)  # Tel aantal likes
        
        # Bereken gemiddelde rating, negeer None ratings
        reviews = listing.reviews
        valid_ratings = [review.rating for review in reviews if review.rating is not None]
        if valid_ratings:
            listing.average_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
        else:
            listing.average_rating = None

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
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validatie van e-mail
        email_pattern = r"^[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç._%-]+@[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+\.[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+$"
        if not re.match(email_pattern, email):
            flash('Invalid email address. Please enter a valid email.', 'error')
            return redirect(url_for('main.register'))
        
        # Geboortedatum validatie 
        if not date_of_birth:
            flash('Invalid date of birth. Please enter a valid date of birth.', 'error')
            return redirect(url_for('main.register'))

        date_parts = date_of_birth.split('-')
        if len(date_parts) != 3: #Controleer of de datum bestaat uit drie delen (dag, maand, jaar)
            flash('Invalid date format. Please enter the date in "dd mm yyyy" format.', 'error')
            return redirect(url_for('main.register'))
    
        day, month, year = date_parts
        if not (day.isdigit() and month.isdigit() and year.isdigit()): #--> Controleer of de dag, maand en jaar geldig zijn
            flash('Invalid date. Day, month, and year must be numeric.', 'error')
            return redirect(url_for('main.register'))
        
        if len(year) != 4 or int(year) < 1 or int(year) > 9999: #--> Controleer of het jaartal vier cijfers heeft en tussen 1 en 9999 ligt
            flash('Year must be between 1 and 9999.', 'error')
            return redirect(url_for('main.register'))

        if int(month) < 1 or int(month) > 12: #-> Controleer of de maand binnen de geldige waardes valt
            flash('Invalid month. Please enter a value between 01 and 12.', 'error')
            return redirect(url_for('main.register'))
        
        if int(day) < 1 or int(day) > 31: #-> Controleer of de dag binnen de geldige waardes valt
            flash('Invalid day. Please enter a value between 01 and 31.', 'error')
            return redirect(url_for('main.register'))
        
        #Password validation
        if len(password) < 8:
            flash('Password must be more than 8 characters long.', 'error')
            return redirect(url_for('main.register'))

        if password != confirm_password:
            flash('Passwords do not match. Please try again.','error')
            return redirect(url_for('main.register'))

        # Phone number validation (should be exactly 10 digits)
        if len(phone_number) != 10 or not phone_number.isdigit():
            flash('Phone number must be exactly 10 digits long.', 'error')
            return redirect(url_for('main.register'))
        
        # Start met de basisvoorkeuren
        preferences = preferences = {"Adventure": 0, "Nature": 0, "Culture": 0, "Sport & Active": 0, "Family": 0, "Wellness & Relaxation": 0, "Romantic": 0, "City Trips": 0, "Festivals & Events": 0, "Budget & Backpacking": 0, "Roadtrip & Multi-Destination": 0}

        # Update voorkeuren op basis van keuze in de eerste vraag
        preference_choice = request.form.get('preference')
        if preference_choice in preferences:
            preferences[preference_choice]+=1
        
        # Handle multiple photo preferences
        photo_preferences = request.form.getlist('photo_preference[]')
        for photo_pref in photo_preferences:
            categories = photo_pref.split(', ')
            for category in categories:
                if category in preferences:
                    preferences[category] += 1


        # Controleer of de username of email al bestaan
        if User.query.filter_by(username=username).first() is not None:
            flash('Username already registered. Please login.', 'register')
            return redirect(url_for('main.login'))  # Redirect naar de login-pagina
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already registered. Please login.', 'register')
            return redirect(url_for('main.login'))  # Redirect naar de login-pagina
        
        # Maak na alle checks een nieuwe gebruiker aan als dus alles in orde is
        new_user = User(
            username=username,
            email=email,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            preferences=preferences
        )
        new_user.set_password(password) #Wachtwoord hash instellen
        
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
        password = request.form['password']  # Haal het wachtwoord op, default is een lege string

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.user_id
            flash('Login successful!','info')
            return redirect(url_for('main.index'))

        flash('Incorrect username or password. Please try again.','error')
        return render_template('login.html')

    return render_template('login.html')


@main.route('/account')
def account():
    if 'user_id' not in session:
        flash('You need to log in to access your account.', 'warning')
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    return render_template('account.html', user=user)


@main.route('/wallet', methods=['GET'])
def wallet():
    if 'user_id' not in session:
        flash('You need to log in to view your wallet.', 'warning')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('wallet.html', wallet_balance=round(user.wallet_balance,2))


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


@main.route('/wallet/recharge', methods=['GET'])
def recharge_page():
    if 'user_id' not in session:
        flash('You need to log in to recharge your wallet.', 'walleterror')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['user_id'])
    return render_template('recharge_wallet.html', wallet_balance=round(user.wallet_balance,2))


@main.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        # Verwijder de user_id uit de sessie
        session.pop('user_id', None)
        # Redirect naar de homepagina na succesvolle logout
        return redirect(url_for('main.index'))  # Verwijs naar de homepagina

    # Bij een GET-verzoek tonen we een bevestigingspagina
    return render_template('logout.html')  # Toon de logout-pagina met een boodschap


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
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validatie van e-mail met accenten
        email_pattern = r"^[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç._%-]+@[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+\.[a-zA-Zàáâäãåçèéêëìíîïòóôöõùúûüÿñç.-]+$"
        if not re.match(email_pattern, email):
            flash('Invalid email address. Please enter a valid email.', 'error')
            return redirect(url_for('main.edit_profile'))

        # Phone number validation (should be exactly 10 digits)
        if len(phone_number) != 10 or not phone_number.isdigit():
            flash('Phone number must be exactly 10 digits long.', 'register')
            return redirect(url_for('main.register'))
        
        # Validatie van wachtwoord
        if new_password or confirm_password:
            if len(new_password) < 8:
                flash('Password must be at least 8 characters long.', 'error')
                return redirect(url_for('main.edit_profile'))
            if new_password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('main.edit_profile'))
            # Wachtwoord updaten
            user.set_password(new_password)

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

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('main.index'))

    # Verwijder gerelateerde likes
    likes = Like.query.filter_by(user_id=user_id).all()
    for like in likes:
        db.session.delete(like)

    # Verwijder reviews van de gebruiker
    reviews = Review.query.filter_by(user_id=user_id).all()
    for review in reviews:
        db.session.delete(review)

    # Verwijder notificaties
    notifications = Notification.query.filter_by(user_id=user_id).all()
    for notification in notifications:
        db.session.delete(notification)

    # Verwijder transacties waarbij de gebruiker betrokken is
    transactions = Transaction.query.filter(
        (Transaction.user_id == user_id) |
        (Transaction.listing_id.in_(
            Listing.query.filter_by(user_id=user_id).with_entities(Listing.listing_id)
        ))
    ).all()
    for transaction in transactions:
        db.session.delete(transaction)

    # Verwijder listings van de gebruiker
    listings = Listing.query.filter_by(user_id=user_id).all()
    for listing in listings:
        # Verwijder gerelateerde likes van de listing
        listing_likes = Like.query.filter_by(listing_id=listing.listing_id).all()
        for listing_like in listing_likes:
            db.session.delete(listing_like)
        # Verwijder gerelateerde reviews van de listing
        listing_reviews = Review.query.filter_by(listing_id=listing.listing_id).all()
        for listing_review in listing_reviews:
            db.session.delete(listing_review)
        db.session.delete(listing)

    # Verwijder de gebruiker
    db.session.delete(user)
    db.session.commit()

    # Verwijder sessie en bevestig verwijdering
    session.pop('user_id', None)
    flash('Your account has been deleted successfully.', 'success')
    return redirect(url_for('main.index'))




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
            picture = request.files.get('picture')

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
            
            try:
                price = float(price)  # Convert price to a float
                if price < 0:   #Check if price is negative
                    flash("Price cannot be negative.","error")
                    return redirect(request.url)
                price = round(price,2)  #Round price to two decimal places
            except ValueError:
                flash("Price must be a valid number.", "error")
                return redirect(request.url)
            
            
            if not file:
                flash("A file is required.", "error")
                return redirect(request.url)
            
            # Ensure the file is a PDF
            if not file.filename.endswith('.pdf'):
                flash("Only PDF files are allowed.", "error")
                return redirect(request.url)
            # Secure the file name
            import uuid
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            folder_path = f"Listing_Bestand/{uuid.uuid4().hex}_{secure_filename(file.filename)}"

            file_content = file.read()
            # Upload the file to Supabase
            response = supabase.storage.from_("ViaVia").upload(folder_path, file_content, {
                'content-type': 'application/pdf'
                })

            # Handle the response
            if hasattr(response, "raw_response") and response.raw_response.status_code != 200:
                flash(f"Error uploading file to Supabase: {response.raw_response.text}", "error")
                return redirect(request.url)

            # Get the public URL of the file
            file_url = f"{supabase_url}/storage/v1/object/public/ViaVia/{folder_path}"

            
            if picture and picture.filename.endswith(('jpg', 'jpeg', 'png')):
                picture_filename = f"Listing_Picture/{uuid.uuid4().hex}_{secure_filename(picture.filename)}"
                picture_content = picture.read()

                # Upload the picture to Supabase
                picture_response = supabase.storage.from_("ViaVia").upload(picture_filename, picture_content, {
                    'content-type': picture.mimetype
                })

                if hasattr(picture_response, "raw_response") and picture_response.raw_response.status_code != 200:
                    flash(f"Error uploading picture: {picture_response.raw_response.text}", "error")
                    return redirect(request.url)

                # Get the public URL of the picture
                picture_url = f"{supabase_url}/storage/v1/object/public/ViaVia/{picture_filename}"
            else:
                flash("A valid picture file is required (jpg, jpeg, png).", "error")
                return redirect(request.url)
            # Save listing details to the database
            new_listing = Listing(
                listing_name=listing_name,
                description=description,
                price_listing=price,
                url=file_url,  # Save the file URL
                place=place,
                picture=picture_url,
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

@main.route('/delete-listing/<int:listing_id>', methods=['POST'])
def delete_listing(listing_id):
    if 'user_id' not in session:
        flash('You need to log in to delete a listing.', 'warning')
        return redirect(url_for('main.login'))

    # Fetch the listing by ID
    listing = Listing.query.get(listing_id)

    if not listing:
        flash('Listing not found.', 'error')
        return redirect(url_for('main.my_listings'))  # Redirect to a page with a list of the user's listings

    # Check if the logged-in user is the owner of the listing
    if listing.user_id != session['user_id']:
        flash('You do not have permission to delete this listing.', 'error')
        return redirect(url_for('main.my_listings'))

    try:
        # Delete all associated likes for the listing
        likes = Like.query.filter_by(listing_id=listing_id).all()
        for like in likes:
            db.session.delete(like)

        # Remove the listing from the session and commit to the database
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the listing: {str(e)}', 'error')

    return redirect(url_for('main.my_listings'))  # Redirect to a page with the user's listings

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

        # Bereken gemiddelde rating, negeer None ratings
        reviews = Review.query.filter_by(listing_id=listing.listing_id).all()
        valid_ratings = [review.rating for review in reviews if review.rating is not None]
        if valid_ratings:
            listing.average_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
        else:
            listing.average_rating = None  # Geen ratings beschikbaar

    return render_template('my_listings.html', listings=user_listings)


@main.route('/listings')
def listings():
    all_listings = Listing.query.all()
    for listing in all_listings:
        listing.price_listing = round(listing.price_listing, 2)
        listing.like_count = len(listing.likes)  # Tel het aantal likes
        
        # Bereken gemiddelde rating, negeer None ratings
        reviews = listing.reviews
        valid_ratings = [review.rating for review in reviews if review.rating is not None]
        if valid_ratings:
            listing.average_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
        else:
            listing.average_rating = None  # Geen ratings beschikbaar
    
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

    # Bereken het aantal likes
    listing.like_count = len(listing.likes)

    # Bereken gemiddelde rating, negeer None ratings
    reviews = Review.query.filter_by(listing_id=listing_id).all()
    valid_ratings = [review.rating for review in reviews if review.rating is not None]
    if valid_ratings:
        listing.average_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
    else:
        listing.average_rating = None

    # Controleer of de gebruiker is ingelogd en of de listing al is gekocht
    transaction_exists = None
    has_reviewed = False
    seller_email = None  # Voeg de verkoper-email toe
    if 'user_id' in session:
        user_id = session['user_id']
        transaction = Transaction.query.filter_by(
            user_id=user_id,
            listing_id=listing_id,
        ).first()

        # Controleer of de gebruiker al een review heeft toegevoegd
        has_reviewed = Review.query.filter_by(user_id=user_id, listing_id=listing_id).first() is not None

        # Controleer of de gebruiker de listing heeft gekocht
        if transaction:
            transaction_exists = True
            seller_email = listing.user.email  # Verkrijg het e-mailadres van de verkoper

    # Controleer of de gebruiker zijn eigen listing probeert te liken
    can_like = True
    if 'user_id' in session and listing.user_id == session['user_id']:
        can_like = False  # Disable like if it's the user's own listing

    if request.method == 'POST':
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

        # Trek saldo af bij koper en voeg toe bij verkoper
        buyer.wallet_balance -= listing.price_listing
        seller.wallet_balance += listing.price_listing

        # Registreer de transactie
        transaction = Transaction(
            user_id=buyer.user_id,
            listing_id=listing_id,
            price_transaction=listing.price_listing,
        )
        db.session.add(transaction)
        db.session.commit()

        flash('Purchase successful! Your wallet has been debited.', 'success')
        return redirect(url_for('main.view_listing', listing_id=listing_id))

    return render_template(
        'view_listing.html',
        listing=listing,
        reviews=reviews,
        transaction_exists=transaction_exists,
        can_like=can_like,
        has_reviewed=has_reviewed,
        seller_email=seller_email  # Pass de verkoper-email naar de template
    )


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

    user_transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(desc(Transaction.created_at)).all()
    return render_template('bought_transactions.html', transactions=user_transactions)


@main.route('/sold-transactions')
def sold_transactions():
    if 'user_id' not in session:
        flash('You need to log in to view your sold listings.', 'warning')
        return redirect(url_for('main.login'))

    # Get listings where the logged-in user is the seller
    user_sold_transactions = Transaction.query.join(Listing).filter(Listing.user_id == session['user_id']).order_by(desc(Transaction.created_at)).all()

    return render_template('sold_transactions.html', transactions=user_sold_transactions)


def transaction_exists(user_id, listing_id):
    return Transaction.query.filter_by(user_id=user_id, listing_id=listing_id).first() is not None


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
        rating = int(request.form['rating'])  # Haal de rating op uit het formulier
        
        # Validatie van rating
        if rating < 1 or rating > 5:
            flash('Invalid rating. Please select a value between 1 and 5.', 'error')
            return redirect(url_for('main.add_review', listing_id=listing_id))

        # Nieuwe review aanmaken
        new_review = Review(
            user_id=session['user_id'],
            listing_id=listing_id,
            content=content,
            rating=rating  # Rating opslaan
        )
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
    return render_template('view_reviews.html', listing_id=listing_id, reviews=reviews)


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


from decimal import Decimal

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
            user.preferences[category] = user.preferences.get(category, 0) + 1
            flag_modified(user, 'preferences')  # Expliciet aangeven dat dit veld is gewijzigd
            print(f"Updated {category} preference to {user.preferences[category]} for user {user.username}")

    try:
        db.session.commit()
        flash('You liked this listing!', 'success')
        print("Database commit successful.")
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while liking the listing.', 'error')
        print(f"Error during commit: {e}")


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

    # Verwerk 'next' parameter of blijf op de view_listing-pagina
    next_page = request.args.get('next', url_for('main.view_listing', listing_id=listing_id))  # Default naar view_listing
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
        listing.price_listing = round(listing.price_listing, 2)
        
        # Bereken gemiddelde rating, negeer None ratings
        reviews = listing.reviews
        valid_ratings = [review.rating for review in reviews if review.rating is not None]
        if valid_ratings:
            listing.average_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
        else:
            listing.average_rating = None  # Geen ratings beschikbaar

    return render_template('liked_listings.html', listings=liked_listings)


@main.route('/filter_listings', methods=['GET', 'POST'])
def filter_listings():
    # Get filter and search parameters from the request
    search_query = request.args.get('search', '').strip()
    sort_by_price = request.args.get('filter-price')  # "low-to-high" or "high-to-low"
    sort_by_date = request.args.get('filter-date')  # "newest" or "oldest"
    category = request.args.get('category', '').strip()
    filter_rating = request.args.get('filter-rating', '').strip()  # "high-to-low" or "only-5-star"

    # Base query
    query = Listing.query

    # Apply search query (if provided)
    if search_query:
        query = query.filter(Listing.listing_name.ilike(f"%{search_query}%"))

    # Apply category filter (if provided)
    if category:
        query = query.filter(Listing.listing_categorie.ilike(f"%{category}%"))

    # Retrieve all listings based on the current filters
    filtered_listings = query.all()

    # Calculate additional data for each listing
    for listing in filtered_listings:
        # Round the price to 2 decimal places
        listing.price_listing = round(listing.price_listing, 2)

        # Count the likes for the listing
        listing.like_count = len(listing.likes)

        # Calculate the average rating
        reviews = listing.reviews
        valid_ratings = [review.rating for review in reviews if review.rating is not None]
        if valid_ratings:
            listing.average_rating = round(sum(valid_ratings) / len(valid_ratings), 1)
        else:
            listing.average_rating = None

    # Apply rating filter (if provided)
    if filter_rating:
        if filter_rating == 'only-5-star':
            # Filter listings with an average rating of 5
            filtered_listings = [listing for listing in filtered_listings if listing.average_rating == 5]
        elif filter_rating == 'high-to-low':
            # Sort listings by average rating, descending
            filtered_listings.sort(key=lambda x: (x.average_rating or 0), reverse=True)

    # Apply sorting
    if sort_by_price:
        # Price sorting takes priority
        if sort_by_price == 'low-to-high':
            filtered_listings.sort(key=lambda x: (x.price_listing, -(x.created_at.timestamp())))
        elif sort_by_price == 'high-to-low':
            filtered_listings.sort(key=lambda x: (-x.price_listing, -(x.created_at.timestamp())))
    elif sort_by_date:
        # Apply date sorting only if price sorting is not specified
        if sort_by_date == 'newest':
            filtered_listings.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by_date == 'oldest':
            filtered_listings.sort(key=lambda x: x.created_at)

    # Render the listings page with filtered results
    return render_template('listings.html', listings=filtered_listings)



