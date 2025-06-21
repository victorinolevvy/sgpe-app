from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from forms import RegistrationForm, LoginForm, ProjectForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key

# -- configuracao do banco de dados --
# -- difine o caminho para o arquivo do banco de dados SQLite --
# "sqlite:///site.db" significa que o banco de dados será criado no mesmo diretório do app.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# -- desativa o recurso de rastreamento de modificações do SQLAlchemy, pois consome muita memoria --
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# -- inicializa a extensao SQLAlchemy com a aplicacao Flask --
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -- definicao de modelos de dados para o projecto --

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Project(db.Model):

    # -- define uma tabela 'projects' no banco de dados --
    __tablename__ = 'projects'

    # -- define as colunas da tabela --

    id = db.Column(db.Integer, primary_key=True) # -- ID unico para cada projecto (chave primaria) --
    name = db.Column(db.String(100), nullable=False, unique=True) # -- Nome do projecto (string, nao pode ser nulo e deve ser unico) --
    location_province = db.Column(db.String(50), nullable=False) # -- Provincia --
    location_district = db.Column(db.String(50), nullable=False) # -- Distrito --
    location_admin_post = db.Column(db.String(50), nullable=False) # -- Posto Administrativo --

    # -- Detalhes da central fotovoltaica --
    generation_capacity_kW = db.Column(db.Float, nullable=False) # -- Capacidade de geracao (em KW) --
    storage_capacity_kWh = db.Column(db.Float, nullable=False) # -- Capacidade de armazenamento (em KWh) --

    # -- Detalhes da rede de distribuicao --
    network_type = db.Column(db.String(50), nullable=False) # -- Tipo de rede(Media tensao ou baixa tensao) --
    # -- Tensao da rede de media tensao  (se aplicavel) --
    mv_voltage_kV = db.Column(db.Float, nullable=True) # Ex: 6.6 , 11,22, 33 kV
    # -- Tensao da rede de baixa tensao (se aplicavel) --
    lv_voltage_V = db.Column(db.Integer, nullable=True) # Ex: 220V, 380V
    num_connections = db.Column(db.Integer, nullable=False) # -- Numero de ligacoes (clientes) --
    

    def __repr__(self):
        return f"Project('{self.name}', '{self.location_province}')"


@app.route('/')
@app.route('/home')
def home():
    projects = Project.query.all()
    return render_template('dashboard.html', projects=projects)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, location_province=form.location_province.data,
                          location_district=form.location_district.data, location_admin_post=form.location_admin_post.data,
                          generation_capacity_kW=form.generation_capacity_kW.data, storage_capacity_kWh=form.storage_capacity_kWh.data,
                          network_type=form.network_type.data, mv_voltage_kV=form.mv_voltage_kV.data,
                          lv_voltage_V=form.lv_voltage_V.data, num_connections=form.num_connections.data)
        db.session.add(project)
        db.session.commit()
        flash('Your project has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_project.html', title='New Project', form=form)


@app.route('/project/<int:project_id>')
def project(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project.html', title=project.name, project=project)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

