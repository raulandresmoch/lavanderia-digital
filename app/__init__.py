from flask import Flask
from .extensions import db
from .routes import main
import os

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lavanderia.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get("SECRET_KEY", "supersecreto")


    db.init_app(app)
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app
