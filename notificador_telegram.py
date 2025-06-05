# notificador_telegram.py - Enviar notificaciones desde Flask
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def enviar_notificacion_pedido(pedido_id, usuario_nombre, direccion, total):
    """Enviar notificación de nuevo pedido a admin"""
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHATS')
        
        if not token or not admin_chat_id:
            print("❌ Token o Chat ID no configurado")
            return False
        
        mensaje = f"""🆕 *NUEVO PEDIDO*

📋 *Pedido #{pedido_id}*
👤 *Cliente:* {usuario_nombre}
📍 *Dirección:* {direccion}
💰 *Total:* ${total}

🔗 Ver en admin: http://localhost:5000/admin
"""
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': admin_chat_id,
            'text': mensaje,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Notificación enviada para pedido #{pedido_id}")
            return True
        else:
            print(f"❌ Error enviando notificación: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Función de prueba
if __name__ == "__main__":
    # Probar notificación
    enviar_notificacion_pedido(123, "Raul Andres", "Roma Norte", 150.00)