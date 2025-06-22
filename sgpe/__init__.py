from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Por favor, faça o login para aceder a esta página.'


def create_app(config_name):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from sgpe.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from sgpe.main.routes import main
    app.register_blueprint(main)

    return app
