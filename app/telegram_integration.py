import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configuración
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id, text, parse_mode='Markdown'):
    """Enviar mensaje por Telegram"""
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"✅ Mensaje enviado a {chat_id}")
            return True
        else:
            logger.error(f"❌ Error enviando mensaje: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en send_message: {e}")
        return False

def enviar_ruta_completa(chat_id, ruta_data, ruta_id=""):
    """Enviar ruta completa formateada a repartidor"""
    try:
        # Extraer información de la ruta
        zonas = ruta_data.get('rutas', {})
        total_pedidos = ruta_data.get('total_pedidos', 0)
        tipo_ruta = ruta_data.get('tipo', 'desconocido')
        fecha = ruta_data.get('fecha', datetime.now().strftime('%Y-%m-%d'))
        
        if not zonas or total_pedidos == 0:
            send_message(chat_id, "⚠️ No hay pedidos para esta ruta.")
            return True
        
        # Crear mensaje principal
        mensaje_principal = f"""🗺️ *NUEVA RUTA ASIGNADA*

📅 *Fecha:* {fecha}
🚚 *Tipo:* {tipo_ruta.title()}
📦 *Total Pedidos:* {total_pedidos}
🏘️ *Zonas:* {len(zonas)}
🆔 *ID Ruta:* {ruta_id}

⏰ *Horarios de Servicio:*
• Recolección: 9:00 AM - 12:00 PM
• Entrega: 2:00 PM - 6:00 PM

📋 *RUTAS POR ZONA:*"""
        
        # Enviar mensaje principal
        if not send_message(chat_id, mensaje_principal):
            return False
        
        # Enviar cada zona por separado
        zona_num = 1
        for zona_nombre, pedidos in zonas.items():
            mensaje_zona = f"""📍 *ZONA {zona_num}: {zona_nombre}*
🎯 *Paradas:* {len(pedidos)}

"""
            
            # Agregar cada pedido
            for i, pedido in enumerate(pedidos, 1):
                emoji_orden = f"{i}️⃣" if i <= 10 else f"🔹"
                emoji_tipo = "📦" if tipo_ruta == "recoleccion" else "🏠"
                
                mensaje_zona += f"""{emoji_orden} {emoji_tipo} *Pedido #{pedido['id']}*
👤 *Cliente:* {pedido['cliente']}
📍 *Dirección:* {pedido['direccion']}
📱 *Teléfono:* {pedido['telefono']}
💰 *Total:* ${pedido.get('total', 0)}"""
                
                if pedido.get('notas'):
                    mensaje_zona += f"\n💡 *Nota:* {pedido['notas']}"
                
                mensaje_zona += "\n\n"
            
            # Agregar instrucciones de la zona
            mensaje_zona += f"""🎯 *INSTRUCCIONES ZONA {zona_num}:*
1️⃣ Confirma cada parada 
2️⃣ Reporta problemas 
3️⃣ Navega con Google Maps
4️⃣ Mantén contacto con clientes

---"""
            
            # Enviar zona (dividir si es muy largo)
            if len(mensaje_zona) > 4000:
                # Dividir en mensajes más pequeños
                partes = mensaje_zona.split('\n\n')
                mensaje_actual = f"📍 *ZONA {zona_num}: {zona_nombre}*\n🎯 *Paradas:* {len(pedidos)}\n\n"
                
                for parte in partes:
                    if len(mensaje_actual + parte) > 3800:
                        send_message(chat_id, mensaje_actual)
                        mensaje_actual = parte + "\n\n"
                    else:
                        mensaje_actual += parte + "\n\n"
                
                if mensaje_actual.strip():
                    send_message(chat_id, mensaje_actual)
            else:
                send_message(chat_id, mensaje_zona)
            
            zona_num += 1
        
        # Mensaje final con comandos
        mensaje_comandos = f"""🎮 *COMANDOS DISPONIBLES:*

▶️ `/iniciar` - Comenzar ruta
🏁 `/finalizar` - Terminar ruta  
📍 `/ubicacion` - Compartir ubicación
❓ `/ayuda` - Obtener ayuda
🆘 `/problema` - Reportar incidencia

🎯 *IMPORTANTE:*
• Confirma cada recogida/entrega
• Mantén contacto con los clientes
• Reporta cualquier problema
• Revisa el tráfico antes de salir

¡Buena suerte con tu ruta! 🚚💨"""
        
        send_message(chat_id, mensaje_comandos)
        
        logger.info(f"✅ Ruta completa enviada a {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando ruta completa: {e}")
        return False