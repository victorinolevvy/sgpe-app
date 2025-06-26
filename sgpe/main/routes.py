import os
import secrets
from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify, abort, current_app, send_from_directory
from flask_login import login_user, current_user, logout_user, login_required
from sgpe import db, bcrypt
from sgpe.models import User, Project, Contract, Supplier, ContractType, ProjectType
from sqlalchemy import func
from sgpe.forms import RegistrationForm, LoginForm, ProjectForm, ContractForm, SupplierForm, ContractTypeForm, ProjectTypeForm
from sgpe.locations import LOCATIONS
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    # Dados para o dashboard
    total_projects = Project.query.count()
    total_contracts = Contract.query.count()
    total_contract_value = db.session.query(func.sum(Contract.contract_value)).scalar() or 0

    # Dados para o gráfico de projetos por província
    projects_by_province = db.session.query(Project.location_province, func.count(Project.id)).group_by(Project.location_province).all()
    province_labels = [row[0] for row in projects_by_province]
    province_data = [row[1] for row in projects_by_province]

    # Lógica de pesquisa e paginação para a lista de projetos
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    query = Project.query

    if search_query:
        query = query.filter(Project.name.ilike(f'%{search_query}%'))

    projects = query.order_by(Project.date_posted.desc()).paginate(page=page, per_page=5)

    return render_template(
        'dashboard.html',
        title='Dashboard',
        projects=projects,
        search_query=search_query,
        total_projects=total_projects,
        total_contracts=total_contracts,
        total_contract_value=total_contract_value,
        province_labels=province_labels,
        province_data=province_data
    )


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
        project = Project(
            name=form.name.data,
            project_type_id=form.project_type_id.data.id,
            location_province=form.location_province.data,
            location_district=form.location_district.data,
            location_admin_post=form.location_admin_post.data,
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
    form.submit.label.text = 'Atualizar Projeto'

    # Popula as províncias em todas as requisições
    form.location_province.choices = [('', 'Selecione a Província')] + [(p, p) for p in LOCATIONS.keys()]

    # Lógica para repopular os dropdowns em caso de erro de validação no POST
    if request.method == 'POST':
        province = request.form.get('location_province')
        district = request.form.get('location_district')
        
        districts_choices = [('', 'Selecione o Distrito')]
        if province in LOCATIONS:
            districts_choices.extend([(d, d) for d in LOCATIONS[province].keys()])
        form.location_district.choices = districts_choices

        admin_posts_choices = [('', 'Selecione o Posto Administrativo')]
        if province and district and district in LOCATIONS.get(province, {}):
            admin_posts_choices.extend([(p, p) for p in LOCATIONS[province][district]])
        form.location_admin_post.choices = admin_posts_choices

    if form.validate_on_submit():
        project.name = form.name.data
        project.project_type_id = form.project_type_id.data.id
        project.location_province = form.location_province.data
        project.location_district = form.location_district.data
        project.location_admin_post = form.location_admin_post.data
        db.session.commit()
        flash('O projeto foi atualizado com sucesso!', 'success')
        return redirect(url_for('main.project', project_id=project.id))
    
    elif request.method == 'GET':
        # Popula o formulário com os dados existentes do projeto
        
        # Popula as escolhas dos dropdowns dinâmicos
        province = project.location_province
        district = project.location_district

        districts_choices = [('', 'Selecione o Distrito')]
        if province in LOCATIONS:
            districts_choices.extend([(d, d) for d in LOCATIONS[province].keys()])
        form.location_district.choices = districts_choices

        admin_posts_choices = [('', 'Selecione o Posto Administrativo')]
        if province and district and district in LOCATIONS.get(province, {}):
            admin_posts_choices.extend([(p, p) for p in LOCATIONS[province][district]])
        form.location_admin_post.choices = admin_posts_choices

        # Define os valores selecionados para todos os campos
        form.name.data = project.name
        form.project_type_id.data = project.project_type
        form.location_province.data = province
        form.location_district.data = district
        form.location_admin_post.data = project.location_admin_post

    return render_template('create_project.html', title='Atualizar Projeto',
                           form=form, legend='Atualizar Projeto', project_id=project_id)


@main.route("/project/<int:project_id>/delete", methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.author != current_user:
        abort(403)
    db.session.delete(project)
    db.session.commit()
    flash('O seu projeto foi apagado!', 'success')
    return redirect(url_for('main.home'))

# Rotas para Tipos de Projeto
@main.route("/project_types")
@login_required
def project_types():
    if not current_user.is_admin:
        abort(403)
    page = request.args.get('page', 1, type=int)
    project_types = ProjectType.query.order_by(ProjectType.name.asc()).paginate(page=page, per_page=10)
    return render_template('project_types.html', project_types=project_types, title='Tipos de Projeto')

@main.route("/project_types/new", methods=['GET', 'POST'])
@login_required
def add_project_type():
    if not current_user.is_admin:
        abort(403)
    form = ProjectTypeForm()
    if form.validate_on_submit():
        project_type = ProjectType(name=form.name.data, description=form.description.data)
        db.session.add(project_type)
        db.session.commit()
        flash('Tipo de Projeto adicionado com sucesso!', 'success')
        return redirect(url_for('main.project_types'))
    return render_template('add_project_type.html', title='Adicionar Tipo de Projeto', form=form, legend='Novo Tipo de Projeto')

@main.route("/project_types/<int:project_type_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_project_type(project_type_id):
    project_type = ProjectType.query.get_or_404(project_type_id)
    if not current_user.is_admin:
        abort(403)
    form = ProjectTypeForm()
    if form.validate_on_submit():
        project_type.name = form.name.data
        project_type.description = form.description.data
        db.session.commit()
        flash('Tipo de Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('main.project_types'))
    elif request.method == 'GET':
        form.name.data = project_type.name
        form.description.data = project_type.description
    return render_template('add_project_type.html', title='Editar Tipo de Projeto', form=form, legend='Editar Tipo de Projeto')

@main.route("/project_types/<int:project_type_id>/delete", methods=['POST'])
@login_required
def delete_project_type(project_type_id):
    project_type = ProjectType.query.get_or_404(project_type_id)
    if not current_user.is_admin:
        abort(403)
    if project_type.projects:
        flash('Não é possível apagar este tipo de projeto, pois existem projetos associados a ele.', 'danger')
        return redirect(url_for('main.project_types'))
    db.session.delete(project_type)
    db.session.commit()
    flash('Tipo de Projeto apagado com sucesso!', 'success')
    return redirect(url_for('main.project_types'))


# Rotas para Fornecedores
@main.route('/suppliers')
@login_required
def suppliers():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    query = Supplier.query

    if search_query:
        query = query.filter(Supplier.name.ilike(f'%{search_query}%'))

    suppliers = query.order_by(Supplier.name).paginate(page=page, per_page=10)
    return render_template('suppliers.html', title='Fornecedores', suppliers=suppliers, search_query=search_query)

@main.route('/supplier/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if not current_user.is_admin:
        flash('Não tem permissão para aceder a esta página.', 'danger')
        return redirect(url_for('main.home'))
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(name=form.name.data, contact_person=form.contact_person.data,
                            email=form.email.data, phone=form.phone.data)
        db.session.add(supplier)
        db.session.commit()
        flash('Fornecedor adicionado com sucesso!', 'success')
        return redirect(url_for('main.suppliers'))
    return render_template('add_supplier.html', title='Adicionar Fornecedor', form=form, legend='Novo Fornecedor')

@main.route('/supplier/<int:supplier_id>/update', methods=['GET', 'POST'])
@login_required
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.suppliers'))
    form = SupplierForm(obj=supplier)
    if form.validate_on_submit():
        form.populate_obj(supplier)
        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('main.suppliers'))
    return render_template('add_supplier.html', title='Atualizar Fornecedor',
                           form=form, legend='Atualizar Fornecedor')

@main.route('/supplier/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.suppliers'))
    db.session.delete(supplier)
    db.session.commit()
    flash('Fornecedor apagado com sucesso!', 'success')
    return redirect(url_for('main.suppliers'))


# Rotas para Tipos de Contrato
@main.route('/contract_types')
@login_required
def contract_types():
    """Exibe uma lista de todos os tipos de contrato."""
    page = request.args.get('page', 1, type=int)
    contract_types = ContractType.query.order_by(ContractType.name).paginate(page=page, per_page=10)
    return render_template('contract_types.html', title='Tipos de Contrato', contract_types=contract_types)

@main.route('/contract_type/new', methods=['GET', 'POST'])
@login_required
def new_contract_type():
    """Cria um novo tipo de contrato."""
    if not current_user.is_admin:
        flash('Não tem permissão para aceder a esta página.', 'danger')
        return redirect(url_for('main.home'))
    form = ContractTypeForm()
    if form.validate_on_submit():
        contract_type = ContractType(name=form.name.data, description=form.description.data)
        db.session.add(contract_type)
        db.session.commit()
        flash('Tipo de contrato criado com sucesso!', 'success')
        return redirect(url_for('main.contract_types'))
    return render_template('add_contract_type.html', title='Novo Tipo de Contrato', form=form, legend='Novo Tipo de Contrato')

@main.route('/contract_type/<int:type_id>/update', methods=['GET', 'POST'])
@login_required
def update_contract_type(type_id):
    """Atualiza um tipo de contrato existente."""
    contract_type = ContractType.query.get_or_404(type_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.contract_types'))
    form = ContractTypeForm(obj=contract_type)
    if form.validate_on_submit():
        contract_type.name = form.name.data
        contract_type.description = form.description.data
        db.session.commit()
        flash('Tipo de contrato atualizado com sucesso!', 'success')
        return redirect(url_for('main.contract_types'))
    return render_template('add_contract_type.html', title='Atualizar Tipo de Contrato', form=form, legend='Atualizar Tipo de Contrato')

@main.route('/contract_type/<int:type_id>/delete', methods=['POST'])
@login_required
def delete_contract_type(type_id):
    """Apaga um tipo de contrato."""
    contract_type = ContractType.query.get_or_404(type_id)
    if not current_user.is_admin:
        abort(403)
    if contract_type.contracts:
        flash('Não é possível apagar este tipo de contrato, pois existem contratos associados a ele.', 'danger')
        return redirect(url_for('main.contract_types'))
    db.session.delete(contract_type)
    db.session.commit()
    flash('Tipo de contrato apagado com sucesso!', 'success')
    return redirect(url_for('main.contract_types'))


# Rotas para Contratos
@main.route('/contracts')
@login_required
def contracts():
    """Exibe uma lista de todos os contratos."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    query = Contract.query

    if search_query:
        # Pesquisa por número do contrato ou nome do fornecedor
        query = query.join(Supplier).filter(
            (Contract.contract_number.ilike(f'%{search_query}%')) |
            (Supplier.name.ilike(f'%{search_query}%'))
        )

    contracts = query.order_by(Contract.start_date.desc()).paginate(page=page, per_page=10)
    return render_template('contracts.html', title='Contratos', contracts=contracts, search_query=search_query)


@main.route('/contract/add', methods=['GET', 'POST'])
@login_required
def add_contract():
    if not current_user.is_admin:
        flash('Não tem permissão para aceder a esta página.', 'danger')
        return redirect(url_for('main.home'))
    form = ContractForm()
    if form.validate_on_submit():
        document_filename = None
        if form.document.data:
            document_filename = save_document(form.document.data)

        contract = Contract(
            contract_number=form.contract_number.data,
            contract_type_id=form.contract_type.data.id,
            supplier_id=form.supplier.data.id,
            contract_value=form.contract_value.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            document_filename=document_filename
        )
        # Associa os projetos selecionados
        for project in form.projects.data:
            contract.projects.append(project)
            
        db.session.add(contract)
        db.session.commit()
        flash('Contrato adicionado com sucesso!', 'success')
        return redirect(url_for('main.contracts'))
    return render_template('add_contract.html', title='Adicionar Contrato', form=form, legend='Novo Contrato')


@main.route('/contract/<int:contract_id>/update', methods=['GET', 'POST'])
@login_required
def update_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.contracts'))
    form = ContractForm(obj=contract)
    
    if form.validate_on_submit():
        if form.document.data:
            # Apaga o documento antigo se um novo for enviado
            if contract.document_filename:
                old_document_path = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'], contract.document_filename)
                if os.path.exists(old_document_path):
                    os.remove(old_document_path)
            contract.document_filename = save_document(form.document.data)

        contract.contract_number = form.contract_number.data
        contract.contract_type_id = form.contract_type.data.id
        contract.supplier_id = form.supplier.data.id
        contract.contract_value = form.contract_value.data
        contract.start_date = form.start_date.data
        contract.end_date = form.end_date.data
        
        # Atualiza os projetos associados
        contract.projects = form.projects.data

        db.session.commit()
        flash('Contrato atualizado com sucesso!', 'success')
        return redirect(url_for('main.contracts'))
    
    elif request.method == 'GET':
        # Popula o formulário com os dados existentes
        form.contract_number.data = contract.contract_number
        form.contract_type.data = contract.contract_type_info
        form.supplier.data = contract.supplier_info
        form.contract_value.data = contract.contract_value
        form.start_date.data = contract.start_date
        form.end_date.data = contract.end_date
        form.projects.data = contract.projects

    return render_template('add_contract.html', title='Atualizar Contrato', form=form, legend='Atualizar Contrato')


@main.route('/contract/<int:contract_id>/delete', methods=['POST'])
@login_required
def delete_contract(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    if not current_user.is_admin:
        flash('Não tem permissão para executar esta ação.', 'danger')
        return redirect(url_for('main.contracts'))
    
    # Apaga o documento associado, se existir
    if contract.document_filename:
        document_path = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'], contract.document_filename)
        if os.path.exists(document_path):
            os.remove(document_path)

    db.session.delete(contract)
    db.session.commit()
    flash('Contrato apagado com sucesso!', 'success')
    return redirect(url_for('main.contracts'))


def save_document(form_document):
    """Salva o documento de contrato no sistema de ficheiros."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_document.filename)
    document_fn = random_hex + f_ext
    document_path = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'], document_fn)
    
    # Garante que o diretório de upload existe
    os.makedirs(os.path.dirname(document_path), exist_ok=True)
    
    form_document.save(document_path)
    
    return document_fn

@main.route('/uploads/<filename>')
@login_required
def download_document(filename):
    """Serve os ficheiros de upload para download."""
    upload_dir = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'])
    return send_from_directory(upload_dir, filename)


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
