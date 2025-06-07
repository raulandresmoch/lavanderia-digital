#!/usr/bin/env python3
"""
Script para actualizar completamente la base de datos con todas las columnas faltantes
"""

import sys
import os
from sqlalchemy import text

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def update_database():
    """Actualizar base de datos con todas las columnas faltantes"""
    try:
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Actualizando base de datos completa...")
            
            # Lista de todas las migraciones necesarias
            migrations = [
                # Tabla usuario
                {
                    'table': 'usuario',
                    'column': 'activo',
                    'sql': 'ALTER TABLE usuario ADD COLUMN activo BOOLEAN DEFAULT 1'
                },
                
                # Tabla pedido - notas_internas
                {
                    'table': 'pedido',
                    'column': 'notas_internas', 
                    'sql': 'ALTER TABLE pedido ADD COLUMN notas_internas TEXT'
                },
                
                # Tabla pedido - direccion_usuario_id
                {
                    'table': 'pedido',
                    'column': 'direccion_usuario_id',
                    'sql': 'ALTER TABLE pedido ADD COLUMN direccion_usuario_id INTEGER REFERENCES direccion_usuario(id)'
                },
                
                # Tabla pedido - hora_recoleccion
                {
                    'table': 'pedido',
                    'column': 'hora_recoleccion',
                    'sql': 'ALTER TABLE pedido ADD COLUMN hora_recoleccion TEXT DEFAULT "9:00-12:00"'
                },
                
                # Tabla pedido - hora_entrega
                {
                    'table': 'pedido',
                    'column': 'hora_entrega',
                    'sql': 'ALTER TABLE pedido ADD COLUMN hora_entrega TEXT DEFAULT "14:00-18:00"'
                },
                
                # Tabla pedido - actualizado
                {
                    'table': 'pedido',
                    'column': 'actualizado',
                    'sql': 'ALTER TABLE pedido ADD COLUMN actualizado DATETIME DEFAULT CURRENT_TIMESTAMP'
                }
            ]
            
            for migration in migrations:
                try:
                    # Verificar si la columna ya existe
                    result = db.session.execute(text(f"PRAGMA table_info({migration['table']})")).fetchall()
                    columns = [row[1] for row in result]
                    
                    if migration['column'] not in columns:
                        print(f"➕ Agregando columna {migration['column']} a tabla {migration['table']}...")
                        db.session.execute(text(migration['sql']))
                        db.session.commit()
                        print(f"✅ Columna {migration['column']} agregada exitosamente")
                    else:
                        print(f"ℹ️  La columna {migration['column']} ya existe en {migration['table']}")
                        
                except Exception as e:
                    print(f"❌ Error agregando columna {migration['column']}: {e}")
                    db.session.rollback()
            
            # Crear las nuevas tablas si no existen
            print("\n🏗️  Creando tablas nuevas si no existen...")
            
            try:
                # Crear todas las tablas según los modelos actuales
                db.create_all()
                print("✅ Todas las tablas creadas/verificadas")
                
            except Exception as e:
                print(f"❌ Error creando tablas: {e}")
            
            # Verificar el estado final
            print("\n📊 Estado final de las tablas:")
            
            # Verificar tabla usuario
            result = db.session.execute(text("PRAGMA table_info(usuario)")).fetchall()
            user_columns = [row[1] for row in result]
            print(f"📋 Tabla usuario ({len(user_columns)} columnas): {', '.join(user_columns)}")
            
            # Verificar tabla pedido
            result = db.session.execute(text("PRAGMA table_info(pedido)")).fetchall()
            pedido_columns = [row[1] for row in result]
            print(f"📋 Tabla pedido ({len(pedido_columns)} columnas): {', '.join(pedido_columns)}")
            
            # Verificar si direccion_usuario existe
            try:
                result = db.session.execute(text("PRAGMA table_info(direccion_usuario)")).fetchall()
                direccion_columns = [row[1] for row in result]
                print(f"📋 Tabla direccion_usuario ({len(direccion_columns)} columnas): {', '.join(direccion_columns)}")
            except:
                print("📋 Tabla direccion_usuario: No existe (se creará automáticamente)")
            
            print("\n🎉 Actualización de base de datos completada")
            
            return True
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = update_database()
    if success:
        print("\n✅ Base de datos actualizada correctamente")
        print("🚀 Ahora puedes ejecutar: python run.py")
    else:
        print("\n❌ Falló la actualización de la base de datos")
        sys.exit(1)