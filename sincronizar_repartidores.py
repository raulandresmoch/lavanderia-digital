#!/usr/bin/env python3
"""
Script para sincronizar repartidores entre el bot y el sistema web
"""

import sqlite3
import os
from datetime import datetime

def sincronizar_repartidores():
    """Sincronizar repartidores del bot con la base de datos principal"""
    
    bot_db_path = 'repartidores.db'
    web_db_path = 'instance/lavanderia.db'
    
    print("🔄 Sincronizando repartidores...")
    
    # Verificar que ambas bases de datos existen
    if not os.path.exists(bot_db_path):
        print(f"❌ No se encontró {bot_db_path}")
        return False
        
    if not os.path.exists(web_db_path):
        print(f"❌ No se encontró {web_db_path}")
        return False
    
    try:
        # Conectar a base de datos del bot
        bot_conn = sqlite3.connect(bot_db_path)
        bot_cursor = bot_conn.cursor()
        
        # Conectar a base de datos web
        web_conn = sqlite3.connect(web_db_path)
        web_cursor = web_conn.cursor()
        
        # Verificar si existe la tabla repartidor en la BD web
        web_cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='repartidor'
        """)
        
        if not web_cursor.fetchone():
            print("📝 Creando tabla repartidor en la base de datos web...")
            web_cursor.execute("""
                CREATE TABLE repartidor (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_chat_id TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    estado TEXT DEFAULT 'disponible',
                    activo BOOLEAN DEFAULT 1,
                    verificado BOOLEAN DEFAULT 0,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_actividad TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ubicacion_actual_lat REAL,
                    ubicacion_actual_lng REAL,
                    ultima_ubicacion TIMESTAMP,
                    pedidos_completados INTEGER DEFAULT 0,
                    calificacion_promedio REAL DEFAULT 5.0,
                    tiempo_promedio_entrega INTEGER,
                    notificaciones_activas BOOLEAN DEFAULT 1,
                    tracking_activo BOOLEAN DEFAULT 0
                )
            """)
            web_conn.commit()
            print("✅ Tabla repartidor creada")
        
        # Obtener repartidores del bot
        bot_cursor.execute("SELECT * FROM repartidores WHERE activo = 1")
        repartidores_bot = bot_cursor.fetchall()
        
        print(f"📊 Encontrados {len(repartidores_bot)} repartidores activos en el bot")
        
        sincronizados = 0
        
        for repartidor in repartidores_bot:
            chat_id = repartidor[0]
            nombre = repartidor[1]
            activo = repartidor[2]
            fecha_registro = repartidor[6] if len(repartidor) > 6 else datetime.now().isoformat()
            
            # Verificar si ya existe en la BD web
            web_cursor.execute(
                "SELECT id FROM repartidor WHERE telegram_chat_id = ?", 
                (chat_id,)
            )
            
            if web_cursor.fetchone():
                # Actualizar si ya existe
                web_cursor.execute("""
                    UPDATE repartidor 
                    SET nombre = ?, activo = ?, ultima_actividad = CURRENT_TIMESTAMP
                    WHERE telegram_chat_id = ?
                """, (nombre, activo, chat_id))
                print(f"🔄 Actualizado: {nombre} ({chat_id})")
            else:
                # Insertar nuevo repartidor
                web_cursor.execute("""
                    INSERT INTO repartidor (
                        telegram_chat_id, nombre, activo, verificado, 
                        fecha_registro, ultima_actividad
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (chat_id, nombre, activo, True, fecha_registro))
                print(f"➕ Agregado: {nombre} ({chat_id})")
            
            sincronizados += 1
        
        web_conn.commit()
        
        # Cerrar conexiones
        bot_conn.close()
        web_conn.close()
        
        print(f"✅ Sincronización completada: {sincronizados} repartidores")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la sincronización: {e}")
        return False

def mostrar_repartidores():
    """Mostrar repartidores en ambas bases de datos"""
    
    print("\n" + "="*60)
    print("📊 REPARTIDORES EN AMBAS BASES DE DATOS")
    print("="*60)
    
    # Bot DB
    if os.path.exists('repartidores.db'):
        print("\n🤖 REPARTIDORES EN BOT (repartidores.db):")
        bot_conn = sqlite3.connect('repartidores.db')
        bot_cursor = bot_conn.cursor()
        bot_cursor.execute("SELECT chat_id, nombre, activo FROM repartidores")
        
        for row in bot_cursor.fetchall():
            estado = "✅ Activo" if row[2] else "❌ Inactivo"
            print(f"   👤 {row[1]} - Chat ID: {row[0]} - {estado}")
        
        bot_conn.close()
    else:
        print("\n🤖 REPARTIDORES EN BOT: ❌ Base de datos no encontrada")
    
    # Web DB
    if os.path.exists('instance/lavanderia.db'):
        print("\n🌐 REPARTIDORES EN WEB (instance/lavanderia.db):")
        web_conn = sqlite3.connect('instance/lavanderia.db')
        web_cursor = web_conn.cursor()
        
        try:
            web_cursor.execute("SELECT telegram_chat_id, nombre, activo FROM repartidor")
            repartidores = web_cursor.fetchall()
            
            if repartidores:
                for row in repartidores:
                    estado = "✅ Activo" if row[2] else "❌ Inactivo"
                    print(f"   👤 {row[1]} - Chat ID: {row[0]} - {estado}")
            else:
                print("   📭 No hay repartidores registrados")
                
        except sqlite3.OperationalError:
            print("   ❌ Tabla 'repartidor' no existe")
        
        web_conn.close()
    else:
        print("\n🌐 REPARTIDORES EN WEB: ❌ Base de datos no encontrada")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🔧 SINCRONIZADOR DE REPARTIDORES")
    print("="*40)
    
    # Mostrar estado actual
    mostrar_repartidores()
    
    # Sincronizar
    if sincronizar_repartidores():
        print("\n🎉 ¡Sincronización exitosa!")
        
        # Mostrar estado después de sincronizar
        mostrar_repartidores()
    else:
        print("\n💥 Error en la sincronización")