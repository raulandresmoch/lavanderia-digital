#!/usr/bin/env python3
"""
Script para arreglar rápidamente los errores del sistema
"""

import sys
import os
from datetime import datetime, timedelta  # ← CORREGIDO: Agregado import

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def limpiar_errores():
    """Limpiar errores y reiniciar el sistema"""
    try:
        from app import create_app
        from app.extensions import db
        from app.models import Admin, Usuario, Pedido, TipoPrenda, DireccionUsuario
        from werkzeug.security import generate_password_hash
        
        print("🧹 Limpiando errores del sistema...")
        
        app = create_app()
        
        with app.app_context():
            # Verificar que la base de datos funcione
            try:
                admin_count = Admin.query.count()
                print(f"✅ Base de datos funciona - Admins: {admin_count}")
            except Exception as e:
                print(f"❌ Error en BD: {e}")
                return False
            
            # Verificar datos mínimos
            admin = Admin.query.filter_by(usuario="admin").first()
            if not admin:
                admin = Admin(
                    usuario="admin",
                    contrasena=generate_password_hash("admin123"),
                    nombre="Admin Principal",
                    email="admin@test.com"
                )
                db.session.add(admin)
                print("✅ Admin creado")
            
            # Verificar tipos de prenda
            tipos_count = TipoPrenda.query.count()
            if tipos_count == 0:
                tipos_default = [
                    ("Ropa Normal", 25.0, 24),
                    ("Ropa Delicada", 35.0, 48),
                    ("Edredones", 45.0, 48),
                    ("Ropa de Cama", 30.0, 24)
                ]
                
                for nombre, precio, tiempo in tipos_default:
                    tipo = TipoPrenda(
                        nombre=nombre,
                        precio_por_kg=precio,
                        tiempo_lavado_horas=tiempo,
                        descripcion=f"Servicio de {nombre.lower()}"
                    )
                    db.session.add(tipo)
                print("✅ Tipos de prenda creados")
            
            # Crear usuario de prueba para hoy
            hoy = datetime.now().date()
            usuario_test = Usuario.query.filter_by(email="test@test.com").first()
            
            if not usuario_test:
                usuario_test = Usuario(
                    nombre="Usuario Test",
                    email="test@test.com",
                    contrasena=generate_password_hash("test123"),
                    telefono="55 1234 5678"
                )
                db.session.add(usuario_test)
                db.session.flush()
                
                # Dirección para el usuario
                direccion_test = DireccionUsuario(
                    usuario_id=usuario_test.id,
                    nombre="Casa Test",
                    direccion="Av. Test 123, Colonia Test, CDMX",
                    latitud=19.4326,
                    longitud=-99.1332,
                    es_principal=True,
                    verificada=True
                )
                db.session.add(direccion_test)
                db.session.flush()
                print("✅ Usuario de prueba creado")
            else:
                direccion_test = usuario_test.direccion_principal
                if not direccion_test:
                    direccion_test = DireccionUsuario(
                        usuario_id=usuario_test.id,
                        nombre="Casa Test",
                        direccion="Av. Test 123, Colonia Test, CDMX",
                        latitud=19.4326,
                        longitud=-99.1332,
                        es_principal=True,
                        verificada=True
                    )
                    db.session.add(direccion_test)
                    db.session.flush()
            
            # Limpiar pedidos antiguos de prueba
            Pedido.query.filter(Pedido.usuario_id == usuario_test.id).delete()
            
            # Crear pedidos para HOY
            pedidos_para_hoy = [
                {
                    "fecha_recoleccion": hoy,
                    "fecha_entrega": hoy + timedelta(days=1),
                    "estado": "Solicitado",
                    "precio": 125.50,
                    "peso": 5.0,
                    "notas": "Pedido de recolección para hoy"
                },
                {
                    "fecha_recoleccion": hoy,
                    "fecha_entrega": hoy + timedelta(days=1),
                    "estado": "Solicitado",
                    "precio": 89.75,
                    "peso": 3.5,
                    "notas": "Segundo pedido de recolección"
                },
                {
                    "fecha_recoleccion": hoy - timedelta(days=1),
                    "fecha_entrega": hoy,
                    "estado": "Listo",
                    "precio": 156.25,
                    "peso": 6.0,
                    "notas": "Pedido listo para entrega hoy"
                },
                {
                    "fecha_recoleccion": hoy - timedelta(days=1),
                    "fecha_entrega": hoy,
                    "estado": "Listo",
                    "precio": 78.50,
                    "peso": 2.5,
                    "notas": "Segundo pedido para entrega"
                }
            ]
            
            for pedido_data in pedidos_para_hoy:
                pedido = Pedido(
                    usuario_id=usuario_test.id,
                    direccion_usuario_id=direccion_test.id,
                    direccion=direccion_test.direccion,
                    latitud=direccion_test.latitud,
                    longitud=direccion_test.longitud,
                    fecha_recoleccion=pedido_data["fecha_recoleccion"],
                    fecha_entrega=pedido_data["fecha_entrega"],
                    precio_total=pedido_data["precio"],
                    peso_estimado=pedido_data["peso"],
                    estado=pedido_data["estado"],
                    notas=pedido_data["notas"]
                )
                db.session.add(pedido)
            
            db.session.commit()
            
            # Verificar que todo esté bien
            recolecciones_hoy = Pedido.query.filter(
                Pedido.fecha_recoleccion == hoy,
                Pedido.estado == 'Solicitado'
            ).count()
            
            entregas_hoy = Pedido.query.filter(
                Pedido.fecha_entrega == hoy,
                Pedido.estado == 'Listo'
            ).count()
            
            print(f"✅ Sistema limpio y listo:")
            print(f"   📦 Recolecciones para hoy: {recolecciones_hoy}")
            print(f"   🏠 Entregas para hoy: {entregas_hoy}")
            print(f"   📅 Fecha de hoy: {hoy}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error limpiando sistema: {e}")
        import traceback
        traceback.print_exc()
        return False

def probar_rutas():
    """Probar que las rutas funcionen"""
    try:
        from app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            # Login admin
            response = client.post('/admin/login', data={
                'usuario': 'admin',
                'contrasena': 'admin123'
            })
            
            if response.status_code != 302:
                print("❌ Error en login admin")
                return False
            
            print("✅ Login admin OK")
            
            # Probar endpoint de rutas
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            # Probar recolección
            response = client.post('/admin/api/generar-ruta-optimizada', 
                                 json={'fecha': hoy, 'tipo': 'recoleccion'},
                                 headers={'Content-Type': 'application/json'})
            
            print(f"📦 Test recolección: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Success: {data.get('success')}")
                print(f"   ✅ Pedidos: {data.get('total_pedidos', 0)}")
                if data.get('rutas'):
                    print(f"   ✅ Zonas generadas: {len(data.get('rutas', {}))}")
            else:
                print(f"   ❌ Error: {response.get_data(as_text=True)[:100]}...")
            
            # Probar entrega
            response = client.post('/admin/api/generar-ruta-optimizada',
                                 json={'fecha': hoy, 'tipo': 'entrega'},
                                 headers={'Content-Type': 'application/json'})
            
            print(f"🏠 Test entrega: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Success: {data.get('success')}")
                print(f"   ✅ Pedidos: {data.get('total_pedidos', 0)}")
                if data.get('rutas'):
                    print(f"   ✅ Zonas generadas: {len(data.get('rutas', {}))}")
            else:
                print(f"   ❌ Error: {response.get_data(as_text=True)[:100]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Error probando rutas: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar arreglo completo"""
    print("🔧 ARREGLO RÁPIDO DEL SISTEMA")
    print("="*40)
    
    if not limpiar_errores():
        print("❌ Falló la limpieza")
        return
    
    if not probar_rutas():
        print("❌ Falló la prueba de rutas")
        return
    
    print("\n🎉 ¡SISTEMA ARREGLADO!")
    print("="*40)
    print("✅ Todo funcionando correctamente")
    print("🚀 Ejecuta: python run.py")
    print("🌐 Ve a: http://127.0.0.1:5000/admin/rutas")
    print("🛡️  Login: admin / admin123")

if __name__ == "__main__":
    main()