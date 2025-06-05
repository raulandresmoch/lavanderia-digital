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

def send_message(chat_id, text, parse_mode='Markdown'):
    """Enviar mensaje"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    try:
        response = requests.post(url, data=data, timeout=10)
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

*Comandos:*
• /start - Este mensaje
• /test - Probar bot
• /registro - Registrarte
• /estado - Tu estado
• /id - Tu Chat ID
• /admin - Info admin

*Sistema:* ✅ Funcionando
"""
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
                            send_message(
                                chat_id, 
                                f"✅ *Registrado*\n\n"
                                f"👤 {user_name}\n"
                                f"📱 Chat ID: `{chat_id}`\n"
                                f"⭐ Estado: Repartidor Activo"
                            )
                        elif text == '/estado':
                            send_message(
                                chat_id,
                                f"📊 *Estado*\n\n"
                                f"👤 {user_name}\n"
                                f"📱 ID: `{chat_id}`\n"
                                f"✅ Sistema: Operativo"
                            )
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

if __name__ == "__main__":
    main()

# IMPORTANTE: Esta función se puede importar desde Flask
def notificar_pedido_flask(pedido_id, usuario_nombre, direccion, total):
    """Función específica para llamar desde Flask"""
    return enviar_notificacion_pedido(pedido_id, usuario_nombre, direccion, total)