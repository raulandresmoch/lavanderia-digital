# bot_repartidor_completo.py - Sistema completo de bot para repartidores con GPS
import requests
import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sqlite3
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import threading
import asyncio

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHATS')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # Nueva variable
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ===== MODELOS DE DATOS =====
@dataclass
class RepartidorEstado:
    chat_id: str
    nombre: str
    activo: bool = False
    ruta_activa: Optional[Dict] = None
    ubicacion_actual: Optional[Dict] = None
    parada_actual: int = 0
    pedidos_completados: List[int] = None
    inicio_ruta: Optional[datetime] = None
    
    def __post_init__(self):
        if self.pedidos_completados is None:
            self.pedidos_completados = []

@dataclass
class Pedido:
    id: int
    cliente: str
    direccion: str
    telefono: str
    latitud: float
    longitud: float
    notas: str = ""
    completado: bool = False

# ===== BASE DE DATOS SQLITE PARA REPARTIDORES =====
class RepartidorDB:
    def __init__(self):
        self.db_path = 'repartidores.db'
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repartidores (
                chat_id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                activo BOOLEAN DEFAULT 0,
                ruta_activa TEXT,
                ubicacion_lat REAL,
                ubicacion_lng REAL,
                parada_actual INTEGER DEFAULT 0,
                pedidos_completados TEXT,
                inicio_ruta TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ubicaciones_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                latitud REAL,
                longitud REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES repartidores (chat_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def registrar_repartidor(self, chat_id: str, nombre: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO repartidores (chat_id, nombre, activo)
            VALUES (?, ?, 1)
        ''', (chat_id, nombre))
        
        conn.commit()
        conn.close()
    
    def obtener_repartidor(self, chat_id: str) -> Optional[RepartidorEstado]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM repartidores WHERE chat_id = ?', (chat_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return RepartidorEstado(
            chat_id=row[0],
            nombre=row[1],
            activo=bool(row[2]),
            ruta_activa=json.loads(row[3]) if row[3] else None,
            ubicacion_actual={'lat': row[4], 'lng': row[5]} if row[4] and row[5] else None,
            parada_actual=row[6],
            pedidos_completados=json.loads(row[7]) if row[7] else [],
            inicio_ruta=datetime.fromisoformat(row[8]) if row[8] else None
        )
    
    def actualizar_ubicacion(self, chat_id: str, latitud: float, longitud: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Actualizar ubicación actual
        cursor.execute('''
            UPDATE repartidores 
            SET ubicacion_lat = ?, ubicacion_lng = ?
            WHERE chat_id = ?
        ''', (latitud, longitud, chat_id))
        
        # Guardar en histórico
        cursor.execute('''
            INSERT INTO ubicaciones_historico (chat_id, latitud, longitud)
            VALUES (?, ?, ?)
        ''', (chat_id, latitud, longitud))
        
        conn.commit()
        conn.close()
    
    def actualizar_ruta_activa(self, chat_id: str, ruta_data: Dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE repartidores 
            SET ruta_activa = ?, inicio_ruta = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        ''', (json.dumps(ruta_data), chat_id))
        
        conn.commit()
        conn.close()

# ===== SERVICIOS DE GOOGLE MAPS =====
class GoogleMapsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def calcular_distancia(self, origen: Dict, destino: Dict) -> Dict:
        """Calcular distancia y tiempo entre dos puntos"""
        url = f"{self.base_url}/distancematrix/json"
        params = {
            'origins': f"{origen['lat']},{origen['lng']}",
            'destinations': f"{destino['lat']},{destino['lng']}",
            'mode': 'driving',
            'language': 'es',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                if element['status'] == 'OK':
                    return {
                        'distancia': element['distance']['text'],
                        'tiempo': element['duration']['text'],
                        'distancia_metros': element['distance']['value'],
                        'tiempo_segundos': element['duration']['value']
                    }
            return None
        except Exception as e:
            print(f"Error calculando distancia: {e}")
            return None
    
    def obtener_direcciones(self, origen: Dict, destino: Dict) -> str:
        """Obtener link de navegación de Google Maps"""
        origen_str = f"{origen['lat']},{origen['lng']}"
        destino_str = f"{destino['lat']},{destino['lng']}"
        
        return f"https://www.google.com/maps/dir/{origen_str}/{destino_str}/@{destino['lat']},{destino['lng']},17z/data=!3m1!4b1!4m2!4m1!3e0"
    
    def geocodificar_direccion(self, direccion: str) -> Optional[Dict]:
        """Convertir dirección en coordenadas"""
        url = f"{self.base_url}/geocode/json"
        params = {
            'address': direccion,
            'key': self.api_key,
            'language': 'es'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'direccion_formateada': data['results'][0]['formatted_address']
                }
            return None
        except Exception as e:
            print(f"Error geocodificando: {e}")
            return None

# ===== SISTEMA PRINCIPAL DEL BOT =====
class BotRepartidor:
    def __init__(self):
        self.db = RepartidorDB()
        self.maps_service = GoogleMapsService(GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None
        self.repartidores_activos: Dict[str, RepartidorEstado] = {}
        self.running = True
        
        # Cargar repartidores activos al inicio
        self.cargar_repartidores_activos()
    
    def cargar_repartidores_activos(self):
        """Cargar repartidores activos desde la base de datos"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM repartidores WHERE activo = 1')
        
        for (chat_id,) in cursor.fetchall():
            repartidor = self.db.obtener_repartidor(chat_id)
            if repartidor:
                self.repartidores_activos[chat_id] = repartidor
        
        conn.close()
    
    def send_message(self, chat_id: str, text: str, parse_mode='Markdown', reply_markup=None):
        """Enviar mensaje con markup personalizado"""
        url = f"{BASE_URL}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return None
    
    def send_location(self, chat_id: str, latitud: float, longitud: float, 
                     live_period: int = None, heading: int = None):
        """Enviar ubicación por Telegram"""
        url = f"{BASE_URL}/sendLocation"
        data = {
            'chat_id': chat_id,
            'latitude': latitud,
            'longitude': longitud
        }
        
        if live_period:
            data['live_period'] = live_period
        if heading:
            data['heading'] = heading
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ Error enviando ubicación: {e}")
            return None
    
    def crear_teclado_principal(self) -> Dict:
        """Crear teclado principal para repartidores"""
        return {
            'keyboard': [
                [{'text': '📍 Enviar Ubicación', 'request_location': True}],
                [{'text': '🚛 Ver Ruta Actual'}, {'text': '✅ Completar Parada'}],
                [{'text': '🆘 Reportar Problema'}, {'text': '❓ Ayuda'}],
                [{'text': '🏁 Finalizar Ruta'}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': False
        }
    
    def handle_iniciar_comando(self, chat_id: str, user_name: str):
        """Manejar comando /iniciar"""
        # Registrar o activar repartidor
        self.db.registrar_repartidor(chat_id, user_name)
        
        repartidor = self.db.obtener_repartidor(chat_id)
        self.repartidores_activos[chat_id] = repartidor
        
        mensaje = f"""🚛 *¡Bienvenido al Sistema de Reparto!*

👋 Hola *{user_name}*, has sido registrado como repartidor activo.

*¿Cómo funciona?*
1️⃣ Recibirás rutas asignadas con todos los pedidos
2️⃣ Sigue las indicaciones paso a paso
3️⃣ Envía tu ubicación para seguimiento en tiempo real
4️⃣ Marca cada parada como completada
5️⃣ Reporta cualquier problema inmediatamente

*Estado actual:* ✅ Repartidor Activo
*Ruta asignada:* {'✅ Sí' if repartidor and repartidor.ruta_activa else '❌ No'}

Usa los botones del teclado para navegar 👇"""
        
        self.send_message(
            chat_id, 
            mensaje, 
            reply_markup=self.crear_teclado_principal()
        )
    
    def handle_ubicacion_recibida(self, chat_id: str, latitud: float, longitud: float):
        """Procesar ubicación recibida del repartidor"""
        # Guardar ubicación en base de datos
        self.db.actualizar_ubicacion(chat_id, latitud, longitud)
        
        # Actualizar en memoria
        if chat_id in self.repartidores_activos:
            self.repartidores_activos[chat_id].ubicacion_actual = {
                'lat': latitud, 'lng': longitud
            }
        
        repartidor = self.repartidores_activos.get(chat_id)
        
        if not repartidor or not repartidor.ruta_activa:
            self.send_message(chat_id, "📍 *Ubicación actualizada*\n\n❌ No tienes ruta activa asignada.")
            return
        
        # Calcular distancia a próxima parada
        rutas = repartidor.ruta_activa.get('rutas', {})
        if not rutas:
            return
        
        # Obtener pedido actual
        pedido_actual = self.obtener_pedido_actual(repartidor)
        
        if not pedido_actual:
            self.send_message(chat_id, "✅ *¡Ruta completada!*\n\nTodos los pedidos han sido entregados.")
            return
        
        # Calcular distancia y tiempo si Google Maps está disponible
        if self.maps_service:
            distancia_info = self.maps_service.calcular_distancia(
                {'lat': latitud, 'lng': longitud},
                {'lat': pedido_actual['latitud'], 'lng': pedido_actual['longitud']}
            )
            
            if distancia_info:
                # Crear link de navegación
                link_navegacion = self.maps_service.obtener_direcciones(
                    {'lat': latitud, 'lng': longitud},
                    {'lat': pedido_actual['latitud'], 'lng': pedido_actual['longitud']}
                )
                
                mensaje = f"""📍 *Ubicación Actualizada*

🎯 *Próxima parada:*
📦 Pedido #{pedido_actual['id']} - {pedido_actual['cliente']}
📍 {pedido_actual['direccion']}
📱 {pedido_actual['telefono']}

📏 *Distancia:* {distancia_info['distancia']}
⏱️ *Tiempo estimado:* {distancia_info['tiempo']}

🗺️ [Abrir en Google Maps]({link_navegacion})

{f"📝 *Notas:* {pedido_actual['notas']}" if pedido_actual.get('notas') else ""}"""
                
                self.send_message(chat_id, mensaje)
                
                # Enviar ubicación del destino
                self.send_location(
                    chat_id, 
                    pedido_actual['latitud'], 
                    pedido_actual['longitud']
                )
            else:
                self.send_message(chat_id, "📍 Ubicación actualizada ✅")
        else:
            self.send_message(chat_id, "📍 Ubicación actualizada ✅\n\n⚠️ Servicio de mapas no disponible")
    
    def obtener_pedido_actual(self, repartidor: RepartidorEstado) -> Optional[Dict]:
        """Obtener el pedido actual del repartidor"""
        if not repartidor.ruta_activa:
            return None
        
        rutas = repartidor.ruta_activa.get('rutas', {})
        
        # Obtener todos los pedidos en orden
        todos_pedidos = []
        for zona, pedidos in rutas.items():
            todos_pedidos.extend(pedidos)
        
        # Filtrar pedidos no completados
        pedidos_pendientes = [
            p for p in todos_pedidos 
            if p['id'] not in repartidor.pedidos_completados
        ]
        
        return pedidos_pendientes[0] if pedidos_pendientes else None
    
    def handle_completar_parada(self, chat_id: str):
        """Manejar completar parada actual"""
        repartidor = self.repartidores_activos.get(chat_id)
        
        if not repartidor or not repartidor.ruta_activa:
            self.send_message(chat_id, "❌ No tienes ruta activa")
            return
        
        pedido_actual = self.obtener_pedido_actual(repartidor)
        
        if not pedido_actual:
            self.send_message(chat_id, "✅ ¡Todos los pedidos completados!")
            return
        
        # Marcar como completado
        repartidor.pedidos_completados.append(pedido_actual['id'])
        
        # Actualizar en base de datos
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE repartidores 
            SET pedidos_completados = ?
            WHERE chat_id = ?
        ''', (json.dumps(repartidor.pedidos_completados), chat_id))
        conn.commit()
        conn.close()
        
        # Notificar al admin
        if ADMIN_CHAT_ID:
            self.send_message(
                ADMIN_CHAT_ID,
                f"✅ *Pedido Completado*\n\n"
                f"📦 Pedido #{pedido_actual['id']}\n"
                f"👤 Cliente: {pedido_actual['cliente']}\n"
                f"🚛 Repartidor: {repartidor.nombre}\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
        
        # Obtener siguiente pedido
        siguiente_pedido = self.obtener_pedido_actual(repartidor)
        
        if siguiente_pedido:
            mensaje = f"""✅ *Pedido #{pedido_actual['id']} Completado*

🎯 *Siguiente parada:*
📦 Pedido #{siguiente_pedido['id']} - {siguiente_pedido['cliente']}
📍 {siguiente_pedido['direccion']}
📱 {siguiente_pedido['telefono']}

💡 Envía tu ubicación para obtener direcciones"""
            
            self.send_message(chat_id, mensaje)
        else:
            # Ruta completada
            self.finalizar_ruta(chat_id)
    
    def finalizar_ruta(self, chat_id: str):
        """Finalizar ruta actual"""
        repartidor = self.repartidores_activos.get(chat_id)
        
        if not repartidor:
            return
        
        # Estadísticas de la ruta
        total_pedidos = 0
        if repartidor.ruta_activa:
            rutas = repartidor.ruta_activa.get('rutas', {})
            for pedidos in rutas.values():
                total_pedidos += len(pedidos)
        
        completados = len(repartidor.pedidos_completados)
        tiempo_total = ""
        
        if repartidor.inicio_ruta:
            tiempo_transcurrido = datetime.now() - repartidor.inicio_ruta
            horas = int(tiempo_transcurrido.total_seconds() // 3600)
            minutos = int((tiempo_transcurrido.total_seconds() % 3600) // 60)
            tiempo_total = f"{horas}h {minutos}m"
        
        mensaje = f"""🏁 *¡Ruta Finalizada!*

📊 *Resumen del día:*
✅ Pedidos completados: {completados}/{total_pedidos}
⏱️ Tiempo total: {tiempo_total}
📍 Ubicaciones registradas

🎉 ¡Excelente trabajo!

Estado: 🟢 Disponible para nueva ruta"""
        
        # Limpiar ruta activa
        repartidor.ruta_activa = None
        repartidor.pedidos_completados = []
        repartidor.parada_actual = 0
        repartidor.inicio_ruta = None
        
        # Actualizar base de datos
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE repartidores 
            SET ruta_activa = NULL, pedidos_completados = '[]', 
                parada_actual = 0, inicio_ruta = NULL
            WHERE chat_id = ?
        ''', (chat_id,))
        conn.commit()
        conn.close()
        
        self.send_message(chat_id, mensaje)
        
        # Notificar al admin
        if ADMIN_CHAT_ID:
            self.send_message(
                ADMIN_CHAT_ID,
                f"🏁 *Ruta Finalizada*\n\n"
                f"🚛 Repartidor: {repartidor.nombre}\n"
                f"✅ Completados: {completados}/{total_pedidos}\n"
                f"⏱️ Tiempo: {tiempo_total}"
            )
    
    def asignar_ruta_a_repartidor(self, chat_id: str, ruta_data: Dict):
        """Asignar nueva ruta a repartidor (llamado desde admin)"""
        # Actualizar en base de datos
        self.db.actualizar_ruta_activa(chat_id, ruta_data)
        
        # Actualizar en memoria
        repartidor = self.db.obtener_repartidor(chat_id)
        if repartidor:
            self.repartidores_activos[chat_id] = repartidor
            
            # Notificar al repartidor
            total_pedidos = sum(len(pedidos) for pedidos in ruta_data.get('rutas', {}).values())
            
            mensaje = f"""🆕 *Nueva Ruta Asignada*

📋 *Tipo:* {ruta_data.get('tipo', 'Desconocido').title()}
📅 *Fecha:* {ruta_data.get('fecha', 'Hoy')}
📦 *Total pedidos:* {total_pedidos}

🎯 *Instrucciones:*
1. Envía tu ubicación para comenzar
2. Sigue la ruta paso a paso
3. Marca cada parada como completada
4. Reporta cualquier problema

¡Buena suerte! 🚛✨"""
            
            self.send_message(chat_id, mensaje)
            return True
        
        return False
    
    def procesar_mensaje(self, update: Dict):
        """Procesar mensaje recibido"""
        if 'message' not in update:
            return
        
        message = update['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        user_name = message['from'].get('first_name', 'Repartidor')
        
        # Manejar ubicación
        if 'location' in message:
            location = message['location']
            self.handle_ubicacion_recibida(
                chat_id, 
                location['latitude'], 
                location['longitude']
            )
            return
        
        # Manejar comandos y botones
        if text == '/iniciar' or text == '/start':
            self.handle_iniciar_comando(chat_id, user_name)
        
        elif text == '🚛 Ver Ruta Actual' or text == '/ruta':
            self.mostrar_ruta_actual(chat_id)
        
        elif text == '✅ Completar Parada' or text == '/completar':
            self.handle_completar_parada(chat_id)
        
        elif text == '🏁 Finalizar Ruta' or text == '/finalizar':
            self.confirmar_finalizar_ruta(chat_id)
        
        elif text == '🆘 Reportar Problema' or text == '/problema':
            self.handle_reportar_problema(chat_id)
        
        elif text == '❓ Ayuda' or text == '/ayuda' or text == '/help':
            self.mostrar_ayuda(chat_id)
        
        elif text == '📍 Enviar Ubicación' or text == '/ubicacion':
            self.solicitar_ubicacion(chat_id)
        
        else:
            # Mensaje no reconocido
            self.send_message(
                chat_id, 
                "❓ Comando no reconocido. Usa /ayuda para ver comandos disponibles.",
                reply_markup=self.crear_teclado_principal()
            )
    
    def mostrar_ruta_actual(self, chat_id: str):
        """Mostrar información de ruta actual"""
        repartidor = self.repartidores_activos.get(chat_id)
        
        if not repartidor or not repartidor.ruta_activa:
            self.send_message(chat_id, "❌ No tienes ruta activa asignada")
            return
        
        # Calcular estadísticas
        rutas = repartidor.ruta_activa.get('rutas', {})
        total_pedidos = sum(len(pedidos) for pedidos in rutas.values())
        completados = len(repartidor.pedidos_completados)
        pendientes = total_pedidos - completados
        
        # Pedido actual
        pedido_actual = self.obtener_pedido_actual(repartidor)
        
        mensaje = f"""🚛 *Ruta Actual*

📊 *Progreso:*
✅ Completados: {completados}
⏳ Pendientes: {pendientes}
📈 Total: {total_pedidos}

{f"🎯 *Próxima parada:*\n📦 Pedido #{pedido_actual['id']}\n👤 {pedido_actual['cliente']}\n📍 {pedido_actual['direccion']}\n📱 {pedido_actual['telefono']}" if pedido_actual else "🎉 ¡Todos los pedidos completados!"}

💡 Envía tu ubicación para obtener direcciones"""
        
        self.send_message(chat_id, mensaje)
    
    def solicitar_ubicacion(self, chat_id: str):
        """Solicitar ubicación al repartidor"""
        teclado = {
            'keyboard': [
                [{'text': '📍 Compartir Ubicación', 'request_location': True}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        self.send_message(
            chat_id, 
            "📍 *Compartir Ubicación*\n\nPor favor, presiona el botón para compartir tu ubicación actual:",
            reply_markup=teclado
        )
    
    def confirmar_finalizar_ruta(self, chat_id: str):
        """Confirmar finalización de ruta"""
        repartidor = self.repartidores_activos.get(chat_id)
        
        if not repartidor or not repartidor.ruta_activa:
            self.send_message(chat_id, "❌ No tienes ruta activa")
            return
        
        pedidos_pendientes = self.obtener_pedido_actual(repartidor)
        
        if pedidos_pendientes:
            self.send_message(
                chat_id,
                "⚠️ *Atención*\n\nAún tienes pedidos pendientes. ¿Estás seguro de que quieres finalizar la ruta?\n\n"
                "Si hay un problema, usa '🆘 Reportar Problema' en su lugar."
            )
        else:
            self.finalizar_ruta(chat_id)
    
    def handle_reportar_problema(self, chat_id: str):
        """Manejar reporte de problemas"""
        self.send_message(
            chat_id,
            "🆘 *Reportar Problema*\n\n"
            "Describe brevemente el problema que estás experimentando.\n"
            "Un administrador será notificado inmediatamente.\n\n"
            "Ejemplos:\n"
            "• Cliente no está en casa\n"
            "• Dirección incorrecta\n"
            "• Problema con el vehículo\n"
            "• No puedo encontrar la ubicación\n\n"
            "Escribe tu mensaje y será enviado al administrador:"
        )
        
        # Aquí podrías implementar un estado para capturar el siguiente mensaje
        # como el reporte del problema
    
    def mostrar_ayuda(self, chat_id: str):
        """Mostrar ayuda y comandos disponibles"""
        mensaje = """❓ *Ayuda - Sistema de Reparto*

🔧 *Comandos disponibles:*

📍 *Ubicación*
• Envía tu ubicación para recibir direcciones
• Se registra automáticamente tu posición

🚛 *Gestión de Ruta*
• Ver Ruta Actual - Estado y próximas paradas
• Completar Parada - Marcar entrega como realizada
• Finalizar Ruta - Terminar el día de trabajo

🆘 *Soporte*
• Reportar Problema - Notificar incidencias
• Ayuda - Este menú

📱 *Uso básico:*
1. Recibe tu ruta del administrador
2. Envía ubicación para comenzar
3. Sigue las direcciones de Google Maps
4. Marca cada parada como completada
5. Reporta cualquier problema

📞 *Contacto de emergencia:*
Teléfono: +52 55 1234-5678
Email: soporte@lavanderia.com

¡Que tengas un excelente día de trabajo! 🚛✨"""
        
        self.send_message(chat_id, mensaje)
    
    def run(self):
        """Ejecutar bot en modo polling"""
        print("🤖 Bot de Repartidores iniciado...")
        print(f"📱 Repartidores activos: {len(self.repartidores_activos)}")
        
        offset = 0
        
        while self.running:
            try:
                # Obtener updates
                url = f"{BASE_URL}/getUpdates"
                params = {'offset': offset, 'timeout': 5}
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if data.get('ok'):
                    updates = data.get('result', [])
                    
                    for update in updates:
                        offset = update['update_id'] + 1
                        self.procesar_mensaje(update)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 Deteniendo bot de repartidores...")
                self.running = False
            except Exception as e:
                print(f"❌ Error en bot: {e}")
                time.sleep(3)

# ===== FUNCIÓN PARA INTEGRAR CON EL SISTEMA ADMIN =====
def enviar_ruta_a_repartidor(chat_id: str, ruta_data: Dict) -> bool:
    """
    Función para ser llamada desde el sistema admin
    para asignar rutas a repartidores
    """
    try:
        bot = BotRepartidor()
        return bot.asignar_ruta_a_repartidor(chat_id, ruta_data)
    except Exception as e:
        print(f"❌ Error asignando ruta: {e}")
        return False

def obtener_repartidores_disponibles() -> List[Dict]:
    """
    Función para obtener lista de repartidores disponibles
    (para ser usada en el panel admin)
    """
    try:
        db = RepartidorDB()
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chat_id, nombre, activo, 
                   CASE WHEN ruta_activa IS NULL THEN 0 ELSE 1 END as tiene_ruta
            FROM repartidores 
            WHERE activo = 1
            ORDER BY nombre
        ''')
        
        repartidores = []
        for row in cursor.fetchall():
            repartidores.append({
                'chat_id': row[0],
                'nombre': row[1],
                'activo': bool(row[2]),
                'tiene_ruta': bool(row[3]),
                'disponible': bool(row[2]) and not bool(row[3])
            })
        
        conn.close()
        return repartidores
        
    except Exception as e:
        print(f"❌ Error obteniendo repartidores: {e}")
        return []

def obtener_estado_repartidor(chat_id: str) -> Optional[Dict]:
    """Obtener estado actual de un repartidor específico"""
    try:
        db = RepartidorDB()
        repartidor = db.obtener_repartidor(chat_id)
        
        if not repartidor:
            return None
        
        return {
            'nombre': repartidor.nombre,
            'activo': repartidor.activo,
            'tiene_ruta': repartidor.ruta_activa is not None,
            'ubicacion_actual': repartidor.ubicacion_actual,
            'parada_actual': repartidor.parada_actual,
            'pedidos_completados': len(repartidor.pedidos_completados),
            'inicio_ruta': repartidor.inicio_ruta.isoformat() if repartidor.inicio_ruta else None
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")
        return None

# ===== SCRIPT PRINCIPAL =====
if __name__ == "__main__":
    # Verificar configuración
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN no configurado en .env")
        exit(1)
    
    if not GOOGLE_MAPS_API_KEY:
        print("⚠️ Advertencia: GOOGLE_MAPS_API_KEY no configurado - funciones de mapas limitadas")
    
    # Inicializar y ejecutar bot
    bot = BotRepartidor()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")

# ===== EJEMPLO DE USO DESDE ADMIN =====
"""
# En tu admin_routes.py, puedes usar estas funciones:

from bot_repartidor_completo import (
    enviar_ruta_a_repartidor, 
    obtener_repartidores_disponibles,
    obtener_estado_repartidor
)

@admin_bp.route('/api/repartidores-disponibles')
def api_repartidores_disponibles():
    repartidores = obtener_repartidores_disponibles()
    return jsonify({
        'success': True,
        'repartidores': repartidores
    })

@admin_bp.route('/api/enviar-ruta-telegram', methods=['POST'])
def api_enviar_ruta_telegram():
    data = request.get_json()
    chat_id = data.get('repartidor_chat_id')
    ruta_data = data.get('ruta_data')
    
    if enviar_ruta_a_repartidor(chat_id, ruta_data):
        return jsonify({'success': True, 'mensaje': 'Ruta enviada exitosamente'})
    else:
        return jsonify({'success': False, 'error': 'Error enviando ruta'})
"""