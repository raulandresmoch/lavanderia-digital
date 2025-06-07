# google_maps_utils.py - Utilidades para integración con Google Maps
import urllib.parse
from typing import List, Dict, Tuple

class GoogleMapsIntegration:
    """Clase para manejar integraciones con Google Maps"""
    
    @staticmethod
    def generar_url_direccion(latitud: float, longitud: float, nombre_destino: str = None) -> str:
        """Generar URL de Google Maps para una dirección específica"""
        if nombre_destino:
            # URL con nombre del destino
            query = urllib.parse.quote(f"{nombre_destino}")
            return f"https://www.google.com/maps/search/{query}/@{latitud},{longitud},17z"
        else:
            # URL con coordenadas directas
            return f"https://www.google.com/maps?q={latitud},{longitud}"
    
    @staticmethod
    def generar_url_navegacion(latitud_destino: float, longitud_destino: float, 
                              latitud_origen: float = None, longitud_origen: float = None) -> str:
        """Generar URL de navegación de Google Maps"""
        if latitud_origen and longitud_origen:
            # Navegación desde origen específico
            return (f"https://www.google.com/maps/dir/{latitud_origen},{longitud_origen}/"
                   f"{latitud_destino},{longitud_destino}")
        else:
            # Navegación desde ubicación actual
            return f"https://www.google.com/maps/dir/current+location/{latitud_destino},{longitud_destino}"
    
    @staticmethod
    def generar_ruta_completa(paradas: List[Dict]) -> str:
        """Generar URL para ruta completa con múltiples paradas"""
        if not paradas:
            return ""
        
        # Punto de inicio (primera parada)
        primera_parada = paradas[0]
        origen = f"{primera_parada['latitud']},{primera_parada['longitud']}"
        
        # Punto final (última parada)
        ultima_parada = paradas[-1]
        destino = f"{ultima_parada['latitud']},{ultima_parada['longitud']}"
        
        # Paradas intermedias (waypoints)
        waypoints = []
        for parada in paradas[1:-1]:  # Excluir primera y última
            waypoints.append(f"{parada['latitud']},{parada['longitud']}")
        
        # Construir URL
        url = f"https://www.google.com/maps/dir/{origen}/{destino}"
        
        if waypoints:
            waypoints_str = "/".join(waypoints)
            url = f"https://www.google.com/maps/dir/{origen}/{waypoints_str}/{destino}"
        
        return url
    
    @staticmethod
    def generar_mensaje_telegram_con_mapas(ruta_data: Dict, repartidor_nombre: str) -> str:
        """Generar mensaje de Telegram con enlaces de Google Maps"""
        
        tipo_ruta = ruta_data.get('tipo', 'recoleccion').upper()
        fecha = ruta_data.get('fecha', 'Hoy')
        rutas = ruta_data.get('rutas', {})
        total_pedidos = ruta_data.get('total_pedidos', 0)
        
        mensaje = f"""🚚 *NUEVA RUTA ASIGNADA*

👤 *Repartidor:* {repartidor_nombre}
📅 *Fecha:* {fecha}
🚛 *Tipo:* {tipo_ruta}
📦 *Total Pedidos:* {total_pedidos}

"""
        
        zona_numero = 1
        for zona, zona_data in rutas.items():
            pedidos = zona_data['pedidos']
            mensaje += f"""
🗺️ *ZONA {zona_numero}: {zona}*
📍 *Paradas:* {len(pedidos)}

"""
            
            for i, pedido in enumerate(pedidos, 1):
                lat = pedido.get('latitud', 0)
                lng = pedido.get('longitud', 0)
                cliente = pedido.get('cliente', 'Cliente')
                direccion = pedido.get('direccion', 'Dirección no disponible')
                telefono = pedido.get('telefono', 'No disponible')
                notas = pedido.get('notas', '')
                
                # URLs de Google Maps
                url_ubicacion = GoogleMapsIntegration.generar_url_direccion(lat, lng, f"{cliente} - Pedido #{pedido.get('id')}")
                url_navegacion = GoogleMapsIntegration.generar_url_navegacion(lat, lng)
                
                mensaje += f"""{i}. Pedido #{pedido.get('id', 'N/A')}
👤 {cliente}
📱 {telefono}
📍 {direccion[:60]}{'...' if len(direccion) > 60 else ''}
"""
                
                if notas:
                    mensaje += f"📝 {notas}\n"
                
                mensaje += f"""
🗺️ [Ver Ubicación]({url_ubicacion})
🧭 [Navegar Aquí]({url_navegacion})

"""
            
            # URL para ruta completa de la zona
            if len(pedidos) > 1:
                url_ruta_zona = GoogleMapsIntegration.generar_ruta_completa(pedidos)
                mensaje += f"🛣️ [Ruta Completa Zona {zona_numero}]({url_ruta_zona})\n\n"
            
            zona_numero += 1
        
        # Generar estimaciones de tiempo
        todos_pedidos = []
        for zona_data in ruta_data.get('rutas', {}).values():
            todos_pedidos.extend(zona_data['pedidos'])
        
        if len(todos_pedidos) > 1:
            url_ruta_completa = GoogleMapsIntegration.generar_ruta_completa(todos_pedidos)
            mensaje += f"🗺️ [RUTA COMPLETA DEL DÍA]({url_ruta_completa})\n\n"
        
        mensaje += f"""
*⚡ INSTRUCCIONES RÁPIDAS:*

1️⃣ Usa `/iniciar` para comenzar
2️⃣ Haz clic en "🧭 Navegar Aquí" para cada parada
3️⃣ Marca entregas con `✅ Entregado`
4️⃣ Reporta problemas con `/problema`
5️⃣ Finaliza con `/finalizar`

*📞 Coordinador:* {ruta_data.get('admin_chat_id', 'No disponible')}

🚀 ¡Que tengas un excelente día de trabajo!
"""
        
        return mensaje
    
    @staticmethod
    def generar_mensaje_parada_individual(pedido: Dict) -> str:
        """Generar mensaje para una parada individual"""
        lat = pedido.get('latitud', 0)
        lng = pedido.get('longitud', 0)
        cliente = pedido.get('cliente', 'Cliente')
        direccion = pedido.get('direccion', 'Dirección no disponible')
        telefono = pedido.get('telefono', 'No disponible')
        notas = pedido.get('notas', '')
        pedido_id = pedido.get('id', 'N/A')
        
        url_ubicacion = GoogleMapsIntegration.generar_url_direccion(lat, lng, f"{cliente} - Pedido #{pedido_id}")
        url_navegacion = GoogleMapsIntegration.generar_url_navegacion(lat, lng)
        
        mensaje = f"""📍 *PRÓXIMA PARADA*

📋 *Pedido #{pedido_id}*
👤 *Cliente:* {cliente}
📱 *Teléfono:* {telefono}
📍 *Dirección:* {direccion}
"""
        
        if notas:
            mensaje += f"📝 *Notas:* {notas}\n"
        
        mensaje += f"""
🗺️ [Ver Ubicación]({url_ubicacion})
🧭 [NAVEGAR AQUÍ]({url_navegacion})

*Acciones disponibles:*
• ✅ Marcar como entregado
• ⚠️ Reportar problema
• 📞 Llamar al cliente
"""
        
        return mensaje
    
    @staticmethod
    def generar_urls_optimizadas_por_zona(rutas_por_zona: Dict) -> Dict[str, str]:
        """Generar URLs optimizadas para cada zona"""
        urls_por_zona = {}
        
        for zona, pedidos in rutas_por_zona.items():
            if len(pedidos) > 1:
                urls_por_zona[zona] = GoogleMapsIntegration.generar_ruta_completa(pedidos)
            elif len(pedidos) == 1:
                pedido = pedidos[0]
                urls_por_zona[zona] = GoogleMapsIntegration.generar_url_navegacion(
                    pedido['latitud'], pedido['longitud']
                )
        
        return urls_por_zona
    
    @staticmethod
    def calcular_distancia_aproximada(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcular distancia aproximada entre dos puntos (en km)"""
        import math
        
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def generar_estimacion_tiempo(pedidos: List[Dict], tiempo_por_parada: int = 10) -> Dict:
        """Generar estimación de tiempo para completar la ruta"""
        if not pedidos:
            return {'tiempo_total': 0, 'distancia_total': 0, 'paradas': 0}
        
        distancia_total = 0
        tiempo_total = len(pedidos) * tiempo_por_parada  # Tiempo base por parada
        
        # Calcular distancia entre paradas consecutivas
        for i in range(len(pedidos) - 1):
            lat1 = pedidos[i]['latitud']
            lng1 = pedidos[i]['longitud']
            lat2 = pedidos[i + 1]['latitud']
            lng2 = pedidos[i + 1]['longitud']
            
            distancia = GoogleMapsIntegration.calcular_distancia_aproximada(lat1, lng1, lat2, lng2)
            distancia_total += distancia
        
        # Estimar tiempo de viaje (asumiendo 25 km/h promedio en CDMX)
        tiempo_viaje = (distancia_total / 25) * 60  # Convertir a minutos
        tiempo_total += tiempo_viaje
        
        return {
            'tiempo_total': round(tiempo_total),
            'distancia_total': round(distancia_total, 2),
            'paradas': len(pedidos),
            'tiempo_paradas': len(pedidos) * tiempo_por_parada,
            'tiempo_viaje': round(tiempo_viaje)
        }

# Función para uso desde el panel admin
def obtener_info_google_maps_para_admin(pedidos: List[Dict]) -> Dict:
    """Generar información de Google Maps para mostrar en el panel admin"""
    if not pedidos:
        return {}
    
    # URL de la ruta completa
    url_ruta_completa = GoogleMapsIntegration.generar_ruta_completa(pedidos)
    
    # URLs individuales
    urls_individuales = []
    for pedido in pedidos:
        url_ubicacion = GoogleMapsIntegration.generar_url_direccion(
            pedido['latitud'], pedido['longitud'], 
            f"Pedido #{pedido.get('id')} - {pedido.get('cliente')}"
        )
        url_navegacion = GoogleMapsIntegration.generar_url_navegacion(
            pedido['latitud'], pedido['longitud']
        )
        urls_individuales.append({
            'pedido_id': pedido.get('id'),
            'cliente': pedido.get('cliente'),
            'url_ubicacion': url_ubicacion,
            'url_navegacion': url_navegacion
        })
    
    # Estimaciones
    estimacion = GoogleMapsIntegration.generar_estimacion_tiempo(pedidos)
    
    return {
        'url_ruta_completa': url_ruta_completa,
        'urls_individuales': urls_individuales,
        'estimaciones': estimacion,
        'total_pedidos': len(pedidos)
    }