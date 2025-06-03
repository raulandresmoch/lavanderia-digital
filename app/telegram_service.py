import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from openai import OpenAI

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RutaOptimizada:
    orden_paradas: List[Dict]
    distancia_total: float
    tiempo_estimado: int
    instrucciones: str
    mapa_url: str

@dataclass
class Notificacion:
    tipo: str
    destinatario: str
    mensaje: str
    datos_extra: Dict = None

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.admin_chat_ids = os.getenv('TELEGRAM_ADMIN_CHATS', '').split(',')
        self.repartidor_chat_ids = {}  # Se cargarán desde la base de datos
        
        # Configurar OpenAI
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Configurar bot
        self.bot = Bot(token=self.bot_token)
        self.application = None
        
    async def inicializar_bot(self):
        """Inicializar el bot de Telegram"""
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            # Agregar handlers
            self.application.add_handler(CommandHandler("start", self.comando_start))
            self.application.add_handler(CommandHandler("registro", self.comando_registro))
            self.application.add_handler(CommandHandler("rutas", self.comando_rutas))
            self.application.add_handler(CommandHandler("estado", self.comando_estado))
            self.application.add_handler(CallbackQueryHandler(self.manejar_callback))
            
            # Inicializar bot
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Bot de Telegram inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando bot: {e}")
            return False
    
    async def comando_start(self, update: Update, context):
        """Comando /start"""
        chat_id = update.effective_chat.id
        username = update.effective_user.username or "Usuario"
        
        mensaje = f"""🚚 *Lavandería Digital - Bot de Rutas*

¡Hola {username}! 👋

*Comandos disponibles:*
🔸 /registro - Registrarte como repartidor
🔸 /rutas - Ver rutas asignadas
🔸 /estado - Estado actual de entregas

*¿Eres administrador?*
El bot te notificará automáticamente sobre nuevos pedidos y el progreso de las rutas.

*¿Eres repartidor?*
Usa /registro para comenzar a recibir rutas optimizadas.
"""
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    
    async def comando_registro(self, update: Update, context):
        """Registro de repartidores"""
        chat_id = update.effective_chat.id
        username = update.effective_user.username
        
        # Aquí conectarías con tu base de datos para registrar al repartidor
        # Por ahora, guardamos en memoria
        self.repartidor_chat_ids[chat_id] = {
            'username': username,
            'activo': True,
            'fecha_registro': datetime.now()
        }
        
        mensaje = f"""✅ *Registro Exitoso*

¡Bienvenido al equipo, {username}! 🚚

*Tu Chat ID:* `{chat_id}`
*Estado:* Activo ✅

Ahora recibirás:
🔸 Rutas optimizadas automáticamente
🔸 Instrucciones detalladas de navegación
🔸 Notificaciones de nuevos pedidos

*Próximos pasos:*
Espera a recibir tu primera ruta. Te notificaremos cuando tengas pedidos para recoger/entregar.
"""
        
        # Notificar a admins
        await self.notificar_admins(f"🆕 Nuevo repartidor registrado: {username} (ID: {chat_id})")
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    
    async def comando_rutas(self, update: Update, context):
        """Ver rutas asignadas"""
        chat_id = update.effective_chat.id
        
        # Aquí conectarías con tu base de datos para obtener rutas
        # Por ahora, simulamos datos
        rutas_pendientes = await self.obtener_rutas_repartidor(chat_id)
        
        if not rutas_pendientes:
            mensaje = """📋 *Estado de Rutas*

No tienes rutas asignadas en este momento.

Recibirás una notificación automática cuando tengas nuevos pedidos para recoger o entregar. 📱"""
        else:
            mensaje = "📋 *Tus Rutas Activas*\n\n"
            for i, ruta in enumerate(rutas_pendientes, 1):
                mensaje += f"*Ruta {i}:*\n"
                mensaje += f"🕐 Hora: {ruta['hora_inicio']}\n"
                mensaje += f"📍 Paradas: {ruta['total_paradas']}\n"
                mensaje += f"⭐ Estado: {ruta['estado']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Actualizar", callback_data="actualizar_rutas")],
            [InlineKeyboardButton("📍 Ver Mapa", callback_data="ver_mapa")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(mensaje, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def comando_estado(self, update: Update, context):
        """Estado actual del repartidor"""
        chat_id = update.effective_chat.id
        
        # Obtener estado desde base de datos
        estado = await self.obtener_estado_repartidor(chat_id)
        
        mensaje = f"""📊 *Tu Estado Actual*

🚚 *Repartidor:* {estado['nombre']}
📱 *Chat ID:* `{chat_id}`
⭐ *Estado:* {estado['estado']}
📦 *Pedidos Hoy:* {estado['pedidos_hoy']}
🛣️ *Rutas Completadas:* {estado['rutas_completadas']}
⏱️ *Tiempo Activo:* {estado['tiempo_activo']}

*Última Actividad:* {estado['ultima_actividad']}
"""
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    
    async def manejar_callback(self, update: Update, context):
        """Manejar callbacks de botones"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "actualizar_rutas":
            await self.comando_rutas(update, context)
        elif query.data == "ver_mapa":
            await self.enviar_mapa_ruta(query.message.chat_id)
        elif query.data.startswith("iniciar_ruta_"):
            ruta_id = query.data.split("_")[2]
            await self.iniciar_ruta(query.message.chat_id, ruta_id)
        elif query.data.startswith("confirmar_pickup_"):
            pedido_id = query.data.split("_")[2]
            await self.confirmar_pickup(query.message.chat_id, pedido_id)
        elif query.data.startswith("finalizar_ruta_"):
            ruta_id = query.data.split("_")[2]
            await self.finalizar_ruta(query.message.chat_id, ruta_id)
    
    async def optimizar_ruta_con_ia(self, pedidos: List[Dict]) -> RutaOptimizada:
        """Optimizar ruta usando ChatGPT"""
        try:
            # Preparar datos para la IA
            ubicaciones = []
            for pedido in pedidos:
                ubicaciones.append({
                    'id': pedido['id'],
                    'tipo': pedido['tipo'],  # 'recoleccion' o 'entrega'
                    'direccion': pedido['direccion'],
                    'lat': pedido['latitud'],
                    'lng': pedido['longitud'],
                    'cliente': pedido['cliente'],
                    'notas': pedido.get('notas', ''),
                    'prioridad': pedido.get('prioridad', 'normal')
                })
            
            prompt = f"""
Como experto en optimización de rutas de entrega, necesito que optimices la siguiente ruta para un repartidor de lavandería en Ciudad de México.

UBICACIONES A VISITAR:
{json.dumps(ubicaciones, indent=2, ensure_ascii=False)}

REGLAS DE OPTIMIZACIÓN:
1. Las recolecciones tienen prioridad sobre las entregas
2. Minimizar la distancia total recorrida
3. Considerar el tráfico típico de CDMX
4. Agrupar paradas cercanas geográficamente
5. Respetar horarios: Recolecciones 9:00-12:00, Entregas 14:00-18:00

RESPONDE EN FORMATO JSON con esta estructura:
{{
    "orden_paradas": [
        {{
            "paso": 1,
            "pedido_id": "ID",
            "tipo": "recoleccion/entrega",
            "direccion": "dirección",
            "cliente": "nombre",
            "hora_estimada": "HH:MM",
            "tiempo_parada": 5,
            "instrucciones": "detalles específicos"
        }}
    ],
    "resumen": {{
        "distancia_total_km": 0.0,
        "tiempo_total_minutos": 0,
        "total_paradas": 0,
        "hora_inicio": "09:00",
        "hora_fin": "18:00"
    }},
    "optimizaciones": [
        "Razón de optimización 1",
        "Razón de optimización 2"
    ],
    "consejos_repartidor": [
        "Consejo práctico 1",
        "Consejo práctico 2"
    ]
}}
"""
            
            # Llamar a OpenAI
            if not self.openai_client:
                raise Exception("OpenAI client no configurado")
            response = await self.openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto optimizador de rutas de entrega en Ciudad de México. Respondes únicamente en formato JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            resultado = json.loads(response.choices[0].message.content)
            
            # Generar URL del mapa
            mapa_url = self.generar_url_mapa(resultado['orden_paradas'])
            
            return RutaOptimizada(
                orden_paradas=resultado['orden_paradas'],
                distancia_total=resultado['resumen']['distancia_total_km'],
                tiempo_estimado=resultado['resumen']['tiempo_total_minutos'],
                instrucciones=self.formatear_instrucciones(resultado),
                mapa_url=mapa_url
            )
            
        except Exception as e:
            logger.error(f"Error optimizando ruta con IA: {e}")
            # Fallback: optimización básica por distancia
            return await self.optimizar_ruta_basica(pedidos)
    
    def generar_url_mapa(self, paradas: List[Dict]) -> str:
        """Generar URL de Google Maps con la ruta"""
        if not paradas:
            return ""
        
        # Punto de inicio (base de operaciones)
        origen = "19.4326,-99.1332"  # Centro CDMX
        
        # Waypoints intermedios
        waypoints = []
        for parada in paradas[:-1]:  # Todas excepto la última
            waypoints.append(f"{parada.get('lat', 0)},{parada.get('lng', 0)}")
        
        # Destino final
        destino = f"{paradas[-1].get('lat', 0)},{paradas[-1].get('lng', 0)}"
        
        # Construir URL
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origen}/"
        
        if waypoints:
            url += "/".join(waypoints) + "/"
        
        url += f"{destino}"
        
        return url
    
    def formatear_instrucciones(self, resultado: Dict) -> str:
        """Formatear instrucciones para el repartidor"""
        instrucciones = f"""🗺️ *RUTA OPTIMIZADA*

📊 *Resumen:*
• 📍 Paradas: {resultado['resumen']['total_paradas']}
• 🛣️ Distancia: {resultado['resumen']['distancia_total_km']} km
• ⏱️ Tiempo: {resultado['resumen']['tiempo_total_minutos']} min
• 🕘 Inicio: {resultado['resumen']['hora_inicio']}
• 🕕 Fin: {resultado['resumen']['hora_fin']}

📋 *PARADAS EN ORDEN:*
"""
        
        for parada in resultado['orden_paradas']:
            emoji = "📦" if parada['tipo'] == 'recoleccion' else "🏠"
            instrucciones += f"""
{emoji} *Parada {parada['paso']}* - {parada['hora_estimada']}
📍 {parada['direccion']}
👤 {parada['cliente']}
⏱️ {parada['tiempo_parada']} min
💡 {parada['instrucciones']}
"""
        
        if 'consejos_repartidor' in resultado:
            instrucciones += "\n🎯 *CONSEJOS:*\n"
            for consejo in resultado['consejos_repartidor']:
                instrucciones += f"• {consejo}\n"
        
        return instrucciones
    
    async def enviar_ruta_repartidor(self, chat_id: str, ruta: RutaOptimizada, ruta_id: str):
        """Enviar ruta optimizada al repartidor"""
        try:
            # Mensaje principal con la ruta
            await self.bot.send_message(
                chat_id=chat_id,
                text=ruta.instrucciones,
                parse_mode='Markdown'
            )
            
            # Botones de acción
            keyboard = [
                [InlineKeyboardButton("🚀 Iniciar Ruta", callback_data=f"iniciar_ruta_{ruta_id}")],
                [InlineKeyboardButton("🗺️ Ver en Maps", url=ruta.mapa_url)],
                [InlineKeyboardButton("❓ Ayuda", callback_data="ayuda_ruta")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text="🎯 *¿Listo para comenzar?*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando ruta: {e}")
            return False
    
    async def notificar_admins(self, mensaje: str, datos_extra: Dict = None):
        """Notificar a todos los administradores"""
        for admin_chat_id in self.admin_chat_ids:
            if admin_chat_id.strip():
                try:
                    await self.bot.send_message(
                        chat_id=admin_chat_id.strip(),
                        text=f"🔔 *NOTIFICACIÓN ADMIN*\n\n{mensaje}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error notificando admin {admin_chat_id}: {e}")
    
    async def confirmar_pickup(self, chat_id: str, pedido_id: str):
        """Confirmar recogida de pedido"""
        try:
            # Actualizar estado en base de datos
            # await self.actualizar_estado_pedido(pedido_id, "recolectado")
            
            # Notificar al repartidor
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"✅ *Recogida Confirmada*\n\nPedido #{pedido_id} marcado como recolectado.\n\n¡Continúa con la siguiente parada! 🚚",
                parse_mode='Markdown'
            )
            
            # Notificar a admins
            await self.notificar_admins(f"📦 Pedido #{pedido_id} recolectado por repartidor {chat_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error confirmando pickup: {e}")
            return False
    
    async def finalizar_ruta(self, chat_id: str, ruta_id: str):
        """Finalizar ruta completa"""
        try:
            # Obtener resumen de la ruta
            resumen = await self.obtener_resumen_ruta(ruta_id)
            
            mensaje = f"""🎉 *¡RUTA COMPLETADA!*

📊 *Resumen Final:*
🆔 Ruta: #{ruta_id}
📦 Pedidos: {resumen['total_pedidos']}
✅ Completados: {resumen['completados']}
⏱️ Tiempo: {resumen['tiempo_total']}
🛣️ Distancia: {resumen['distancia']} km

¡Excelente trabajo! 👏
"""
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=mensaje,
                parse_mode='Markdown'
            )
            
            # Notificar a admins
            await self.notificar_admins(f"🏁 Ruta #{ruta_id} completada por repartidor {chat_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error finalizando ruta: {e}")
            return False
    
    # Métodos auxiliares (conectar con tu base de datos)
    async def obtener_rutas_repartidor(self, chat_id: str):
        """Obtener rutas asignadas a un repartidor desde la BD"""
        # Conectar con tu base de datos
        return []
    
    async def obtener_estado_repartidor(self, chat_id: str):
        """Obtener estado actual del repartidor"""
        return {
            'nombre': 'Repartidor',
            'estado': 'Disponible',
            'pedidos_hoy': 0,
            'rutas_completadas': 0,
            'tiempo_activo': '0h 0m',
            'ultima_actividad': 'Hace 5 minutos'
        }
    
    async def obtener_resumen_ruta(self, ruta_id: str):
        """Obtener resumen de ruta completada"""
        return {
            'total_pedidos': 5,
            'completados': 5,
            'tiempo_total': '4h 30m',
            'distancia': 25.6
        }

# Instancia global del servicio
telegram_service = TelegramService()