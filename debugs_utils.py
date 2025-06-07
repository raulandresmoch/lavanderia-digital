"""
Utilidades para debugging y diagnóstico del sistema
"""
from app.models import db, Pedido, Usuario, Admin, TipoPrenda, DireccionUsuario
from datetime import datetime, timedelta
import logging

def diagnosticar_sistema():
    """Ejecutar diagnóstico completo del sistema"""
    print("\n" + "="*60)
    print("🔍 DIAGNÓSTICO DEL SISTEMA")
    print("="*60)
    
    # 1. Verificar conexión a base de datos
    try:
        # Test básico de conexión
        db.session.execute("SELECT 1")
        print("✅ Conexión a base de datos: OK")
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False
    
    # 2. Verificar tablas existentes
    try:
        tablas_esperadas = ['usuario', 'direccion_usuario', 'pedido', 'admin', 'tipo_prenda']
        inspector = db.inspect(db.engine)
        tablas_existentes = inspector.get_table_names()
        
        print(f"\n📊 Tablas en base de datos: {len(tablas_existentes)}")
        for tabla in tablas_esperadas:
            if tabla in tablas_existentes:
                print(f"  ✅ {tabla}")
            else:
                print(f"  ❌ {tabla} - FALTA")
                
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
    
    # 3. Verificar datos básicos
    try:
        # Contar registros
        num_usuarios = Usuario.query.count()
        num_admins = Admin.query.count()
        num_pedidos = Pedido.query.count()
        num_tipos_prenda = TipoPrenda.query.count()
        num_direcciones = DireccionUsuario.query.count()
        
        print(f"\n📈 Estadísticas de datos:")
        print(f"  👥 Usuarios: {num_usuarios}")
        print(f"  🛡️  Admins: {num_admins}")
        print(f"  📦 Pedidos: {num_pedidos}")
        print(f"  👕 Tipos de prenda: {num_tipos_prenda}")
        print(f"  📍 Direcciones: {num_direcciones}")
        
        # Verificar admin por defecto
        admin_default = Admin.query.filter_by(usuario="admin").first()
        if admin_default:
            print(f"  ✅ Admin por defecto existe: {admin_default.nombre}")
        else:
            print(f"  ⚠️  Admin por defecto no encontrado")
            
        # Verificar tipos de prenda
        if num_tipos_prenda == 0:
            print(f"  ⚠️  No hay tipos de prenda configurados")
        else:
            tipos = TipoPrenda.query.filter_by(activo=True).all()
            print(f"  ✅ Tipos de prenda activos: {len(tipos)}")
            for tipo in tipos[:3]:  # Mostrar primeros 3
                print(f"    - {tipo.nombre}: ${tipo.precio_por_kg}/kg")
                
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
    
    # 4. Verificar rutas y endpoints
    try:
        from flask import current_app
        print(f"\n🛣️  Endpoints registrados:")
        
        endpoints_importantes = [
            'admin.rutas',
            'admin.dashboard', 
            'admin.pedidos',
            'admin.generar_ruta_optimizada',
            'main.cotizar',
            'main.confirmar_pedido'
        ]
        
        for endpoint in endpoints_importantes:
            try:
                from flask import url_for
                url = url_for(endpoint)
                print(f"  ✅ {endpoint} -> {url}")
            except Exception:
                print(f"  ❌ {endpoint} -> NO ENCONTRADO")
                
    except Exception as e:
        print(f"❌ Error verificando rutas: {e}")
    
    # 5. Verificar logs recientes
    try:
        print(f"\n📝 Configuración de logging:")
        logger = logging.getLogger()
        print(f"  Nivel: {logger.level}")
        print(f"  Handlers: {len(logger.handlers)}")
        
    except Exception as e:
        print(f"❌ Error verificando logs: {e}")
    
    print("\n" + "="*60)
    print("✅ Diagnóstico completado")
    print("="*60)
    return True

def crear_datos_prueba():
    """Crear datos de prueba para testing"""
    try:
        print("\n🧪 Creando datos de prueba...")
        
        # Crear usuario de prueba
        usuario_prueba = Usuario.query.filter_by(email="test@example.com").first()
        if not usuario_prueba:
            from werkzeug.security import generate_password_hash
            
            usuario_prueba = Usuario(
                nombre="Usuario de Prueba",
                email="test@example.com", 
                contrasena=generate_password_hash("test123"),
                telefono="55 1234 5678"
            )
            db.session.add(usuario_prueba)
            db.session.flush()
            
            # Crear dirección para el usuario
            direccion_prueba = DireccionUsuario(
                usuario_id=usuario_prueba.id,
                nombre="Casa de Prueba",
                direccion="Av. Reforma 123, Roma Norte, Ciudad de México",
                latitud=19.4326,
                longitud=-99.1332,
                es_principal=True,
                verificada=True,
                notas="Dirección de prueba para testing"
            )
            db.session.add(direccion_prueba)
            print("✅ Usuario de prueba creado: test@example.com / test123")
        
        # Crear pedidos de prueba
        pedidos_existentes = Pedido.query.filter_by(usuario_id=usuario_prueba.id).count()
        if pedidos_existentes == 0:
            # Pedido para hoy (recolección)
            hoy = datetime.now().date()
            manana = hoy + timedelta(days=1)
            
            pedido1 = Pedido(
                usuario_id=usuario_prueba.id,
                direccion="Av. Reforma 123, Roma Norte, Ciudad de México",
                fecha_recoleccion=hoy,
                fecha_entrega=manana,
                precio_total=125.50,
                peso_estimado=5.0,
                estado="Solicitado",
                notas="Pedido de prueba para recolección"
            )
            db.session.add(pedido1)
            
            # Pedido para entrega
            pedido2 = Pedido(
                usuario_id=usuario_prueba.id,
                direccion="Av. Reforma 123, Roma Norte, Ciudad de México", 
                fecha_recoleccion=hoy - timedelta(days=1),
                fecha_entrega=hoy,
                precio_total=89.75,
                peso_estimado=3.5,
                estado="Listo",
                notas="Pedido de prueba para entrega"
            )
            db.session.add(pedido2)
            
            print("✅ Pedidos de prueba creados")
        
        db.session.commit()
        print("✅ Datos de prueba guardados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        db.session.rollback()
        return False

def limpiar_datos_prueba():
    """Limpiar datos de prueba"""
    try:
        print("\n🧹 Limpiando datos de prueba...")
        
        # Eliminar usuario de prueba y sus datos relacionados
        usuario_prueba = Usuario.query.filter_by(email="test@example.com").first()
        if usuario_prueba:
            # Eliminar pedidos
            Pedido.query.filter_by(usuario_id=usuario_prueba.id).delete()
            # Eliminar direcciones
            DireccionUsuario.query.filter_by(usuario_id=usuario_prueba.id).delete()
            # Eliminar usuario
            db.session.delete(usuario_prueba)
            
            db.session.commit()
            print("✅ Datos de prueba eliminados")
        else:
            print("ℹ️  No hay datos de prueba para eliminar")
            
    except Exception as e:
        print(f"❌ Error limpiando datos de prueba: {e}")
        db.session.rollback()

if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    with app.app_context():
        diagnosticar_sistema()
        
        respuesta = input("\n¿Crear datos de prueba? (s/n): ")
        if respuesta.lower() == 's':
            crear_datos_prueba()
            print("\n✅ Sistema listo para testing")
            print("📝 Usuario de prueba: test@example.com / test123")
            print("🛡️  Admin: admin / admin123")