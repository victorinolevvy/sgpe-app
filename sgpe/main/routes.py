from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_login import login_user, current_user, logout_user, login_required
from sgpe import db, bcrypt
from sgpe.models import User, Project
from sgpe.forms import RegistrationForm, LoginForm, ProjectForm
from sgpe.locations import LOCATIONS

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('dashboard.html', projects=projects)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # O primeiro utilizador registado é o administrador
        is_admin = not User.query.first()
        user = User(username=form.username.data, email=form.email.data, password=form.password.data, is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash(f'Conta criada para {form.username.data}!', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Registar', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login sem sucesso. Por favor, verifique o e-mail e a senha', 'danger')
    return render_template('login.html', title='Login', form=form)


@main.route('/logout')
def logout():
    logout_user()
    flash('Sessão terminada com sucesso.', 'success')
    return redirect(url_for('main.home'))


@main.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if not current_user.is_admin:
        flash('Não tem permissão para aceder a esta página.', 'danger')
        return redirect(url_for('main.home'))
    form = ProjectForm()

    # Popula as províncias em todas as requisições
    form.location_province.choices = [('', 'Selecione a Província')] + [(p, p) for p in LOCATIONS.keys()]

    # Se a requisição for POST (submissão do formulário), tentamos popular os campos
    # de distrito e posto administrativo baseados nos dados enviados.
    # Isto é crucial para repopular os campos em caso de falha de validação.
    if request.method == 'POST':
        province = request.form.get('location_province')
        district = request.form.get('location_district')

        form.location_district.choices = [('', 'Selecione o Distrito')]
        if province and province in LOCATIONS:
            form.location_district.choices.extend([(d, d) for d in LOCATIONS[province].keys()])

        form.location_admin_post.choices = [('', 'Selecione o Posto Administrativo')]
        if province and district and district in LOCATIONS.get(province, {}):
            form.location_admin_post.choices.extend([(p, p) for p in LOCATIONS[province][district]])
    else:
        # Para uma requisição GET, apenas definimos as escolhas vazias com placeholders.
        form.location_district.choices = [('', 'Selecione o Distrito')]
        form.location_admin_post.choices = [('', 'Selecione o Posto Administrativo')]

    if form.validate_on_submit():
        # Converte a lista de tipos de rede para uma string
        network_type_str = ", ".join(form.network_type.data)

        project = Project(
            name=form.name.data,
            location_province=form.location_province.data,
            location_district=form.location_district.data,
            location_admin_post=form.location_admin_post.data,
            generation_capacity_kW=form.generation_capacity_kW.data,
            storage_capacity_kWh=form.storage_capacity_kWh.data,
            network_type=network_type_str,
            mv_voltage_level=form.mv_voltage_level.data if 'Média Tensão' in form.network_type.data else None,
            lv_network_type=form.lv_network_type.data if 'Baixa Tensão' in form.network_type.data else None,
            num_connections=form.num_connections.data,
            author=current_user
        )
        db.session.add(project)
        db.session.commit()
        flash('Projeto criado com sucesso!', 'success')
        return redirect(url_for('main.home'))

    return render_template('create_project.html', title='Novo Projeto', form=form, legend='Novo Projeto')


@main.route('/project/<int:project_id>')
def project(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project.html', title=project.name, project=project)


@main.route("/project/<int:project_id>/update", methods=['GET', 'POST'])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.home'))
    
    form = ProjectForm()
    form.submit.label.text = 'Atualizar Projeto' # Altera o rótulo do botão

    # Popula as províncias em todas as requisições
    form.location_province.choices = [('', 'Selecione a Província')] + [(p, p) for p in LOCATIONS.keys()]

    # Lógica para popular dinamicamente os dropdowns, tanto em GET (para exibir dados existentes)
    # quanto em POST (para repopular em caso de erro de validação)
    if request.method == 'POST':
        province = request.form.get('location_province')
        district = request.form.get('location_district')
    else: # GET
        province = project.location_province
        district = project.location_district

    form.location_district.choices = [('', 'Selecione o Distrito')]
    if province and province in LOCATIONS:
        form.location_district.choices.extend([(d, d) for d in LOCATIONS[province].keys()])

    form.location_admin_post.choices = [('', 'Selecione o Posto Administrativo')]
    if province and district and district in LOCATIONS.get(province, {}):
        form.location_admin_post.choices.extend([(p, p) for p in LOCATIONS[province][district]])

    if form.validate_on_submit():
        project.name = form.name.data
        project.location_province = form.location_province.data
        project.location_district = form.location_district.data
        project.location_admin_post = form.location_admin_post.data
        project.generation_capacity_kW = form.generation_capacity_kW.data
        project.storage_capacity_kWh = form.storage_capacity_kWh.data
        project.network_type = ", ".join(form.network_type.data)
        project.mv_voltage_level = form.mv_voltage_level.data if 'Média Tensão' in form.network_type.data else None
        project.lv_network_type = form.lv_network_type.data if 'Baixa Tensão' in form.network_type.data else None
        project.num_connections = form.num_connections.data
        db.session.commit()
        flash('O projeto foi atualizado com sucesso!', 'success')
        return redirect(url_for('main.project', project_id=project.id))
    elif request.method == 'GET':
        form.name.data = project.name
        form.location_province.data = project.location_province
        form.location_district.data = project.location_district
        form.location_admin_post.data = project.location_admin_post
        form.generation_capacity_kW.data = project.generation_capacity_kW
        form.storage_capacity_kWh.data = project.storage_capacity_kWh
        form.network_type.data = [item.strip() for item in project.network_type.split(',')]
        form.mv_voltage_level.data = project.mv_voltage_level
        form.lv_network_type.data = project.lv_network_type
        form.num_connections.data = project.num_connections

    return render_template('create_project.html', title='Atualizar Projeto',
                           form=form, legend='Atualizar Projeto', project_id=project_id)


@main.route("/project/<int:project_id>/delete", methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.home'))
    db.session.delete(project)
    db.session.commit()
    flash('O projeto foi apagado com sucesso!', 'success')
    return redirect(url_for('main.home'))


@main.route('/api/districts/<province>')
def get_districts(province):
    if province not in LOCATIONS:
        return jsonify([])
    districts = list(LOCATIONS[province].keys())
    return jsonify(districts)


@main.route('/api/admin_posts/<province>/<district>')
def get_admin_posts(province, district):
    if province not in LOCATIONS or district not in LOCATIONS[province]:
        return jsonify([])
    admin_posts = LOCATIONS[province][district]
    return jsonify(admin_posts)
