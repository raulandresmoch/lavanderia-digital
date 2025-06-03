from flask import Flask
from .extensions import db

def create_app():
    # CORRECCIÓN: Templates están en ../templates (relativo a app/)
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lavanderia.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = "tu_clave_secreta"

    db.init_app(app)
    
    # Registrar blueprints sin importaciones circulares
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app

def register_blueprints(app):
    """Registrar blueprints evitando importaciones circulares"""
    from .routes import main
    from .admin_routes import admin_bp
    
    app.register_blueprint(main)
    app.register_blueprint(admin_bp)