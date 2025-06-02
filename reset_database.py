"""
Script mejorado para resetear la base de datos
Maneja mejor los archivos bloqueados
"""

import os
import time
import shutil
from app import create_app
from app.models import db, TipoPrenda, Configuracion

def reset_database_safe():
    print("🔄 Iniciando reset de base de datos...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Intentar cerrar todas las conexiones
            db.session.close()
            db.engine.dispose()
            print("✅ Conexiones de base de datos cerradas")
        except:
            pass
        
        # Intentar eliminar la base de datos
        db_path = 'instance/lavanderia.db'
        backup_path = 'instance/lavanderia_backup.db'
        
        if os.path.exists(db_path):
            try:
                # Hacer backup por si acaso
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                shutil.copy2(db_path, backup_path)
                print("📁 Backup creado en lavanderia_backup.db")
                
                # Intentar eliminar
                os.remove(db_path)
                print("🗑️  Base de datos anterior eliminada")
            except PermissionError:
                print("⚠️  No se pudo eliminar la DB (archivo en uso)")
                print("⚠️  Renombrando archivo existente...")
                
                # Si no se puede eliminar, renombrar
                old_name = f'instance/lavanderia_old_{int(time.time())}.db'
                try:
                    os.rename(db_path, old_name)
                    print(f"✅ Archivo renombrado a {old_name}")
                except:
                    print("❌ Error: Cierra completamente Flask y vuelve a intentar")
                    return False
        
        # Crear nueva estructura
        try:
            db.create_all()
            print("✅ Nueva estructura de base de datos creada")
            
            # Inicializar datos
            init_sample_data()
            return True
            
        except Exception as e:
            print(f"❌ Error creando nueva DB: {e}")
            return False

def init_sample_data():
    """Inicializa la base de datos con datos de ejemplo"""
    
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
    
    try:
        # Guardar cambios
        db.session.commit()
        
        print("✅ Base de datos inicializada correctamente!")
        print(f"✅ Creados {len(tipos_prenda)} tipos de prendas")
        print(f"✅ Creadas {len(configuraciones)} configuraciones")
        print("\n📋 Tipos de prendas disponibles:")
        for tipo in TipoPrenda.query.all():
            print(f"   - {tipo.nombre}: ${tipo.precio_por_kg}/kg ({tipo.tiempo_lavado_horas}h)")
        
        print("\n🚀 ¡Listo! Ahora puedes ejecutar: python run.py")
        
    except Exception as e:
        print(f"❌ Error guardando datos: {e}")
        db.session.rollback()

if __name__ == "__main__":
    success = reset_database_safe()
    if not success:
        print("\n💡 SOLUCIÓN:")
        print("1. Asegúrate de que Flask no esté corriendo (Ctrl+C)")
        print("2. Cierra cualquier explorador de DB que tengas abierto")
        print("3. Vuelve a ejecutar este script")
        print("4. Si persiste el problema, reinicia la terminal")