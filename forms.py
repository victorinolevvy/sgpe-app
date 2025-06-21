from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        from app import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        from app import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    location_province = StringField('Province', validators=[DataRequired()])
    location_district = StringField('District', validators=[DataRequired()])
    location_admin_post = StringField('Administrative Post', validators=[DataRequired()])
    generation_capacity_kW = FloatField('Generation Capacity (kW)', validators=[DataRequired()])
    storage_capacity_kWh = FloatField('Storage Capacity (kWh)', validators=[DataRequired()])
    network_type = StringField('Network Type', validators=[DataRequired()])
    mv_voltage_kV = FloatField('MV Voltage (kV)')
    lv_voltage_V = IntegerField('LV Voltage (V)')
    num_connections = IntegerField('Number of Connections', validators=[DataRequired()])
    submit = SubmitField('Create Project')
