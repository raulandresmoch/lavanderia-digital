from flask import Flask
from .extensions import db
from .routes import main

def create_app():
    # Cambiar la ruta de templates para que apunte al directorio templates/ en la raíz
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lavanderia.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = "tu_clave_secreta"

    db.init_app(app)
    
    # Registrar blueprints
    app.register_blueprint(main)
    
    # Importar y registrar rutas admin
    from .admin_routes import admin_bp
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app