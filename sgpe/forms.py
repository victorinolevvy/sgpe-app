from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, IntegerField, SelectField, SelectMultipleField, RadioField, TextAreaField
from wtforms.fields import DateField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from sgpe import db # Adicionado para usar db.func
from sgpe.models import User, Supplier, Project, ContractType
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField


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
        validators=[Optional()]
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

        validation_ok = True
        if 'Média Tensão' in self.network_type.data and not self.mv_voltage_level.data:
            self.mv_voltage_level.errors.append('O nível de tensão de Média Tensão é obrigatório quando este tipo de rede é selecionado.')
            validation_ok = False
        
        if 'Baixa Tensão' in self.network_type.data and not self.lv_network_type.data:
            self.lv_network_type.errors.append('O tipo de rede de Baixa Tensão é obrigatório quando este tipo de rede é selecionado.')
            validation_ok = False
            
        return validation_ok

class SupplierForm(FlaskForm):
    name = StringField('Nome do Fornecedor/Empreiteiro', validators=[DataRequired()])
    contact_person = StringField('Pessoa de Contato', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Telefone', validators=[Optional()])
    submit = SubmitField('Salvar Fornecedor')

    def __init__(self, *args, **kwargs):
        super(SupplierForm, self).__init__(*args, **kwargs)
        self.obj_instance = kwargs.get('obj')

    def validate_name(self, name):
        # Pesquisa case-insensitive
        supplier = Supplier.query.filter(db.func.lower(Supplier.name) == db.func.lower(name.data)).first()
        if supplier:
            # Se estivermos a atualizar e o fornecedor encontrado for o mesmo que estamos a editar, está OK.
            if self.obj_instance and self.obj_instance.id == supplier.id:
                return
            # Caso contrário, é um nome duplicado.
            raise ValidationError('Este nome de fornecedor já existe. Por favor, escolha um diferente.')

def supplier_query():
    return Supplier.query

def project_query():
    return Project.query

def contract_type_query():
    return ContractType.query

class ContractForm(FlaskForm):
    contract_number = StringField('Número do Contrato', validators=[DataRequired()])
    contract_type = QuerySelectField('Tipo de Contrato', query_factory=contract_type_query, get_label='name', allow_blank=False, validators=[DataRequired()])
    supplier = QuerySelectField('Fornecedor/Empreiteiro', query_factory=supplier_query, get_label='name', allow_blank=False, validators=[DataRequired()])
    projects = QuerySelectMultipleField('Projetos Associados', query_factory=project_query, get_label='name', widget=ListWidget(prefix_label=False), option_widget=CheckboxInput())
    contract_value = FloatField('Valor do Contrato (MZN)', validators=[DataRequired()])
    start_date = DateField('Data de Início', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Data de Fim', format='%Y-%m-%d', validators=[Optional()])
    document = FileField('Documento do Contrato (PDF, Imagem)', validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Apenas ficheiros PDF e imagens são permitidos!'), Optional()])
    submit = SubmitField('Salvar Contrato')

class ContractTypeForm(FlaskForm):
    name = StringField('Nome do Tipo de Contrato', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Salvar')

    def __init__(self, *args, **kwargs):
        super(ContractTypeForm, self).__init__(*args, **kwargs)
        self.obj_instance = kwargs.get('obj')

    def validate_name(self, name):
        # Pesquisa case-insensitive
        contract_type = ContractType.query.filter(db.func.lower(ContractType.name) == db.func.lower(name.data)).first()
        if contract_type:
            # Se estivermos a atualizar e o tipo encontrado for o mesmo que estamos a editar, está OK.
            if self.obj_instance and self.obj_instance.id == contract_type.id:
                return
            # Caso contrário, é um nome duplicado.
            raise ValidationError('Este nome de tipo de contrato já existe. Por favor, escolha um diferente.')
