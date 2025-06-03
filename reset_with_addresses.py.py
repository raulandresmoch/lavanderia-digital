"""
Script para resetear la base de datos con el nuevo sistema de direcciones múltiples
"""

import os
import time
import shutil

def reset_with_addresses():
    print("🔄 Reseteando base de datos para direcciones múltiples...")
    
    # Eliminar base de datos actual
    db_path = 'instance/lavanderia.db'
    if os.path.exists(db_path):
        try:
            backup_path = f'instance/lavanderia_backup_{int(time.time())}.db'
            shutil.copy2(db_path, backup_path)
            os.remove(db_path)
            print(f"✅ Base de datos anterior respaldada en {backup_path}")
        except Exception as e:
            print(f"⚠️  Error respaldando DB: {e}")
    
    # Importar y crear nueva estructura
    from app import create_app
    from app.models import db, TipoPrenda, Configuracion, Admin, Usuario, DireccionUsuario
    from werkzeug.security import generate_password_hash
    
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✅ Nueva estructura de base de datos creada")
        
        # Crear tipos de prendas
        tipos_prenda = [
            {
                'nombre': 'Ropa Normal',
                'precio_por_kg': 25.0,
                'tiempo_lavado_horas': 24,
                'descripcion': 'Ropa casual, camisetas, pantalones, ropa interior'
            },
            {
                'nombre': 'Ropa Delicada',
                'precio_por_kg': 35.0,
                'tiempo_lavado_horas': 48,
                'descripcion': 'Seda, lana, prendas que requieren cuidado especial'
            },
            {
                'nombre': 'Edredones y Cobijas',
                'precio_por_kg': 40.0,
                'tiempo_lavado_horas': 48,
                'descripcion': 'Edredones, cobijas gruesas, almohadas grandes'
            },
            {
                'nombre': 'Sábanas y Toallas',
                'precio_por_kg': 20.0,
                'tiempo_lavado_horas': 24,
                'descripcion': 'Juegos de sábanas, toallas de baño, manteles'
            },
            {
                'nombre': 'Ropa de Trabajo',
                'precio_por_kg': 30.0,
                'tiempo_lavado_horas': 36,
                'descripcion': 'Uniformes, overoles, ropa con manchas difíciles'
            },
            {
                'nombre': 'Cortinas',
                'precio_por_kg': 45.0,
                'tiempo_lavado_horas': 72,
                'descripcion': 'Cortinas de casa, persianas de tela'
            }
        ]
        
        for tipo_data in tipos_prenda:
            tipo = TipoPrenda(**tipo_data)
            db.session.add(tipo)
        
        # Configuraciones del sistema
        configuraciones = [
            {
                'clave': 'horario_recoleccion',
                'valor': 'Mañana (9:00-12:00)',
                'descripcion': 'Horario fijo de recolección'
            },
            {
                'clave': 'horario_entrega',
                'valor': 'Tarde (14:00-18:00)',
                'descripcion': 'Horario fijo de entrega'
            },
            {
                'clave': 'dias_laborales',
                'valor': '1,2,3,4,5,6',
                'descripcion': 'Días de la semana que trabajamos (1=Lunes, 6=Sábado)'
            },
            {
                'clave': 'telefono_contacto',
                'valor': '+52 55 1234-5678',
                'descripcion': 'Teléfono de contacto para clientes'
            },
            {
                'clave': 'email_contacto',
                'valor': 'soporte@lavanderia-digital.com',
                'descripcion': 'Email de soporte'
            },
            {
                'clave': 'zona_cobertura',
                'valor': 'Benito Juárez, Roma Norte, Condesa, Del Valle',
                'descripcion': 'Zonas donde damos servicio'
            }
        ]
        
        for config_data in configuraciones:
            config = Configuracion(**config_data)
            db.session.add(config)
        
        # Crear admin
        admin = Admin(
            usuario="admin",
            contrasena=generate_password_hash("admin123"),
            nombre="Administrador",
            email="admin@lavanderia-digital.com"
        )
        db.session.add(admin)
        
        # Crear usuario de ejemplo con direcciones múltiples
        usuario_ejemplo = Usuario(
            nombre="Usuario de Prueba",
            email="usuario@test.com",
            contrasena=generate_password_hash("123456"),
            telefono="55 1234 5678",
            ubicacion="Roma Norte, Ciudad de México",  # Por compatibilidad
            latitud=19.4158,
            longitud=-99.1601,
            coordenadas_verificadas=True
        )
        db.session.add(usuario_ejemplo)
        db.session.flush()  # Para obtener ID
        
        # Direcciones de ejemplo
        direcciones_ejemplo = [
            {
                'usuario_id': usuario_ejemplo.id,
                'nombre': 'Casa',
                'direccion': 'Av. Álvaro Obregón 123, Roma Norte, Ciudad de México',
                'latitud': 19.4158,
                'longitud': -99.1601,
                'es_principal': True,
                'verificada': True,
                'notas': 'Casa blanca con portón verde'
            },
            {
                'usuario_id': usuario_ejemplo.id,
                'nombre': 'Trabajo',
                'direccion': 'Paseo de la Reforma 250, Juárez, Ciudad de México',
                'latitud': 19.4284,
                'longitud': -99.1398,
                'es_principal': False,
                'verificada': True,
                'notas': 'Torre corporativa, piso 15'
            },
            {
                'usuario_id': usuario_ejemplo.id,
                'nombre': 'Casa de mamá',
                'direccion': 'Calle Orizaba 45, Roma Norte, Ciudad de México',
                'latitud': 19.4195,
                'longitud': -99.1589,
                'es_principal': False,
                'verificada': True,
                'notas': 'Casa amarilla con jardín al frente'
            }
        ]
        
        for direccion_data in direcciones_ejemplo:
            direccion = DireccionUsuario(**direccion_data)
            db.session.add(direccion)
        
        try:
            db.session.commit()
            
            print("✅ Base de datos inicializada correctamente!")
            print(f"✅ Creados {len(tipos_prenda)} tipos de prendas")
            print(f"✅ Creadas {len(configuraciones)} configuraciones")
            print("✅ Usuario admin creado (admin/admin123)")
            print("✅ Usuario de prueba creado (usuario@test.com/123456)")
            print("✅ 3 direcciones de ejemplo agregadas")
            
            print("\n🏠 Direcciones de ejemplo:")
            for direccion_data in direcciones_ejemplo:
                principal = " (Principal)" if direccion_data['es_principal'] else ""
                print(f"   - {direccion_data['nombre']}{principal}: {direccion_data['direccion']}")
            
            print("\n🗺️ Nuevas funcionalidades:")
            print("   ✅ Sistema de direcciones múltiples")
            print("   ✅ Geocodificación con mapas interactivos")
            print("   ✅ Validación de zona de cobertura")
            print("   ✅ Gestión completa de direcciones por usuario")
            print("   ✅ Selección inteligente en cotización")
            
            print("\n🚀 Para probar:")
            print("   1. Ejecuta: python run.py")
            print("   2. Regístrate o usa: usuario@test.com / 123456")
            print("   3. Ve a 'Mis Direcciones' para gestionar ubicaciones")
            print("   4. Usa 'Cotizar' con selección de direcciones")
            print("   5. Panel admin: admin / admin123")
            
        except Exception as e:
            print(f"❌ Error guardando datos: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    success = reset_with_addresses()
    if success:
        print("\n🎉 ¡Sistema de direcciones múltiples listo!")
    else:
        print("\n❌ Error en la inicialización")
        print("💡 Asegúrate de que Flask no esté ejecutándose")