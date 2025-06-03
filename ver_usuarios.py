from app import create_app
from app.models import Usuario

app = create_app()

with app.app_context():
    usuarios = Usuario.query.all()
    print("=== USUARIOS REGISTRADOS ===")
    for usuario in usuarios:
        print(f"• Email: {usuario.email}")
        print(f"  Nombre: {usuario.nombre}")
        print(f"  Teléfono: {usuario.telefono}")
        print(f"  ID: {usuario.id}")
        print("-" * 30)