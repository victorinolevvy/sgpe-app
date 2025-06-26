from datetime import datetime
from sgpe import db, login_manager, bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    projects = db.relationship('Project', backref='author', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class ProjectType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    projects = db.relationship('Project', backref='project_type', lazy=True)

    def __repr__(self):
        return f"ProjectType('{self.name}')"

# Tabela de associação para a relação muitos-para-muitos entre Contrato and Projeto
contract_projects = db.Table('contract_projects',
    db.Column('contract_id', db.Integer, db.ForeignKey('contract.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_type_id = db.Column(db.Integer, db.ForeignKey('project_type.id'), nullable=False)
    location_province = db.Column(db.String(50), nullable=False)
    location_district = db.Column(db.String(50), nullable=False)
    location_admin_post = db.Column(db.String(50), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relação com Contratos
    contracts = db.relationship(
        'Contract',
        secondary=contract_projects,
        back_populates='projects'
    )

    def __repr__(self):
        return f"Project('{self.name}', '{self.location_province}')"

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    contracts = db.relationship('Contract', backref='supplier_info', lazy=True)

    def __repr__(self):
        return f"Supplier('{self.name}')"

class ContractType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True) 
    contracts = db.relationship('Contract', backref='contract_type_info', lazy=True)

    def __repr__(self):
        return f"ContractType('{self.name}')"

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contract_number = db.Column(db.String(50), unique=True, nullable=False)
    contract_type_id = db.Column(db.Integer, db.ForeignKey('contract_type.id'), nullable=False)
    contract_value = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    document_filename = db.Column(db.String(200), nullable=True) # Campo para o nome do ficheiro
    # Relação com Projetos
    projects = db.relationship(
        'Project',
        secondary=contract_projects,
        back_populates='contracts'
    )

    def __repr__(self):
        return f"Contract('{self.contract_number}', '{self.contract_type_info.name}', '{self.supplier_info.name}', '{self.contract_value}')"

class ContractItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(50), nullable=False)  # Ex: 'unidades', 'metros', 'kg'
    unit_price = db.Column(db.Float, nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=False)
    allocations = db.relationship('Allocation', backref='item', lazy=True, cascade="all, delete-orphan")

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    @property
    def allocated_quantity(self):
        return sum(allocation.quantity for allocation in self.allocations)

    @property
    def available_quantity(self):
        return self.quantity - self.allocated_quantity

    def __repr__(self):
        return f"ContractItem('{self.name}', Qty: {self.quantity})"

class Allocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    allocation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    item_id = db.Column(db.Integer, db.ForeignKey('contract_item.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    project = db.relationship('Project', backref='allocations')

    def __repr__(self):
        return f"Allocation(Item ID: {self.item_id} to Project ID: {self.project_id}, Qty: {self.quantity})"
