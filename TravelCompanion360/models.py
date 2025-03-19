from datetime import datetime
from flask_login import UserMixin
from db import db  # Import db from the new db.py file

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class RoomAvailability(db.Model):
    """Track room availability by date for each hotel"""
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    room_number = db.Column(db.Integer, nullable=True)
    
    # Add a unique constraint to ensure we don't double-book
    __table_args__ = (
        db.UniqueConstraint('hotel_id', 'date', 'room_number', name='unique_room_date'),
    )
    
    def __repr__(self):
        status = "Available" if self.is_available else "Booked"
        return f'<Room {self.room_number} at Hotel {self.hotel_id} on {self.date}: {status}>'

class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=0)
    description = db.Column(db.Text)
    total_rooms = db.Column(db.Integer, default=20)
    available_rooms = db.Column(db.Integer, default=20)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='hotel', lazy=True)
    room_availability = db.relationship('RoomAvailability', backref='hotel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Hotel {self.name}>'
        
    def update_availability(self):
        """Update the number of available rooms based on current bookings"""
        active_bookings = RoomAvailability.query.filter_by(hotel_id=self.id, is_available=False).count()
        self.available_rooms = max(0, self.total_rooms - active_bookings)
        self.last_updated = datetime.utcnow()
        return self.available_rooms
        
    def is_available(self, check_in_date, check_out_date):
        """Check if the hotel has available rooms for the given dates"""
        from sqlalchemy import and_, func
        
        # Calculate how many rooms are booked during the requested period
        booked_rooms = db.session.query(func.count(RoomAvailability.id)).filter(
            and_(
                RoomAvailability.hotel_id == self.id,
                RoomAvailability.is_available == False,
                RoomAvailability.date >= check_in_date,
                RoomAvailability.date < check_out_date
            )
        ).scalar()
        
        # If any day has all rooms booked, the hotel is not available
        max_booked = db.session.query(func.count(RoomAvailability.id)).\
            filter(RoomAvailability.hotel_id == self.id).\
            filter(RoomAvailability.is_available == False).\
            filter(RoomAvailability.date.between(check_in_date, check_out_date)).\
            group_by(RoomAvailability.date).\
            order_by(func.count(RoomAvailability.id).desc()).\
            first()
            
        max_booked_count = max_booked[0] if max_booked else 0
        
        # If the maximum number of rooms booked on any day in the range
        # is less than the total rooms, then the hotel is available
        return max_booked_count < self.total_rooms

class CarRental(db.Model):
    __tablename__ = 'car_rental'
    id = db.Column(db.Integer, primary_key=True)  # Add a primary key
    location = db.Column(db.String(100), nullable=False)
    car_type = db.Column(db.String(50), nullable=False)
    pickup_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='car_rental', lazy=True)
    
    def __repr__(self):
        return f'<CarRental {self.car_type} at {self.location}>'

class Booking(db.Model):
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=True)
    car_rental_id = db.Column(db.Integer, db.ForeignKey('car_rental.id'), nullable=True)
    booking_type = db.Column(db.String(20), nullable=False)  # 'hotel' or 'car'
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    check_in_date = db.Column(db.Date, nullable=True)
    check_out_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='confirmed')  # 'confirmed', 'cancelled', 'completed'
    
    # Relationships
    availability = db.relationship('RoomAvailability', backref='booking', lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.id}, Type: {self.booking_type}>'
        
    def cancel(self):
        """Cancel a booking and free up room availability"""
        self.status = 'cancelled'
        # Update room availability
        if self.booking_type == 'hotel' and self.check_in_date and self.check_out_date:
            room_dates = RoomAvailability.query.filter_by(
                booking_id=self.id,
                hotel_id=self.hotel_id
            ).all()
            
            for room_date in room_dates:
                room_date.is_available = True
                room_date.booking_id = None
            
            # Update hotel availability count
            if self.hotel:
                self.hotel.update_availability()
        
        db.session.commit()
        return True