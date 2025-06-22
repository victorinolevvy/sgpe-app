from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, IntegerField, SelectField, SelectMultipleField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from wtforms.widgets import ListWidget, CheckboxInput
from sgpe.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Nome de Utilizador', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Esse nome de utilizador já existe. Por favor, escolha um diferente.')

    def validate_email(self, email):
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
    location_province = SelectField('Província', choices=[], validators=[DataRequired()])
    location_district = SelectField('Distrito', choices=[], validators=[DataRequired()])
    location_admin_post = SelectField('Posto Administrativo', choices=[], validators=[DataRequired()])
    generation_capacity_kW = FloatField('Capacidade de Geração (kW)', validators=[DataRequired()])
    storage_capacity_kWh = FloatField('Capacidade de Armazenamento (kWh)', validators=[DataRequired()])
    
    network_type = SelectMultipleField(
        'Tipo de Rede', 
        choices=[('Média Tensão', 'Média Tensão'), ('Baixa Tensão', 'Baixa Tensão')],
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
        validators=[DataRequired()]
    )

    mv_voltage_level = SelectField(
        'Nível de Tensão da Média Tensão (kV)',
        choices=[
            ('', 'Selecione o Nível de Tensão'),
            ('6.6', '6.6 kV'),
            ('11', '11 kV'),
            ('22', '22 kV'),
            ('33', '33 kV')
        ],
        validators=[Optional()]
    )

    lv_network_type = RadioField(
        'Tipo de Rede de Baixa Tensão',
        choices=[
            ('Trifásica', '380/220 V (Trifásica)'),
            ('Monofásica', '220 V (Monofásica)')
        ],
        validators=[Optional()]
    )

    num_connections = IntegerField('Número de Ligações', validators=[DataRequired()])
    submit = SubmitField('Criar Projeto')

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        if 'Média Tensão' in self.network_type.data and not self.mv_voltage_level.data:
            self.mv_voltage_level.errors.append('É obrigatório selecionar o nível de tensão para Média Tensão.')
            return False

        if 'Baixa Tensão' in self.network_type.data and not self.lv_network_type.data:
            self.lv_network_type.errors.append('É obrigatório selecionar o tipo de rede para Baixa Tensão.')
            return False
            
        return True
