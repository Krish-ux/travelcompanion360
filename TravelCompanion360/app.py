import os
from datetime import timedelta

from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import check_password_hash, generate_password_hash
import random
import string
import logging

logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy with a base class
class Base(DeclarativeBase):
    pass

from db import db  # Import db from the new db.py file

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///travel_companion.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)  # Set session to expire after 7 days

# Initialize the app with the extension
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Import models and forms after initializing db to avoid circular imports
with app.app_context():
    from models import User, Hotel, CarRental, Booking, RoomAvailability
    from forms import LoginForm, RegistrationForm, HotelSearchForm, CarRentalForm
    from utils.openai_helper import get_hotel_recommendations
    from utils.maps_helper import get_coordinates

    # Create database tables
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Generate a random password with specified length
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            # Generate and set a new random password for next login
            new_password = generate_random_password()
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            flash(f'Login successful! Your new password for next login is: {new_password}', 'success')
            flash('Please note down this password for your next login!', 'warning')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter((User.email == form.email.data) | 
                                         (User.username == form.username.data)).first()
        if existing_user:
            flash('Email or username already exists. Please use a different one.', 'danger')
            return render_template('register.html', form=form)
        
        password = generate_random_password()
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Registration successful! Your password is: {password}', 'success')
        flash('Please note down this password for your login!', 'warning')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', bookings=bookings)

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking and free up the reserved rooms"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id:
        flash('You can only cancel your own bookings.', 'danger')
        return redirect(url_for('profile'))
    
    # Call the cancel method which handles freeing up room availability
    if booking.cancel():
        flash('Your booking has been cancelled successfully.', 'success')
    else:
        flash('There was an error cancelling your booking.', 'danger')
    
    return redirect(url_for('profile'))

@app.route('/hotel_availability/<int:hotel_id>')
@login_required
def hotel_availability(hotel_id):
    """View room availability for a hotel"""
    from datetime import datetime, timedelta
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Get date range (default to next 7 days)
    start_date_str = request.args.get('start_date')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime.now().date()
    except ValueError:
        start_date = datetime.now().date()
    
    end_date = start_date + timedelta(days=7)
    
    # Get all room availability records for this date range
    room_availability = RoomAvailability.query.filter(
        RoomAvailability.hotel_id == hotel_id,
        RoomAvailability.date.between(start_date, end_date)
    ).order_by(RoomAvailability.date, RoomAvailability.room_number).all()
    
    # Group by date and room number for easy display
    availability_by_date = {}
    for avail in room_availability:
        date_str = avail.date.strftime('%Y-%m-%d')
        if date_str not in availability_by_date:
            availability_by_date[date_str] = {}
        availability_by_date[date_str][avail.room_number] = avail.is_available
    
    # Generate dates for display
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    return render_template(
        'hotel_availability.html',
        hotel=hotel,
        date_range=date_range,
        availability=availability_by_date,
        total_rooms=hotel.total_rooms
    )

@app.route('/hotels', methods=['GET', 'POST'])
@login_required
def hotels():
    form = HotelSearchForm()
    hotel_recommendations = []
    
    if form.validate_on_submit():
        destination = form.destination.data
        budget = form.budget.data
        
        # Get hotel recommendations from ChatGPT
        recommendations = get_hotel_recommendations(destination, budget)
        
        # Process recommendations (normally would come from a real API)
        if recommendations:
            session['hotel_recommendations'] = recommendations
            hotel_recommendations = recommendations
            flash(f'Found hotel recommendations for {destination}!', 'success')
        else:
            flash('Unable to find hotel recommendations. Please try again.', 'danger')
    
    # If there are recommendations in session, display them
    elif 'hotel_recommendations' in session:
        hotel_recommendations = session['hotel_recommendations']
    
    return render_template('hotels.html', form=form, recommendations=hotel_recommendations)

@app.route('/book_hotel/<int:hotel_id>', methods=['POST'])
@login_required
def book_hotel(hotel_id):
    from datetime import datetime, timedelta
    
    hotel = Hotel.query.get(hotel_id)
    
    # Extract check-in and check-out dates from form data
    check_in_date_str = request.form.get('check_in_date')
    check_out_date_str = request.form.get('check_out_date')
    
    if not check_in_date_str or not check_out_date_str:
        flash('Please provide both check-in and check-out dates.', 'danger')
        return redirect(url_for('hotels'))
    
    try:
        check_in_date = datetime.strptime(check_in_date_str, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        return redirect(url_for('hotels'))
    
    if check_in_date >= check_out_date:
        flash('Check-out date must be after check-in date.', 'danger')
        return redirect(url_for('hotels'))
    
    if not hotel:
        # If hotel doesn't exist in DB yet, we'd create it from the recommendations
        if 'hotel_recommendations' in session:
            for rec in session['hotel_recommendations']:
                if rec.get('id') == hotel_id:
                    hotel = Hotel(
                        id=hotel_id,
                        name=rec.get('name'),
                        location=rec.get('location'),
                        price_per_night=rec.get('price'),
                        rating=rec.get('rating', 0)
                    )
                    db.session.add(hotel)
                    db.session.commit()
                    break
    
    if hotel:
        # Check if the hotel has available rooms for the requested dates
        if not hotel.is_available(check_in_date, check_out_date):
            flash(f'Sorry, {hotel.name} is fully booked for the selected dates.', 'danger')
            return redirect(url_for('hotels'))
        
        # Create the booking
        booking = Booking(
            user_id=current_user.id,
            hotel_id=hotel.id,
            booking_type='hotel',
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            status='confirmed'
        )
        db.session.add(booking)
        db.session.flush()  # Get booking ID without committing
        
        # Generate availability records for each day of the stay
        # Assign a room number (simple algorithm - just grab the first available room)
        current_date = check_in_date
        day_count = (check_out_date - check_in_date).days
        room_number = None
        
        # Find the first available room number
        for room_num in range(1, hotel.total_rooms + 1):
            # Check if this room is available for all days of the stay
            conflicting_dates = RoomAvailability.query.filter(
                RoomAvailability.hotel_id == hotel.id,
                RoomAvailability.room_number == room_num,
                RoomAvailability.date.between(check_in_date, check_out_date - timedelta(days=1)),
                RoomAvailability.is_available == False
            ).count()
            
            if conflicting_dates == 0:
                room_number = room_num
                break
                
        if room_number is None:
            flash('No rooms available for the selected dates.', 'danger')
            db.session.rollback()
            return redirect(url_for('hotels'))
        
        # Create room availability entries for each day
        for _ in range(day_count):
            # Check if we already have an entry for this room/date
            existing_entry = RoomAvailability.query.filter_by(
                hotel_id=hotel.id,
                date=current_date,
                room_number=room_number
            ).first()
            
            if existing_entry:
                if not existing_entry.is_available:
                    flash(f'Room {room_number} is already booked for {current_date}.', 'danger')
                    db.session.rollback()
                    return redirect(url_for('hotels'))
                # Room exists and is available, update it
                existing_entry.is_available = False
                existing_entry.booking_id = booking.id
            else:
                # Create new availability entry
                room_avail = RoomAvailability(
                    hotel_id=hotel.id,
                    date=current_date,
                    is_available=False,
                    booking_id=booking.id,
                    room_number=room_number
                )
                db.session.add(room_avail)
            
            current_date += timedelta(days=1)
        
        # Update hotel's available rooms count
        hotel.update_availability()
        db.session.commit()
        
        flash(f'Successfully booked {hotel.name} for {day_count} nights (Room {room_number})!', 'success')
    else:
        flash('Hotel not found or unable to book.', 'danger')
    
    return redirect(url_for('hotels'))

@app.route('/car_rentals', methods=['GET', 'POST'])
@login_required
def car_rentals():
    form = CarRentalForm()
    if form.validate_on_submit():
        car_rental = CarRental(
            location=form.location.data,
            car_type=form.car_type.data,
            pickup_date=form.pickup_date.data,
            return_date=form.return_date.data
        )
        db.session.add(car_rental)
        db.session.commit()
        
        booking = Booking(
            user_id=current_user.id,
            car_rental_id=car_rental.id,
            booking_type='car'
        )
        db.session.add(booking)
        db.session.commit()
        
        flash('Car rental booked successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('car_rentals.html', form=form)

@app.route('/destinations')
def destinations():
    # Sample destinations for the map
    sample_destinations = [
        {"name": "Paris", "country": "France", "lat": 48.8566, "lng": 2.3522},
        {"name": "Tokyo", "country": "Japan", "lat": 35.6762, "lng": 139.6503},
        {"name": "New York", "country": "USA", "lat": 40.7128, "lng": -74.0060},
        {"name": "Cape Town", "country": "South Africa", "lat": -33.9249, "lng": 18.4241},
        {"name": "Sydney", "country": "Australia", "lat": -33.8688, "lng": 151.2093}
    ]
    return render_template('destinations.html', destinations=sample_destinations)

@app.route('/api/coordinates', methods=['GET'])
def coordinates():
    location = request.args.get('location', '')
    if not location:
        return {'error': 'No location provided'}, 400
    
    coords = get_coordinates(location)
    if coords:
        return {'lat': coords['lat'], 'lng': coords['lng']}
    else:
        return {'error': 'Location not found'}, 404

@app.route('/assistant')
def assistant():
    """
    Route for the AI Travel Assistant chatbot interface
    """
    return render_template('assistant.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to process chat messages and get responses from OpenAI
    """
    from utils.openai_helper import get_chat_response
    import logging
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return {'error': 'No message provided'}, 400
        
        user_message = data['message']
        
        # Store chat history in session for context
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        # Add user message to history
        session['chat_history'].append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        assistant_response = get_chat_response(user_message, session['chat_history'])
        
        # Add assistant response to history
        session['chat_history'].append({"role": "assistant", "content": assistant_response})
        
        # Keep only the last 20 messages to avoid token limits
        if len(session['chat_history']) > 20:
            session['chat_history'] = session['chat_history'][-20:]
        
        # Check if the response indicates a rate limit error (our fallback mechanism)
        if "offline mode" in assistant_response:
            # Still return the response but with a flag indicating rate limiting
            return {
                'response': assistant_response,
                'status': 'limited'
            }
        
        return {'response': assistant_response}
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return {
            'error': 'An unexpected error occurred while processing your request.',
            'response': 'I apologize, but I encountered an error. Our team has been notified, and we\'re working to resolve it. Please try again later.'
        }, 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Context processor to provide the current year to all templates
@app.context_processor
def inject_current_year():
    from datetime import datetime
    return {'current_year': datetime.now().year}
    
# Add Google Maps API key to all templates
@app.context_processor
def inject_google_maps_api_key():
    import os
    return {'GOOGLE_MAPS_API_KEY': os.environ.get('GOOGLE_MAPS_API_KEY')}
