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

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location_province = db.Column(db.String(50), nullable=False)
    location_district = db.Column(db.String(50), nullable=False)
    location_admin_post = db.Column(db.String(50), nullable=False)
    generation_capacity_kW = db.Column(db.Float, nullable=False)
    storage_capacity_kWh = db.Column(db.Float, nullable=False)
    network_type = db.Column(db.String(100), nullable=False)
    mv_voltage_level = db.Column(db.String(10), nullable=True)
    lv_network_type = db.Column(db.String(20), nullable=True)
    num_connections = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Project('{self.name}', '{self.location_province}')"
