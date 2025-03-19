from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from datetime import date

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Register')

class HotelSearchForm(FlaskForm):
    destination = StringField('Destination', validators=[DataRequired()])
    budget = FloatField('Budget per night ($)', validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', validators=[DataRequired()], format='%Y-%m-%d')
    check_out_date = DateField('Check-out Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Find Hotels')
    
    def validate_check_in_date(self, field):
        if field.data < date.today():
            raise ValidationError('Check-in date cannot be in the past')
            
    def validate_check_out_date(self, field):
        if field.data <= self.check_in_date.data:
            raise ValidationError('Check-out date must be after check-in date')

class CarRentalForm(FlaskForm):
    location = StringField('Pickup Location', validators=[DataRequired()])
    car_type = SelectField('Car Type', 
                          choices=[
                              ('economy', 'Economy'),
                              ('compact', 'Compact'),
                              ('midsize', 'Midsize'),
                              ('suv', 'SUV'),
                              ('luxury', 'Luxury')
                          ],
                          validators=[DataRequired()])
    pickup_date = DateField('Pickup Date', validators=[DataRequired()], format='%Y-%m-%d')
    return_date = DateField('Return Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Book Car')
    
    def validate_pickup_date(self, field):
        if field.data < date.today():
            raise ValidationError('Pickup date cannot be in the past')
            
    def validate_return_date(self, field):
        if field.data < self.pickup_date.data:
            raise ValidationError('Return date must be after pickup date')
