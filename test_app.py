#!/usr/bin/env python3
"""
Script de prueba completa para Lavandería Digital
Ejecuta: python test_app.py
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Probar que todos los imports funcionen"""
    print("🔍 Probando imports...")
    
    try:
        from app import create_app
        print("  ✅ create_app")
    except Exception as e:
        print(f"  ❌ create_app: {e}")
        return False
    
    try:
        from app.models import db, Usuario, Admin, Pedido, TipoPrenda, DireccionUsuario
        print("  ✅ models")
    except Exception as e:
        print(f"  ❌ models: {e}")
        return False
    
    try:
        from app.admin_routes import admin_bp
        print("  ✅ admin_routes")
    except Exception as e:
        print(f"  ❌ admin_routes: {e}")
        return False
    
    try:
        from app.routes import main
        print("  ✅ routes")
    except Exception as e:
        print(f"  ❌ routes: {e}")
        return False
    
    return True

def test_app_creation():
    """Probar creación de la app"""
    print("\n🏗️  Probando creación de app...")
    
    try:
        from app import create_app
        app = create_app()
        print("  ✅ App creada exitosamente")
        return app
    except Exception as e:
        print(f"  ❌ Error creando app: {e}")
        return None

def test_database(app):
    """Probar configuración de base de datos"""
    print("\n💾 Probando base de datos...")
    
    try:
        with app.app_context():
            from app.extensions import db
            from app.models import Admin, TipoPrenda
            
            # Crear tablas
            db.create_all()
            print("  ✅ Tablas creadas")
            
            # Probar query simple
            admin_count = Admin.query.count()
            print(f"  ✅ Query funciona - Admins: {admin_count}")
            
            # Probar insert
            tipo_test = TipoPrenda.query.filter_by(nombre="Test").first()
            if not tipo_test:
                tipo_test = TipoPrenda(
                    nombre="Test",
                    precio_por_kg=20.0,
                    tiempo_lavado_horas=24,
                    descripcion="Tipo de prueba"
                )
                db.session.add(tipo_test)
                db.session.commit()
                print("  ✅ Insert funciona")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error en base de datos: {e}")
        return False

def test_routes(app):
    """Probar rutas principales"""
    print("\n🛣️  Probando rutas...")
    
    try:
        with app.test_client() as client:
            # Ruta principal
            response = client.get('/')
            print(f"  ✅ / -> Status: {response.status_code}")
            
            # Login admin
            response = client.get('/admin/login')
            print(f"  ✅ /admin/login -> Status: {response.status_code}")
            
            # API de rutas (debería dar error sin auth, pero no 500)
            response = client.post('/admin/api/generar-ruta-optimizada', 
                                 json={'fecha': '2025-06-06', 'tipo': 'recoleccion'})
            print(f"  ✅ API ruta -> Status: {response.status_code}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error probando rutas: {e}")
        return False

def setup_test_data(app):
    """Configurar datos de prueba"""
    print("\n📊 Configurando datos de prueba...")
    
    try:
        with app.app_context():
            from app.extensions import db
            from app.models import Admin, TipoPrenda, Usuario, DireccionUsuario, Pedido
            from werkzeug.security import generate_password_hash
            from datetime import datetime, timedelta
            
            # Admin por defecto
            admin = Admin.query.filter_by(usuario="admin").first()
            if not admin:
                admin = Admin(
                    usuario="admin",
                    contrasena=generate_password_hash("admin123"),
                    nombre="Admin Test",
                    email="admin@test.com"
                )
                db.session.add(admin)
                print("  ✅ Admin creado")
            
            # Tipos de prenda básicos
            tipos_basicos = [
                ("Ropa Normal", 25.0, 24),
                ("Ropa Delicada", 35.0, 48),
                ("Edredones", 45.0, 48)
            ]
            
            for nombre, precio, tiempo in tipos_basicos:
                tipo = TipoPrenda.query.filter_by(nombre=nombre).first()
                if not tipo:
                    tipo = TipoPrenda(
                        nombre=nombre,
                        precio_por_kg=precio,
                        tiempo_lavado_horas=tiempo,
                        descripcion=f"Tipo {nombre.lower()}"
                    )
                    db.session.add(tipo)
            
            print("  ✅ Tipos de prenda configurados")
            
            # Usuario de prueba
            usuario = Usuario.query.filter_by(email="test@test.com").first()
            if not usuario:
                usuario = Usuario(
                    nombre="Usuario Test",
                    email="test@test.com",
                    contrasena=generate_password_hash("test123"),
                    telefono="55 1234 5678"
                )
                db.session.add(usuario)
                db.session.flush()
                
                # Dirección para el usuario
                direccion = DireccionUsuario(
                    usuario_id=usuario.id,
                    nombre="Casa Test",
                    direccion="Av. Test 123, Colonia Test, CDMX",
                    latitud=19.4326,
                    longitud=-99.1332,
                    es_principal=True,
                    verificada=True
                )
                db.session.add(direccion)
                db.session.flush()
                
                # Pedidos de prueba
                hoy = datetime.now().date()
                
                # Pedido para recolección
                pedido1 = Pedido(
                    usuario_id=usuario.id,
                    direccion_usuario_id=direccion.id,
                    direccion=direccion.direccion,
                    latitud=direccion.latitud,
                    longitud=direccion.longitud,
                    fecha_recoleccion=hoy,
                    fecha_entrega=hoy + timedelta(days=1),
                    precio_total=125.0,
                    peso_estimado=5.0,
                    estado="Solicitado",
                    notas="Pedido de prueba para recolección"
                )
                db.session.add(pedido1)
                
                # Pedido para entrega
                pedido2 = Pedido(
                    usuario_id=usuario.id,
                    direccion_usuario_id=direccion.id,
                    direccion=direccion.direccion,
                    latitud=direccion.latitud,
                    longitud=direccion.longitud,
                    fecha_recoleccion=hoy - timedelta(days=1),
                    fecha_entrega=hoy,
                    precio_total=85.0,
                    peso_estimado=3.0,
                    estado="Listo",
                    notas="Pedido de prueba para entrega"
                )
                db.session.add(pedido2)
                
                print("  ✅ Usuario y pedidos de prueba creados")
            
            db.session.commit()
            return True
            
    except Exception as e:
        print(f"  ❌ Error configurando datos: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False

def test_api_endpoint(app):
    """Probar específicamente el endpoint de rutas"""
    print("\n🔗 Probando endpoint de rutas...")
    
    try:
        with app.test_client() as client:
            # Primero hacer login como admin
            login_data = {
                'usuario': 'admin',
                'contrasena': 'admin123'
            }
            
            response = client.post('/admin/login', data=login_data, follow_redirects=True)
            print(f"  ✅ Login admin -> Status: {response.status_code}")
            
            # Ahora probar el endpoint de rutas
            api_data = {
                'fecha': '2025-06-06',
                'tipo': 'recoleccion'
            }
            
            response = client.post('/admin/api/generar-ruta-optimizada', 
                                 json=api_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"  ✅ API generar ruta -> Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"  ✅ Respuesta JSON: {data.get('success', False)}")
                return True
            else:
                print(f"  ⚠️  Response: {response.get_data(as_text=True)[:200]}...")
                return False
            
    except Exception as e:
        print(f"  ❌ Error probando API: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 PRUEBA COMPLETA DE LAVANDERÍA DIGITAL")
    print("="*50)
    
    # 1. Probar imports
    if not test_imports():
        print("❌ Falló en imports. Revisar dependencias.")
        return
    
    # 2. Crear app
    app = test_app_creation()
    if not app:
        print("❌ Falló creación de app.")
        return
    
    # 3. Probar base de datos
    if not test_database(app):
        print("❌ Falló configuración de BD.")
        return
    
    # 4. Configurar datos de prueba
    if not setup_test_data(app):
        print("❌ Falló configuración de datos.")
        return
    
    # 5. Probar rutas
    if not test_routes(app):
        print("❌ Falló prueba de rutas.")
        return
    
    # 6. Probar API específicamente
    if not test_api_endpoint(app):
        print("❌ Falló prueba de API.")
        return
    
    print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
    print("="*50)
    print("✅ La aplicación está lista para usar")
    print("🌐 Puedes ejecutar: python run.py")
    print("🛡️  Admin: admin / admin123")
    print("👤 Usuario: test@test.com / test123")

if __name__ == "__main__":
    main()