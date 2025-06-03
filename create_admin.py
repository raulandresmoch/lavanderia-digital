"""
Script para crear un usuario administrador
"""

from app import create_app
from app.models import db, Admin
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existe un admin
        if Admin.query.first():
            print("⚠️  Ya existe un usuario administrador.")
            admin_existente = Admin.query.first()
            print(f"Usuario: {admin_existente.usuario}")
            print(f"Nombre: {admin_existente.nombre}")
            return
        
        # Crear admin por defecto
        admin = Admin(
            usuario="admin",
            contrasena=generate_password_hash("admin123"),  # Cambiar en producción
            nombre="Administrador",
            email="admin@lavanderia-digital.com"
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Usuario administrador creado exitosamente!")
        print("🔐 Credenciales por defecto:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("🌐 Accede en: http://localhost:5000/admin/login")
        print("\n⚠️  IMPORTANTE: Cambia estas credenciales en producción")

if __name__ == "__main__":
    create_admin_user()