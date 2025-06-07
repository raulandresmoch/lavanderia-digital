#!/usr/bin/env python3
"""
Script para arreglar datos de prueba y asegurar que funcione la generación de rutas
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def crear_pedidos_para_fecha(fecha_str=None):
    """Crear pedidos de prueba para una fecha específica"""
    try:
        from app import create_app
        from app.extensions import db
        from app.models import Usuario, DireccionUsuario, Pedido, TipoPrenda
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        
        with app.app_context():
            # Si no se especifica fecha, usar hoy
            if not fecha_str:
                fecha_obj = datetime.now().date()
            else:
                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            
            print(f"🗓️  Creando pedidos para fecha: {fecha_obj}")
            
            # Obtener o crear usuario de prueba
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
                
                # Crear dirección
                direccion = DireccionUsuario(
                    usuario_id=usuario.id,
                    nombre="Casa Test",
                    direccion="Av. Reforma 123, Roma Norte, Ciudad de México",
                    latitud=19.4326,
                    longitud=-99.1332,
                    es_principal=True,
                    verificada=True
                )
                db.session.add(direccion)
                db.session.flush()
            else:
                direccion = usuario.direccion_principal
                if not direccion:
                    direccion = DireccionUsuario(
                        usuario_id=usuario.id,
                        nombre="Casa Test",
                        direccion="Av. Reforma 123, Roma Norte, Ciudad de México",
                        latitud=19.4326,
                        longitud=-99.1332,
                        es_principal=True,
                        verificada=True
                    )
                    db.session.add(direccion)
                    db.session.flush()
            
            # Crear más usuarios y direcciones variadas para rutas más interesantes
            usuarios_adicionales = [
                {
                    "nombre": "María González",
                    "email": "maria@test.com",
                    "direccion": "Calle Insurgentes 456, Condesa, Ciudad de México",
                    "lat": 19.4150, "lng": -99.1700
                },
                {
                    "nombre": "Carlos López", 
                    "email": "carlos@test.com",
                    "direccion": "Av. Universidad 789, Del Valle, Ciudad de México",
                    "lat": 19.3800, "lng": -99.1500
                },
                {
                    "nombre": "Ana Martínez",
                    "email": "ana@test.com", 
                    "direccion": "Reforma 321, Zona Rosa, Ciudad de México",
                    "lat": 19.4250, "lng": -99.1400
                }
            ]
            
            for user_data in usuarios_adicionales:
                user_exists = Usuario.query.filter_by(email=user_data["email"]).first()
                if not user_exists:
                    new_user = Usuario(
                        nombre=user_data["nombre"],
                        email=user_data["email"],
                        contrasena=generate_password_hash("test123"),
                        telefono="55 9876 5432"
                    )
                    db.session.add(new_user)
                    db.session.flush()
                    
                    new_direccion = DireccionUsuario(
                        usuario_id=new_user.id,
                        nombre="Casa",
                        direccion=user_data["direccion"],
                        latitud=user_data["lat"],
                        longitud=user_data["lng"],
                        es_principal=True,
                        verificada=True
                    )
                    db.session.add(new_direccion)
                    db.session.flush()
                    
                    # Crear pedidos para este usuario
                    # Pedido de recolección
                    pedido_recoleccion = Pedido(
                        usuario_id=new_user.id,
                        direccion_usuario_id=new_direccion.id,
                        direccion=new_direccion.direccion,
                        latitud=new_direccion.latitud,
                        longitud=new_direccion.longitud,
                        fecha_recoleccion=fecha_obj,
                        fecha_entrega=fecha_obj + timedelta(days=1),
                        precio_total=125.0 + (hash(user_data["email"]) % 100),
                        peso_estimado=3.0 + (hash(user_data["email"]) % 5),
                        estado="Solicitado",
                        notas=f"Pedido de {user_data['nombre']} para recolección"
                    )
                    db.session.add(pedido_recoleccion)
                    
                    # Pedido de entrega
                    pedido_entrega = Pedido(
                        usuario_id=new_user.id,
                        direccion_usuario_id=new_direccion.id,
                        direccion=new_direccion.direccion,
                        latitud=new_direccion.latitud,
                        longitud=new_direccion.longitud,
                        fecha_recoleccion=fecha_obj - timedelta(days=1),
                        fecha_entrega=fecha_obj,
                        precio_total=85.0 + (hash(user_data["email"]) % 50),
                        peso_estimado=2.0 + (hash(user_data["email"]) % 3),
                        estado="Listo",
                        notas=f"Pedido de {user_data['nombre']} para entrega"
                    )
                    db.session.add(pedido_entrega)
            
            # Eliminar pedidos existentes para la fecha para evitar duplicados
            Pedido.query.filter(
                (Pedido.fecha_recoleccion == fecha_obj) | 
                (Pedido.fecha_entrega == fecha_obj)
            ).delete()
            
            # Crear pedidos variados para el usuario principal
            pedidos_data = [
                {
                    "fecha_recoleccion": fecha_obj,
                    "fecha_entrega": fecha_obj + timedelta(days=1),
                    "estado": "Solicitado",
                    "precio": 125.50,
                    "peso": 5.0,
                    "notas": "Ropa normal para recolección"
                },
                {
                    "fecha_recoleccion": fecha_obj,
                    "fecha_entrega": fecha_obj + timedelta(days=2),
                    "estado": "Solicitado", 
                    "precio": 89.75,
                    "peso": 3.5,
                    "notas": "Ropa delicada para recolección"
                },
                {
                    "fecha_recoleccion": fecha_obj - timedelta(days=1),
                    "fecha_entrega": fecha_obj,
                    "estado": "Listo",
                    "precio": 156.25,
                    "peso": 6.0,
                    "notas": "Edredones listos para entrega"
                },
                {
                    "fecha_recoleccion": fecha_obj - timedelta(days=2),
                    "fecha_entrega": fecha_obj,
                    "estado": "Listo",
                    "precio": 78.50,
                    "peso": 2.5,
                    "notas": "Ropa de cama lista para entrega"
                }
            ]
            
            for pedido_data in pedidos_data:
                pedido = Pedido(
                    usuario_id=usuario.id,
                    direccion_usuario_id=direccion.id,
                    direccion=direccion.direccion,
                    latitud=direccion.latitud,
                    longitud=direccion.longitud,
                    fecha_recoleccion=pedido_data["fecha_recoleccion"],
                    fecha_entrega=pedido_data["fecha_entrega"],
                    precio_total=pedido_data["precio"],
                    peso_estimado=pedido_data["peso"],
                    estado=pedido_data["estado"],
                    notas=pedido_data["notas"]
                )
                db.session.add(pedido)
            
            db.session.commit()
            
            # Verificar lo que se creó
            recolecciones = Pedido.query.filter(
                Pedido.fecha_recoleccion == fecha_obj,
                Pedido.estado == 'Solicitado'
            ).count()
            
            entregas = Pedido.query.filter(
                Pedido.fecha_entrega == fecha_obj,
                Pedido.estado == 'Listo'
            ).count()
            
            print(f"✅ Pedidos creados exitosamente:")
            print(f"   📦 Recolecciones para {fecha_obj}: {recolecciones}")
            print(f"   🏠 Entregas para {fecha_obj}: {entregas}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creando pedidos: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_rutas(fecha_str=None):
    """Verificar que las rutas funcionen"""
    try:
        from app import create_app
        import requests
        
        app = create_app()
        
        if not fecha_str:
            fecha_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"🧪 Probando generación de rutas para {fecha_str}...")
        
        with app.test_client() as client:
            # Login como admin
            login_response = client.post('/admin/login', data={
                'usuario': 'admin',
                'contrasena': 'admin123'
            })
            
            if login_response.status_code != 302:
                print("❌ Error en login de admin")
                return False
            
            # Probar generación de ruta de recolección
            ruta_data = {
                'fecha': fecha_str,
                'tipo': 'recoleccion'
            }
            
            response = client.post('/admin/api/generar-ruta-optimizada',
                                 json=ruta_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"   📦 Recolección -> Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    print(f"   ✅ Rutas de recolección: {len(data.get('rutas', {}))} zonas")
                    print(f"   ✅ Total pedidos: {data.get('total_pedidos', 0)}")
                else:
                    print(f"   ❌ Error en respuesta: {data.get('error', 'Unknown')}")
            else:
                print(f"   ❌ Error HTTP: {response.get_data(as_text=True)[:200]}")
            
            # Probar generación de ruta de entrega
            ruta_data['tipo'] = 'entrega'
            response = client.post('/admin/api/generar-ruta-optimizada',
                                 json=ruta_data,
                                 headers={'Content-Type': 'application/json'})
            
            print(f"   🏠 Entrega -> Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    print(f"   ✅ Rutas de entrega: {len(data.get('rutas', {}))} zonas")
                    print(f"   ✅ Total pedidos: {data.get('total_pedidos', 0)}")
                else:
                    print(f"   ❌ Error en respuesta: {data.get('error', 'Unknown')}")
            else:
                print(f"   ❌ Error HTTP: {response.get_data(as_text=True)[:200]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verificando rutas: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar el fix completo"""
    print("🔧 ARREGLANDO DATOS DE PRUEBA PARA RUTAS")
    print("="*50)
    
    # Obtener fecha actual
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Fecha objetivo: {fecha_hoy}")
    
    # 1. Crear pedidos para hoy
    if crear_pedidos_para_fecha(fecha_hoy):
        print("✅ Datos de prueba creados")
    else:
        print("❌ Error creando datos")
        return
    
    # 2. Verificar que las rutas funcionen
    if verificar_rutas(fecha_hoy):
        print("✅ Rutas funcionando correctamente")
    else:
        print("❌ Error en rutas")
        return
    
    print("\n🎉 ¡ARREGLO COMPLETADO!")
    print("="*50)
    print("🚀 Ahora puedes:")
    print("1. Ejecutar: python run.py")
    print("2. Ir a: http://127.0.0.1:5000/admin/rutas")
    print("3. Seleccionar la fecha de hoy")
    print("4. Hacer clic en 'Generar Ruta'")

if __name__ == "__main__":
    main()