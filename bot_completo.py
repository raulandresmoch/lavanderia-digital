# bot_completo.py - Bot que recibe comandos Y envía notificaciones
import requests
import os
import time
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHATS')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

repartidores_activos = {}
rutas_asignadas = {}

def send_message(chat_id, text, parse_mode=None):
    """Enviar mensaje"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    try:
        response = requests.post(url, data=data, timeout=30)
        return response.json()
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return None

def enviar_notificacion_pedido(pedido_id, usuario_nombre, direccion, total):
    """Función para notificar pedidos (llamada desde Flask)"""
    try:
        mensaje = f"""🆕 *NUEVO PEDIDO*

📋 *Pedido #{pedido_id}*
👤 *Cliente:* {usuario_nombre}
📍 *Dirección:* {direccion[:50]}...
💰 *Total:* ${total}

🔗 Panel: http://localhost:5000/admin
"""
        
        result = send_message(ADMIN_CHAT_ID, mensaje)
        
        if result and result.get('ok'):
            print(f"✅ Notificación enviada para pedido #{pedido_id}")
            return True
        else:
            print(f"❌ Error notificación: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def handle_start(chat_id, user_name):
    """Manejar comando /start"""
    mensaje = f"""🚚 *Lavandería Digital*

¡Hola {user_name}! 👋

🔧 *Comandos básicos:*
- /start - Este mensaje
- /test - Probar bot
- /id - Tu Chat ID
- /admin - Info admin

🚛 *Comandos de repartidor:*
- /registro - Registrarte como repartidor
- /iniciar - Comenzar ruta asignada
- /ruta - Ver tu ruta actual
- /completar - Marcar parada completada
- /estado - Ver tu estado
- /problema - Reportar incidencias
- /ayuda - Ayuda completa

*Sistema:* ✅ Funcionando
*Ubicación:* Envía tu ubicación para tracking"""
    send_message(chat_id, mensaje)

def handle_admin(chat_id, user_name):
    """Info para administradores"""
    if str(chat_id) == ADMIN_CHAT_ID:
        mensaje = f"""👨‍💼 *Panel Administrativo*

✅ Eres administrador del sistema

*Links útiles:*
🌐 Web: http://localhost:5000
👨‍💼 Admin: http://localhost:5000/admin
📊 Pedidos: http://localhost:5000/mis-pedidos

*Tu Chat ID:* `{chat_id}`

*Notificaciones:* Activas ✅
Recibirás alertas automáticas de nuevos pedidos.
"""
    else:
        mensaje = f"""⚠️ *Acceso Restringido*

Hola {user_name}, no tienes permisos de administrador.

*Tu Chat ID:* `{chat_id}`

Para obtener acceso admin, contacta al administrador del sistema.
"""
    
    send_message(chat_id, mensaje)

def handle_estado_repartidor(chat_id, user_name):
    """Estado del repartidor"""
    repartidor = repartidores_activos.get(str(chat_id))
    ruta = rutas_asignadas.get(str(chat_id))
    
    if repartidor:
        mensaje = f"""📊 *Estado del Repartidor*

👤 *Nombre:* {user_name}
📱 *Chat ID:* {chat_id}
⭐ *Estado:* {repartidor.get('estado', 'Activo')}
🚛 *Ruta asignada:* {'✅ Sí' if ruta else '❌ No'}

📈 *Estadísticas:*
📦 Pedidos completados hoy: {repartidor.get('pedidos_hoy', 0)}
⏱️ Tiempo activo: {repartidor.get('tiempo_activo', '0h 0m')}
"""
    else:
        mensaje = f"""📊 *Estado*

👤 {user_name}
📱 ID: {chat_id}
⚠️ No estás registrado como repartidor

Usa /registro para registrarte
"""
    
    send_message(chat_id, mensaje)

def handle_iniciar_ruta(chat_id, user_name):
    """Iniciar ruta asignada"""
    ruta = rutas_asignadas.get(str(chat_id))
    
    if not ruta:
        send_message(chat_id, "❌ No tienes ruta asignada\n\nContacta al administrador para recibir una ruta.")
        return
    
    # Marcar ruta como iniciada
    ruta['estado'] = 'en_progreso'
    ruta['iniciada_en'] = time.time()
    
    mensaje = f"""🚀 *Ruta Iniciada*

✅ Ruta activada exitosamente
📅 Fecha: {ruta.get('fecha', 'Hoy')}
📦 Total pedidos: {ruta.get('total_pedidos', 0)}

💡 *Próximos pasos:*
- Envía tu ubicación para comenzar
- Usa /ruta para ver detalles
- Usa /completar cuando termines una parada

¡Buena suerte! 🚛"""
    
    send_message(chat_id, mensaje)

def handle_ver_ruta(chat_id, user_name):
    """Ver ruta asignada"""
    ruta = rutas_asignadas.get(str(chat_id))
    
    if not ruta:
        send_message(chat_id, "❌ No tienes ruta asignada")
        return
    
    total_pedidos = ruta.get('total_pedidos', 0)
    completados = ruta.get('completados', 0)
    estado = ruta.get('estado', 'asignada')
    
    mensaje = f"""🗺️ *Tu Ruta Actual*

📊 *Progreso:*
✅ Completados: {completados}
⏳ Pendientes: {total_pedidos - completados}
📈 Total: {total_pedidos}
⭐ Estado: {estado.title()}

📋 *Detalles:*
📅 Fecha: {ruta.get('fecha', 'Hoy')}
🚛 Tipo: {ruta.get('tipo', 'recoleccion').title()}

💡 *Comandos útiles:*
/completar - Marcar parada completada
/problema - Reportar incidencia
/ayuda - Ver todos los comandos
"""
    
    send_message(chat_id, mensaje)

def handle_completar_parada(chat_id, user_name):
    """Completar parada actual"""
    ruta = rutas_asignadas.get(str(chat_id))
    
    if not ruta:
        send_message(chat_id, "❌ No tienes ruta activa")
        return
    
    # Incrementar completados
    completados = ruta.get('completados', 0) + 1
    ruta['completados'] = completados
    total = ruta.get('total_pedidos', 0)
    
    if completados >= total:
        # Ruta completada
        mensaje = f"""🎉 *¡Ruta Completada!*

✅ Todos los pedidos han sido completados
📊 Total: {completados}/{total}
⏱️ ¡Excelente trabajo!

Estado: 🟢 Disponible para nueva ruta"""
        
        # Limpiar ruta
        del rutas_asignadas[str(chat_id)]
    else:
        mensaje = f"""✅ *Parada Completada*

📊 Progreso: {completados}/{total}
⏳ Pendientes: {total - completados}

💡 Continúa con la siguiente parada
Usa /ruta para ver detalles"""
    
    send_message(chat_id, mensaje)
    
    # Notificar al admin
    if ADMIN_CHAT_ID:
        send_message(ADMIN_CHAT_ID, f"✅ Parada completada por {user_name} ({chat_id})")

def handle_reportar_problema(chat_id, user_name):
    """Reportar problema"""
    mensaje = f"""🆘 *Reportar Problema*

Para reportar un problema, describe brevemente la situación:

📞 *Contacto directo:*
WhatsApp: +52 55 1234-5678
Email: soporte@lavanderia.com

🔄 *O responde a este mensaje con:*
- Descripción del problema
- Ubicación actual
- Pedido afectado (si aplica)

Un administrador será notificado inmediatamente."""
    
    send_message(chat_id, mensaje)
    
    # Notificar al admin
    if ADMIN_CHAT_ID:
        send_message(ADMIN_CHAT_ID, f"🆘 {user_name} ({chat_id}) necesita ayuda")

def handle_ayuda_repartidor(chat_id, user_name):
    """Mostrar ayuda completa"""
    mensaje = f"""❓ *Ayuda - Sistema de Reparto*

🔧 *Comandos disponibles:*

📍 *Ubicación y Ruta:*
/iniciar - Comenzar ruta asignada
/ruta - Ver ruta actual y progreso
/completar - Marcar parada como completada

🛠️ *Gestión:*
/estado - Ver tu estado actual
/problema - Reportar incidencias
/ayuda - Este menú de ayuda

📱 *Uso básico:*
1. Recibe ruta del administrador
2. Usa /iniciar para activarla
3. Sigue las direcciones
4. Marca cada parada con /completar
5. Reporta problemas con /problema

💡 *Consejos:*
- Mantén el bot abierto para recibir rutas
- Reporta cualquier problema inmediatamente
- Confirma cada entrega/recogida

📞 *Contacto:* +52 55 1234-5678"""
    
    send_message(chat_id, mensaje)

def handle_ubicacion_recibida(chat_id, location):
    """Procesar ubicación recibida"""
    lat = location['latitude']
    lng = location['longitude']
    
    # Guardar ubicación del repartidor
    repartidor = repartidores_activos.get(str(chat_id), {})
    repartidor['ultima_ubicacion'] = {'lat': lat, 'lng': lng, 'timestamp': time.time()}
    repartidores_activos[str(chat_id)] = repartidor
    
    mensaje = f"""📍 *Ubicación Actualizada*

✅ Ubicación registrada correctamente
📊 Coordenadas: {lat:.4f}, {lng:.4f}
⏰ Hora: {time.strftime('%H:%M:%S')}

💡 Usa /ruta para ver tu próxima parada"""
    
    send_message(chat_id, mensaje)
    
    # Notificar al admin con ubicación
    if ADMIN_CHAT_ID:
        repartidor_info = repartidores_activos.get(str(chat_id), {})
        nombre = repartidor_info.get('nombre', f'Chat {chat_id}')
        send_message(ADMIN_CHAT_ID, f"📍 Ubicación de {nombre}: {lat:.4f}, {lng:.4f}")

def asignar_ruta_repartidor(chat_id, ruta_data):
    """Función para asignar ruta desde el admin (llamada desde Flask)"""
    try:
        # Guardar ruta
        rutas_asignadas[str(chat_id)] = {
            'rutas': ruta_data.get('rutas', {}),
            'tipo': ruta_data.get('tipo', 'recoleccion'),
            'fecha': ruta_data.get('fecha', 'Hoy'),
            'total_pedidos': ruta_data.get('total_pedidos', 0),
            'completados': 0,
            'estado': 'asignada',
            'asignada_en': time.time()
        }
        
        # Registrar repartidor si no existe
        if str(chat_id) not in repartidores_activos:
            repartidores_activos[str(chat_id)] = {
                'nombre': f'Repartidor_{chat_id}',
                'estado': 'activo',
                'pedidos_hoy': 0,
                'tiempo_activo': '0h 0m'
            }
        
        return True
    except Exception as e:
        print(f"❌ Error asignando ruta: {e}")
        return False

def enviar_ruta_telegram(chat_id, ruta_data, repartidor_nombre="Repartidor"):
    """Enviar ruta completa por Telegram al repartidor"""
    try:
        # Asignar la ruta
        if not asignar_ruta_repartidor(chat_id, ruta_data):
            return False
        
        # Crear mensaje principal
        tipo = ruta_data.get('tipo', 'recoleccion')
        fecha = ruta_data.get('fecha', 'Hoy')
        total_pedidos = ruta_data.get('total_pedidos', 0)
        rutas = ruta_data.get('rutas', {})
        
        mensaje_principal = f"""🗺️ *NUEVA RUTA ASIGNADA*

👤 *Repartidor:* {repartidor_nombre}
📅 *Fecha:* {fecha}
🚚 *Tipo:* {tipo.upper()}
📦 *Total Pedidos:* {total_pedidos}
🏘️ *Zonas:* {len(rutas)}

⏰ *Horarios:*
- Recolección: 9:00-12:00
- Entrega: 14:00-18:00

🎯 *Instrucciones:*
1. Usa /iniciar para activar la ruta
2. Usa /ruta para ver detalles
3. Comparte tu ubicación regularmente
4. Usa /completar en cada parada
5. Reporta problemas con /problema

¡Buena suerte! 🚛"""
        
        # Enviar mensaje principal
        result = send_message(chat_id, mensaje_principal)
        
        if not result or not result.get('ok'):
            return False
        
        # Enviar detalles de cada zona
        zona_num = 1
        for zona, pedidos in rutas.items():
            mensaje_zona = f"""📍 *ZONA {zona_num}: {zona.upper()}*
🎯 *Paradas:* {len(pedidos)}

"""
            
            for i, pedido in enumerate(pedidos, 1):
                emoji = "📦" if tipo == "recoleccion" else "🏠"
                mensaje_zona += f"""{i}️⃣ {emoji} *Pedido #{pedido.get('id', 'N/A')}*
👤 {pedido.get('cliente', 'Cliente')}
📍 {pedido.get('direccion', 'Dirección')[:40]}...
📱 {pedido.get('telefono', 'No disponible')}
💰 ${pedido.get('precio', 0)}
"""
                if pedido.get('notas'):
                    mensaje_zona += f"📝 {pedido['notas']}\n"
                mensaje_zona += "\n"
            
            mensaje_zona += f"---\n"
            send_message(chat_id, mensaje_zona)
            zona_num += 1
        
        # Mensaje final con comandos
        mensaje_comandos = f"""🎮 *COMANDOS PARA TU RUTA:*

▶️ /iniciar - Comenzar ruta
📋 /ruta - Ver progreso actual  
✅ /completar - Marcar parada completada
📍 Enviar ubicación - Para seguimiento
🆘 /problema - Reportar incidencia
❓ /ayuda - Ayuda completa

🎯 *IMPORTANTE:*
- Confirma cada recogida/entrega
- Mantén contacto con los clientes
- Reporta cualquier problema
- Comparte tu ubicación regularmente

¡Tu ruta está lista para comenzar! 🚚💨"""
        
        send_message(chat_id, mensaje_comandos)
        
        print(f"✅ Ruta enviada exitosamente a {repartidor_nombre} ({chat_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando ruta: {e}")
        return False
# Funciones para integrar con la base de datos web
def registrar_repartidor_en_db(chat_id, nombre):
    """Registrar repartidor en la base de datos web"""
    try:
        import sqlite3
        conn = sqlite3.connect('instance/lavanderia.db')
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repartidor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_chat_id TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                activo BOOLEAN DEFAULT 1,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insertar o actualizar repartidor
        cursor.execute('''
            INSERT OR REPLACE INTO repartidor (telegram_chat_id, nombre, activo)
            VALUES (?, ?, 1)
        ''', (chat_id, nombre))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error registrando repartidor: {e}")
        return False

def handle_registro_repartidor(chat_id, user_name):
    """Registrar nuevo repartidor"""
    try:
        # Registrar en memoria del bot
        repartidores_activos[str(chat_id)] = {
            'nombre': user_name,
            'estado': 'activo',
            'pedidos_hoy': 0,
            'tiempo_activo': '0h 0m',
            'registrado_en': time.time()
        }
        
        # Registrar en base de datos web
        web_success = registrar_repartidor_en_db(str(chat_id), user_name)
        
        # Registrar en base de datos del bot
        bot_success = registrar_en_bot_db(str(chat_id), user_name)
        
        status_web = "✅" if web_success else "❌"
        status_bot = "✅" if bot_success else "❌"
        
        mensaje = f"""✅ *Registro Exitoso*

👤 *Repartidor:* {user_name}
📱 *Chat ID:* {chat_id}
⭐ *Estado:* Activo
📅 *Registrado:* {time.strftime('%d/%m/%Y %H:%M')}

💾 *Bases de datos:*
- Web DB: {status_web}
- Bot DB: {status_bot}

🚛 *Próximos pasos:*
- Espera a recibir tu primera ruta
- Usa /ayuda para ver todos los comandos
- Mantén el bot abierto para notificaciones

¡Bienvenido al equipo! 🎉"""
        
        send_message(chat_id, mensaje)
        
        # Notificar al admin
        if ADMIN_CHAT_ID:
            send_message(ADMIN_CHAT_ID, f"🆕 Nuevo repartidor registrado: {user_name} (ID: {chat_id})")
            
        print(f"✅ Repartidor {user_name} registrado - Web: {web_success}, Bot: {bot_success}")
        
    except Exception as e:
        print(f"❌ Error en registro: {e}")
        send_message(chat_id, f"❌ Error en el registro: {str(e)}")

def registrar_en_bot_db(chat_id, nombre):
    """Registrar en la base de datos del bot (repartidores.db)"""
    try:
        import sqlite3
        
        # Crear la base de datos del bot
        conn = sqlite3.connect('repartidores.db')
        cursor = conn.cursor()
        
        # Crear tabla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repartidores (
                chat_id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                activo BOOLEAN DEFAULT 1,
                ruta_activa TEXT,
                ubicacion_lat REAL,
                ubicacion_lng REAL,
                parada_actual INTEGER DEFAULT 0,
                pedidos_completados TEXT DEFAULT '[]',
                inicio_ruta TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insertar repartidor
        cursor.execute('''
            INSERT OR REPLACE INTO repartidores 
            (chat_id, nombre, activo) VALUES (?, ?, 1)
        ''', (chat_id, nombre))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Repartidor guardado en repartidores.db: {nombre}")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando en bot DB: {e}")
        return False

def main():
    """Función principal del bot"""
    print("🤖 Bot completo iniciado...")
    print(f"📱 Admin Chat ID: {ADMIN_CHAT_ID}")
    
    # Notificar que el bot se inició
    if ADMIN_CHAT_ID:
        send_message(
            ADMIN_CHAT_ID, 
            "🤖 *Bot de Lavandería Iniciado*\n\n"
            "✅ Sistema operativo\n"
            "📱 Notificaciones activas\n"
            "🔄 Esperando comandos..."
        )
    
    offset = 0
    
    while True:
        try:
            # Obtener updates
            url = f"{BASE_URL}/getUpdates"
            params = {'offset': offset, 'timeout': 5}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('ok'):
                updates = data.get('result', [])
                
                if updates:
                    print(f"📨 Recibidos {len(updates)} mensajes")
                
                for update in updates:
                    offset = update['update_id'] + 1
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message['chat']['id']
                        text = message.get('text', '')
                        user_name = message['from'].get('first_name', 'Usuario')
                        
                        print(f"💬 {user_name} ({chat_id}): {text}")
                        
                        # Manejar comandos
                        if text == '/start':
                            handle_start(chat_id, user_name)
                        elif text == '/id':
                            send_message(chat_id, f"Tu Chat ID: `{chat_id}`")
                        elif text == '/test':
                            send_message(chat_id, "🤖 Bot funcionando perfectamente ✅")
                        elif text == '/admin':
                            handle_admin(chat_id, user_name)
                        elif text == '/registro':
                            handle_registro_repartidor(chat_id, user_name)
                        elif text == '/estado':
                            handle_estado_repartidor(chat_id, user_name)
                        elif text == '/iniciar' or text == '/iniciar_ruta':
                            handle_iniciar_ruta(chat_id, user_name)
                        elif text == '/ruta' or text == '/mi_ruta':
                            handle_ver_ruta(chat_id, user_name)
                        elif text == '/completar':
                            handle_completar_parada(chat_id, user_name)
                        elif text == '/problema':
                            handle_reportar_problema(chat_id, user_name)
                        elif text == '/ayuda' or text == '/help':
                            handle_ayuda_repartidor(chat_id, user_name)
                        elif 'location' in message:
                            handle_ubicacion_recibida(chat_id, message['location'])
                        else:
                            send_message(chat_id, "Usa /start para ver los comandos disponibles.")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo bot...")
            if ADMIN_CHAT_ID:
                send_message(ADMIN_CHAT_ID, "🛑 Bot detenido")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(3)

def enviar_ruta_desde_admin(chat_id, ruta_data, repartidor_nombre="Repartidor"):
    """Función para ser llamada desde el admin panel de Flask"""
    try:
        return enviar_ruta_telegram(chat_id, ruta_data, repartidor_nombre)
    except Exception as e:
        print(f"❌ Error enviando ruta desde admin: {e}")
        return False

def obtener_repartidores_activos():
    """Función para obtener lista de repartidores activos (para el admin panel)"""
    try:
        repartidores_lista = []
        for chat_id, datos in repartidores_activos.items():
            repartidores_lista.append({
                'chat_id': chat_id,
                'nombre': datos.get('nombre', f'Repartidor_{chat_id}'),
                'estado': datos.get('estado', 'activo'),
                'tiene_ruta': chat_id in rutas_asignadas,
                'disponible': datos.get('estado') == 'activo' and chat_id not in rutas_asignadas
            })
        return repartidores_lista
    except Exception as e:
        print(f"❌ Error obteniendo repartidores: {e}")
        return []

if __name__ == "__main__":
    main()


# IMPORTANTE: Esta función se puede importar desde Flask
def notificar_pedido_flask(pedido_id, usuario_nombre, direccion, total):
    """Función específica para llamar desde Flask"""
    return enviar_notificacion_pedido(pedido_id, usuario_nombre, direccion, total)