from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Utilizador', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registar')

    def validate_username(self, username):
        from app import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Esse nome de utilizador já existe. Por favor, escolha um diferente.')

    def validate_email(self, email):
        from app import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Esse email já existe. Por favor, escolha um diferente.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')

class ProjectForm(FlaskForm):
    name = StringField('Nome do Projeto', validators=[DataRequired()])
    location_province = StringField('Província', validators=[DataRequired()])
    location_district = StringField('Distrito', validators=[DataRequired()])
    location_admin_post = StringField('Posto Administrativo', validators=[DataRequired()])
    generation_capacity_kW = FloatField('Capacidade de Geração (kW)', validators=[DataRequired()])
    storage_capacity_kWh = FloatField('Capacidade de Armazenamento (kWh)', validators=[DataRequired()])
    network_type = StringField('Tipo de Rede', validators=[DataRequired()])
    mv_voltage_kV = FloatField('Tensão da MT (kV)')
    lv_voltage_V = IntegerField('Tensão da BT (V)')
    num_connections = IntegerField('Número de Ligações', validators=[DataRequired()])
    submit = SubmitField('Criar Projeto')
