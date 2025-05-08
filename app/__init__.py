import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import config

db = SQLAlchemy()
migrate = Migrate()

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [] 

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)



def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    return app