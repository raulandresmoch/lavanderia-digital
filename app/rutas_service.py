# rutas_service.py
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import math

logger = logging.getLogger(__name__)

class TipoParada(Enum):
    RECOLECCION = "recoleccion"
    ENTREGA = "entrega"

class EstadoRuta(Enum):
    PENDIENTE = "pendiente"
    ASIGNADA = "asignada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"

@dataclass
class Parada:
    id: str
    pedido_id: int
    tipo: TipoParada
    cliente_nombre: str
    cliente_telefono: str
    direccion: str
    latitud: float
    longitud: float
    hora_estimada: str
    tiempo_estimado_parada: int  # minutos
    notas: str = ""
    completada: bool = False
    hora_completada: Optional[datetime] = None
    orden_en_ruta: int = 0

@dataclass
class Ruta:
    id: str
    repartidor_chat_id: str
    fecha: date
    estado: EstadoRuta
    paradas: List[Parada]
    distancia_total_km: float = 0.0
    tiempo_total_minutos: int = 0
    hora_inicio_estimada: str = "09:00"
    hora_fin_estimada: str = "18:00"
    hora_inicio_real: Optional[datetime] = None
    hora_fin_real: Optional[datetime] = None
    url_mapa: str = ""
    instrucciones_ia: str = ""
    creada_en: datetime = None
    
    def __post_init__(self):
        if self.creada_en is None:
            self.creada_en = datetime.now()

class RutasService:
    def __init__(self, db_session, telegram_service, email_service):
        self.db = db_session
        self.telegram = telegram_service
        self.email = email_service
        self.rutas_activas = {}  # Cache de rutas en memoria
    
    async def generar_rutas_del_dia(self, fecha: date = None) -> List[Ruta]:
        """Generar rutas optimizadas para el día especificado"""
        if fecha is None:
            fecha = date.today()
        
        try:
            # 1. Obtener pedidos pendientes para la fecha
            pedidos_recoleccion = await self.obtener_pedidos_recoleccion(fecha)
            pedidos_entrega = await self.obtener_pedidos_entrega(fecha)
            
            logger.info(f"Generando rutas para {fecha}: {len(pedidos_recoleccion)} recolecciones, {len(pedidos_entrega)} entregas")
            
            # 2. Convertir pedidos a paradas
            paradas_recoleccion = [self.pedido_a_parada(p, TipoParada.RECOLECCION) for p in pedidos_recoleccion]
            paradas_entrega = [self.pedido_a_parada(p, TipoParada.ENTREGA) for p in pedidos_entrega]
            
            # 3. Agrupar paradas por zona geográfica
            grupos_paradas = await self.agrupar_paradas_por_zona(paradas_recoleccion + paradas_entrega)
            
            # 4. Generar rutas para cada grupo
            rutas_generadas = []
            for i, grupo in enumerate(grupos_paradas):
                ruta_id = f"RUTA_{fecha.strftime('%Y%m%d')}_{i+1:02d}"
                
                # Optimizar orden de paradas con IA
                paradas_optimizadas = await self.optimizar_paradas_con_ia(grupo)
                
                ruta = Ruta(
                    id=ruta_id,
                    repartidor_chat_id="",  # Se asignará después
                    fecha=fecha,
                    estado=EstadoRuta.PENDIENTE,
                    paradas=paradas_optimizadas
                )
                
                # Calcular métricas de la ruta
                await self.calcular_metricas_ruta(ruta)
                
                rutas_generadas.append(ruta)
            
            # 5. Guardar rutas en base de datos
            for ruta in rutas_generadas:
                await self.guardar_ruta(ruta)
            
            logger.info(f"Generadas {len(rutas_generadas)} rutas para {fecha}")
            return rutas_generadas
            
        except Exception as e:
            logger.error(f"Error generando rutas del día: {e}")
            return []
    
    def pedido_a_parada(self, pedido: Dict, tipo: TipoParada) -> Parada:
        """Convertir pedido a parada"""
        return Parada(
            id=f"{tipo.value}_{pedido['id']}",
            pedido_id=pedido['id'],
            tipo=tipo,
            cliente_nombre=pedido['usuario_nombre'],
            cliente_telefono=pedido.get('usuario_telefono', ''),
            direccion=pedido['direccion'],
            latitud=pedido['latitud'],
            longitud=pedido['longitud'],
            hora_estimada="",  # Se calculará después
            tiempo_estimado_parada=5 if tipo == TipoParada.RECOLECCION else 3,
            notas=pedido.get('notas', '')
        )
    
    async def agrupar_paradas_por_zona(self, paradas: List[Parada]) -> List[List[Parada]]:
        """Agrupar paradas por proximidad geográfica"""
        if not paradas:
            return []
        
        # Configuración
        MAX_PARADAS_POR_RUTA = 12
        RADIO_ZONA_KM = 8.0
        
        grupos = []
        paradas_sin_asignar = paradas.copy()
        
        while paradas_sin_asignar:
            # Tomar la primera parada como centro del grupo
            parada_centro = paradas_sin_asignar.pop(0)
            grupo_actual = [parada_centro]
            
            # Buscar paradas cercanas
            paradas_restantes = []
            for parada in paradas_sin_asignar:
                distancia = self.calcular_distancia(
                    parada_centro.latitud, parada_centro.longitud,
                    parada.latitud, parada.longitud
                )
                
                if distancia <= RADIO_ZONA_KM and len(grupo_actual) < MAX_PARADAS_POR_RUTA:
                    grupo_actual.append(parada)
                else:
                    paradas_restantes.append(parada)
            
            paradas_sin_asignar = paradas_restantes
            grupos.append(grupo_actual)
        
        return grupos
    
    def calcular_distancia(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcular distancia entre dos puntos en km"""
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    async def optimizar_paradas_con_ia(self, paradas: List[Parada]) -> List[Parada]:
        """Optimizar orden de paradas usando ChatGPT"""
        try:
            # Preparar datos para la IA
            paradas_data = []
            for parada in paradas:
                paradas_data.append({
                    'id': parada.id,
                    'tipo': parada.tipo.value,
                    'direccion': parada.direccion,
                    'lat': parada.latitud,
                    'lng': parada.longitud,
                    'cliente': parada.cliente_nombre,
                    'tiempo_parada': parada.tiempo_estimado_parada
                })
            
            # Llamar al servicio de Telegram que tiene la integración con OpenAI
            ruta_optimizada = await self.telegram.optimizar_ruta_con_ia(paradas_data)
            
            # Reorganizar paradas según el orden optimizado
            paradas_ordenadas = []
            for i, orden_parada in enumerate(ruta_optimizada.orden_paradas):
                parada_original = next(p for p in paradas if p.id == orden_parada.get('pedido_id') or f"{p.tipo.value}_{p.pedido_id}" == orden_parada.get('pedido_id'))
                parada_original.orden_en_ruta = i + 1
                parada_original.hora_estimada = orden_parada.get('hora_estimada', '09:00')
                paradas_ordenadas.append(parada_original)
            
            return paradas_ordenadas
            
        except Exception as e:
            logger.error(f"Error optimizando con IA: {e}")
            # Fallback: ordenar por tipo (recolecciones primero) y luego por proximidad
            return self.optimizar_paradas_basico(paradas)
    
    def optimizar_paradas_basico(self, paradas: List[Parada]) -> List[Parada]:
        """Optimización básica sin IA"""
        # Separar recolecciones y entregas
        recolecciones = [p for p in paradas if p.tipo == TipoParada.RECOLECCION]
        entregas = [p for p in paradas if p.tipo == TipoParada.ENTREGA]
        
        # Ordenar por proximidad geográfica (algoritmo del vecino más cercano)
        def ordenar_por_proximidad(paradas_lista):
            if not paradas_lista:
                return []
            
            resultado = [paradas_lista[0]]
            restantes = paradas_lista[1:]
            
            while restantes:
                ultima = resultado[-1]
                mas_cercana = min(restantes, key=lambda p: self.calcular_distancia(
                    ultima.latitud, ultima.longitud, p.latitud, p.longitud
                ))
                resultado.append(mas_cercana)
                restantes.remove(mas_cercana)
            
            return resultado
        
        recolecciones_ordenadas = ordenar_por_proximidad(recolecciones)
        entregas_ordenadas = ordenar_por_proximidad(entregas)
        
        # Asignar horarios
        hora_actual = 9  # 9:00 AM
        todas_paradas = []
        
        # Primero recolecciones (9:00-12:00)
        for i, parada in enumerate(recolecciones_ordenadas):
            parada.orden_en_ruta = i + 1
            parada.hora_estimada = f"{hora_actual:02d}:{(i*20)%60:02d}"
            if (i*20) >= 60:
                hora_actual += 1
            todas_paradas.append(parada)
        
        # Pausa para almuerzo/traslado
        hora_actual = 14  # 2:00 PM
        
        # Luego entregas (14:00-18:00)
        for i, parada in enumerate(entregas_ordenadas):
            parada.orden_en_ruta = len(recolecciones_ordenadas) + i + 1
            parada.hora_estimada = f"{hora_actual:02d}:{(i*15)%60:02d}"
            if (i*15) >= 60:
                hora_actual += 1
            todas_paradas.append(parada)
        
        return todas_paradas
    
    async def calcular_metricas_ruta(self, ruta: Ruta):
        """Calcular métricas de distancia y tiempo de la ruta"""
        if not ruta.paradas:
            return
        
        # Punto de inicio (base de operaciones)
        BASE_LAT, BASE_LNG = 19.4326, -99.1332
        
        distancia_total = 0.0
        tiempo_total = 0
        
        # Distancia desde base a primera parada
        primera_parada = ruta.paradas[0]
        distancia_total += self.calcular_distancia(
            BASE_LAT, BASE_LNG,
            primera_parada.latitud, primera_parada.longitud
        )
        
        # Distancias entre paradas consecutivas
        for i in range(len(ruta.paradas) - 1):
            parada_actual = ruta.paradas[i]
            parada_siguiente = ruta.paradas[i + 1]
            
            distancia = self.calcular_distancia(
                parada_actual.latitud, parada_actual.longitud,
                parada_siguiente.latitud, parada_siguiente.longitud
            )
            distancia_total += distancia
            
            # Tiempo de viaje (asumiendo 25 km/h promedio en CDMX)
            tiempo_viaje = (distancia / 25) * 60  # minutos
            tiempo_total += tiempo_viaje + parada_actual.tiempo_estimado_parada
        
        # Distancia de última parada a base
        ultima_parada = ruta.paradas[-1]
        distancia_total += self.calcular_distancia(
            ultima_parada.latitud, ultima_parada.longitud,
            BASE_LAT, BASE_LNG
        )
        
        # Tiempo de la última parada
        tiempo_total += ultima_parada.tiempo_estimado_parada
        
        # Actualizar métricas
        ruta.distancia_total_km = round(distancia_total, 2)
        ruta.tiempo_total_minutos = int(tiempo_total)
        
        # Generar URL del mapa
        ruta.url_mapa = self.generar_url_mapa_ruta(ruta.paradas)
    
    def generar_url_mapa_ruta(self, paradas: List[Parada]) -> str:
        """Generar URL de Google Maps con la ruta completa"""
        if not paradas:
            return ""
        
        # Base de operaciones
        origen = "19.4326,-99.1332"
        
        # Waypoints (todas las paradas excepto la última)
        waypoints = []
        for parada in paradas[:-1]:
            waypoints.append(f"{parada.latitud},{parada.longitud}")
        
        # Destino (última parada)
        destino = f"{paradas[-1].latitud},{paradas[-1].longitud}"
        
        # Construir URL
        base_url = "https://www.google.com/maps/dir/"
        url = f"{base_url}{origen}/"
        
        if waypoints:
            url += "/".join(waypoints) + "/"
        
        url += destino
        
        return url
    
    def generar_instrucciones_ruta(self, ruta: Ruta) -> str:
        """Generar instrucciones detalladas para el repartidor"""
        instrucciones = f"""🗺️ *RUTA {ruta.id}*

📊 *Resumen:*
• 📍 Paradas: {len(ruta.paradas)}
• 🛣️ Distancia: {ruta.distancia_total_km} km
• ⏱️ Tiempo: {ruta.tiempo_total_minutos} min
• 📅 Fecha: {ruta.fecha.strftime('%d/%m/%Y')}

📋 *PARADAS EN ORDEN:*
"""
        
        for parada in ruta.paradas:
            emoji = "📦" if parada.tipo == TipoParada.RECOLECCION else "🏠"
            tipo_texto = "Recolección" if parada.tipo == TipoParada.RECOLECCION else "Entrega"
            
            instrucciones += f"""
{emoji} *Parada #{parada.orden_en_ruta}* - {parada.hora_estimada}
📍 {parada.direccion}
👤 {parada.cliente_nombre}
📱 {parada.cliente_telefono}
🔹 {tipo_texto} - Pedido #{parada.pedido_id}
⏱️ {parada.tiempo_estimado_parada} min estimados
"""
            if parada.notas:
                instrucciones += f"💡 {parada.notas}\n"
        
        instrucciones += "\n🎯 *INSTRUCCIONES:*\n"
        instrucciones += "• Confirma cada recogida/entrega en este chat\n"
        instrucciones += "• Mantén contacto con clientes si hay retrasos\n"
        instrucciones += "• Notifica cualquier problema inmediatamente\n"
        
        return instrucciones
    
    async def iniciar_ruta(self, ruta_id: str, repartidor_chat_id: str) -> bool:
        """Marcar inicio de ruta"""
        try:
            ruta = await self.obtener_ruta(ruta_id)
            if not ruta or ruta.repartidor_chat_id != repartidor_chat_id:
                return False
            
            ruta.estado = EstadoRuta.EN_CURSO
            ruta.hora_inicio_real = datetime.now()
            
            await self.guardar_ruta(ruta)
            
            # Notificar a admins
            await self.telegram.notificar_admins(
                f"🚀 Ruta {ruta_id} iniciada por repartidor {repartidor_chat_id} a las {ruta.hora_inicio_real.strftime('%H:%M')}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando ruta: {e}")
            return False
    
    async def asignar_ruta_repartidor(self, ruta_id: str, repartidor_chat_id: str) -> bool:
        """Asignar ruta a un repartidor específico"""
        try:
            ruta = await self.obtener_ruta(ruta_id)
            if not ruta:
                return False
            
            ruta.repartidor_chat_id = repartidor_chat_id
            ruta.estado = EstadoRuta.ASIGNADA
            
            await self.guardar_ruta(ruta)
            
            # Enviar ruta al repartidor por Telegram
            await self.telegram.enviar_ruta_repartidor(
                chat_id=repartidor_chat_id,
                ruta=self.telegram.RutaOptimizada(
                    orden_paradas=[asdict(p) for p in ruta.paradas],
                    distancia_total=ruta.distancia_total_km,
                    tiempo_estimado=ruta.tiempo_total_minutos,
                    instrucciones=self.generar_instrucciones_ruta(ruta),
                    mapa_url=ruta.url_mapa
                ),
                ruta_id=ruta_id
            )
            
            # Notificar a admins
            await self.telegram.notificar_admins(
                f"✅ Ruta {ruta_id} asignada a repartidor {repartidor_chat_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error asignando ruta: {e}")
            return False
    
    async def confirmar_parada(self, ruta_id: str, parada_id: str, repartidor_chat_id: str) -> bool:
        """Confirmar completación de una parada"""
        try:
            ruta = await self.obtener_ruta(ruta_id)
            if not ruta or ruta.repartidor_chat_id != repartidor_chat_id:
                return False
            
            # Buscar la parada
            parada = next((p for p in ruta.paradas if p.id == parada_id), None)
            if not parada:
                return False
            
            # Marcar como completada
            parada.completada = True
            parada.hora_completada = datetime.now()
            
            await self.guardar_ruta(ruta)
            
            # Actualizar estado del pedido en base de datos
            nuevo_estado = "recolectado" if parada.tipo == TipoParada.RECOLECCION else "entregado"
            await self.actualizar_estado_pedido(parada.pedido_id, nuevo_estado)
            
            # Notificar progreso
            paradas_completadas = sum(1 for p in ruta.paradas if p.completada)
            total_paradas = len(ruta.paradas)
            progreso = (paradas_completadas / total_paradas) * 100
            
            await self.telegram.notificar_admins(
                f"✅ Parada completada en ruta {ruta_id}\n"
                f"📍 {parada.direccion}\n"
                f"👤 {parada.cliente_nombre}\n"
                f"📊 Progreso: {paradas_completadas}/{total_paradas} ({progreso:.1f}%)"
            )
            
            # Enviar email al cliente
            await self.enviar_notificacion_cliente(parada.pedido_id, nuevo_estado)
            
            # Verificar si la ruta está completa
            if paradas_completadas == total_paradas:
                await self.finalizar_ruta(ruta_id, repartidor_chat_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error confirmando parada: {e}")
            return False
    
    async def finalizar_ruta(self, ruta_id: str, repartidor_chat_id: str) -> bool:
        """Finalizar ruta completa"""
        try:
            ruta = await self.obtener_ruta(ruta_id)
            if not ruta or ruta.repartidor_chat_id != repartidor_chat_id:
                return False
            
            ruta.estado = EstadoRuta.COMPLETADA
            ruta.hora_fin_real = datetime.now()
            
            await self.guardar_ruta(ruta)
            
            # Calcular estadísticas
            tiempo_real = ruta.hora_fin_real - ruta.hora_inicio_real
            paradas_completadas = sum(1 for p in ruta.paradas if p.completada)
            
            # Notificar finalización
            await self.telegram.notificar_admins(
                f"🏁 Ruta {ruta_id} COMPLETADA\n"
                f"⏱️ Tiempo total: {tiempo_real}\n"
                f"📦 Paradas: {paradas_completadas}/{len(ruta.paradas)}\n"
                f"🛣️ Distancia: {ruta.distancia_total_km} km\n"
                f"👤 Repartidor: {repartidor_chat_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error finalizando ruta: {e}")
            return False
    
    async def obtener_rutas_del_dia(self, fecha: date = None) -> List[Ruta]:
        """Obtener todas las rutas de un día específico"""
        if fecha is None:
            fecha = date.today()
        
        try:
            # Buscar en cache primero
            rutas_fecha = []
            for ruta_id, ruta in self.rutas_activas.items():
                if ruta.fecha == fecha:
                    rutas_fecha.append(ruta)
            
            return rutas_fecha
            
        except Exception as e:
            logger.error(f"Error obteniendo rutas del día: {e}")
            return []
    
    async def obtener_estadisticas_rutas(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Obtener estadísticas de rutas en un rango de fechas"""
        try:
            # Filtrar rutas por rango de fechas
            rutas_periodo = []
            for ruta in self.rutas_activas.values():
                if fecha_inicio <= ruta.fecha <= fecha_fin:
                    rutas_periodo.append(ruta)
            
            estadisticas = {
                'total_rutas': len(rutas_periodo),
                'rutas_completadas': len([r for r in rutas_periodo if r.estado == EstadoRuta.COMPLETADA]),
                'rutas_en_progreso': len([r for r in rutas_periodo if r.estado == EstadoRuta.EN_CURSO]),
                'total_paradas': sum(len(r.paradas) for r in rutas_periodo),
                'paradas_completadas': sum(sum(1 for p in r.paradas if p.completada) for r in rutas_periodo),
                'distancia_total_km': sum(r.distancia_total_km for r in rutas_periodo),
                'tiempo_promedio_minutos': sum(r.tiempo_total_minutos for r in rutas_periodo) / len(rutas_periodo) if rutas_periodo else 0,
                'repartidores_activos': len(set(r.repartidor_chat_id for r in rutas_periodo if r.repartidor_chat_id))
            }
            
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    # Métodos auxiliares para conectar con la base de datos
    async def obtener_pedidos_recoleccion(self, fecha: date) -> List[Dict]:
        """Obtener pedidos pendientes de recolección para una fecha"""
        try:
            from models import Pedido, Usuario, DireccionUsuario
            
            # Ajustar consulta a tu modelo actual
            query = self.db.query(Pedido, Usuario, DireccionUsuario).join(
                Usuario, Pedido.usuario_id == Usuario.id
            ).join(
                DireccionUsuario, Pedido.direccion_id == DireccionUsuario.id
            ).filter(
                Pedido.fecha_recoleccion >= datetime.combine(fecha, datetime.min.time()),
                Pedido.fecha_recoleccion < datetime.combine(fecha + timedelta(days=1), datetime.min.time()),
                Pedido.estado.in_(['confirmado', 'en_proceso'])
            )
            
            pedidos = query.all()
            
            resultado = []
            for pedido, usuario, direccion in pedidos:
                resultado.append({
                    'id': pedido.id,
                    'usuario_nombre': usuario.nombre,
                    'usuario_telefono': usuario.telefono,
                    'direccion': direccion.direccion_completa,
                    'latitud': direccion.latitud,
                    'longitud': direccion.longitud,
                    'notas': pedido.notas or '',
                    'precio_total': float(pedido.total)
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo pedidos de recolección: {e}")
            return []
    
    async def obtener_pedidos_entrega(self, fecha: date) -> List[Dict]:
        """Obtener pedidos pendientes de entrega para una fecha"""
        try:
            from models import Pedido, Usuario, DireccionUsuario
            
            # Para entregas, buscar pedidos que estén listos para entregar
            query = self.db.query(Pedido, Usuario, DireccionUsuario).join(
                Usuario, Pedido.usuario_id == Usuario.id
            ).join(
                DireccionUsuario, Pedido.direccion_id == DireccionUsuario.id
            ).filter(
                # Pedidos que están listos para entrega en esta fecha
                Pedido.estado == 'listo_entrega'
                # Podrías agregar filtro de fecha_entrega si lo tienes
            )
            
            pedidos = query.all()
            
            resultado = []
            for pedido, usuario, direccion in pedidos:
                resultado.append({
                    'id': pedido.id,
                    'usuario_nombre': usuario.nombre,
                    'usuario_telefono': usuario.telefono,
                    'direccion': direccion.direccion_completa,
                    'latitud': direccion.latitud,
                    'longitud': direccion.longitud,
                    'notas': pedido.notas or '',
                    'precio_total': float(pedido.total)
                })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error obteniendo pedidos de entrega: {e}")
            return []
    
    async def guardar_ruta(self, ruta: Ruta) -> bool:
        """Guardar ruta en base de datos y cache"""
        try:
            # Guardar en cache local
            self.rutas_activas[ruta.id] = ruta
            
            # En una implementación completa, también guardarías en base de datos
            # Para esto necesitarías crear un modelo Ruta en tu models.py
            
            logger.info(f"Ruta {ruta.id} guardada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando ruta: {e}")
            return False
    
    async def obtener_ruta(self, ruta_id: str) -> Optional[Ruta]:
        """Obtener ruta por ID"""
        try:
            return self.rutas_activas.get(ruta_id)
            
        except Exception as e:
            logger.error(f"Error obteniendo ruta: {e}")
            return None
    
    async def actualizar_estado_pedido(self, pedido_id: int, nuevo_estado: str) -> bool:
        """Actualizar estado de un pedido"""
        try:
            from models import Pedido
            
            pedido = self.db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if pedido:
                pedido.estado = nuevo_estado
                
                # Actualizar timestamps según el estado
                if nuevo_estado == 'recolectado':
                    pedido.fecha_recoleccion_real = datetime.now()
                elif nuevo_estado == 'en_lavanderia':
                    pedido.fecha_en_lavanderia = datetime.now()
                elif nuevo_estado == 'listo_entrega':
                    pedido.fecha_listo = datetime.now()
                elif nuevo_estado == 'entregado':
                    pedido.fecha_entrega_real = datetime.now()
                
                self.db.commit()
                logger.info(f"Pedido {pedido_id} actualizado a estado: {nuevo_estado}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando estado de pedido: {e}")
            self.db.rollback()
            return False
    
    async def enviar_notificacion_cliente(self, pedido_id: int, nuevo_estado: str) -> bool:
        """Enviar notificación al cliente sobre cambio de estado"""
        try:
            from models import Pedido, Usuario, DireccionUsuario
            
            result = self.db.query(Pedido, Usuario, DireccionUsuario).join(
                Usuario, Pedido.usuario_id == Usuario.id
            ).join(
                DireccionUsuario, Pedido.direccion_id == DireccionUsuario.id
            ).filter(Pedido.id == pedido_id).first()
            
            if not result:
                return False
            
            pedido, usuario, direccion = result
            
            # Convertir objetos a diccionarios para el servicio de email
            pedido_dict = {
                'id': pedido.id,
                'fecha_recoleccion': pedido.fecha_recoleccion.strftime('%d/%m/%Y'),
                'direccion': direccion.direccion_completa,
                'total': float(pedido.total),
                'notas': pedido.notas or ''
            }
            
            usuario_dict = {
                'nombre': usuario.nombre,
                'email': usuario.email
            }
            
            # Enviar email usando el servicio de email
            await self.email.enviar_actualizacion_estado(usuario_dict, pedido_dict, nuevo_estado)
            
            logger.info(f"Notificación enviada a {usuario.email} para pedido {pedido_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación a cliente: {e}")
            return False

# Instancia global del servicio
rutas_service = None

def inicializar_rutas_service(db_session, telegram_service, email_service):
    """Inicializar el servicio de rutas con las dependencias"""
    global rutas_service
    rutas_service = RutasService(db_session, telegram_service, email_service)
    return rutas_service