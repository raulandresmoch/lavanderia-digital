"""
Servicio de geocodificación usando APIs gratuitas
"""

import requests
import time
from typing import Dict, List, Optional, Tuple

class GeocodingService:
    """Servicio para geocodificación usando Nominatim (OpenStreetMap)"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.headers = {
            'User-Agent': 'Lavanderia-Digital/1.0 (contacto@lavanderia-digital.com)'
        }
        # Zona de cobertura de Ciudad de México (aproximada)
        self.zona_cobertura = {
            'centro': {'lat': 19.4326, 'lng': -99.1332},
            'radio_km': 25,  # 25km de radio desde el centro
            'limites': {
                'norte': 19.6,
                'sur': 19.2,
                'este': -98.9,
                'oeste': -99.4
            }
        }
    
    def geocodificar_direccion(self, direccion: str, ciudad: str = "Ciudad de México") -> Optional[Dict]:
        """
        Convierte una dirección en coordenadas lat/lng
        
        Args:
            direccion: Dirección a geocodificar
            ciudad: Ciudad (por defecto Ciudad de México)
            
        Returns:
            Dict con lat, lng, direccion_completa, en_zona_cobertura
        """
        try:
            # Construir consulta completa
            query = f"{direccion}, {ciudad}, México"
            
            params = {
                'q': query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1,
                'countrycodes': 'mx'  # Solo México
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    result = results[0]
                    lat = float(result['lat'])
                    lng = float(result['lon'])
                    
                    return {
                        'latitud': lat,
                        'longitud': lng,
                        'direccion_completa': result.get('display_name', direccion),
                        'en_zona_cobertura': self._esta_en_zona_cobertura(lat, lng),
                        'confianza': float(result.get('importance', 0.5)),
                        'tipo': result.get('type', 'unknown')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error en geocodificación: {e}")
            return None
    
    def geocodificacion_inversa(self, lat: float, lng: float) -> Optional[str]:
        """
        Convierte coordenadas en dirección legible
        
        Args:
            lat: Latitud
            lng: Longitud
            
        Returns:
            Dirección formateada
        """
        try:
            params = {
                'lat': lat,
                'lon': lng,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = requests.get(
                f"{self.base_url}/reverse",
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extraer componentes de dirección
                address = result.get('address', {})
                
                # Construir dirección mexicana típica
                componentes = []
                
                if 'house_number' in address and 'road' in address:
                    componentes.append(f"{address['road']} {address['house_number']}")
                elif 'road' in address:
                    componentes.append(address['road'])
                
                if 'neighbourhood' in address:
                    componentes.append(address['neighbourhood'])
                elif 'suburb' in address:
                    componentes.append(address['suburb'])
                
                if 'city_district' in address:
                    componentes.append(address['city_district'])
                
                return ', '.join(componentes) if componentes else result.get('display_name', '')
            
            return None
            
        except Exception as e:
            print(f"Error en geocodificación inversa: {e}")
            return None
    
    def _esta_en_zona_cobertura(self, lat: float, lng: float) -> bool:
        """
        Verifica si las coordenadas están dentro de la zona de cobertura
        
        Args:
            lat: Latitud
            lng: Longitud
            
        Returns:
            True si está en zona de cobertura
        """
        limites = self.zona_cobertura['limites']
        
        return (
            limites['sur'] <= lat <= limites['norte'] and
            limites['oeste'] <= lng <= limites['este']
        )
    
    def calcular_distancia(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calcula distancia entre dos puntos usando fórmula Haversine
        
        Returns:
            Distancia en kilómetros
        """
        import math
        
        # Convertir a radianes
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Diferencias
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        # Fórmula Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radio de la Tierra en km
        return 6371 * c
    
    def sugerir_direcciones(self, query: str, limite: int = 5) -> List[Dict]:
        """
        Sugiere direcciones basadas en una consulta parcial
        
        Args:
            query: Texto de búsqueda
            limite: Número máximo de sugerencias
            
        Returns:
            Lista de direcciones sugeridas
        """
        try:
            if len(query) < 3:
                return []
            
            params = {
                'q': f"{query}, Ciudad de México, México",
                'format': 'json',
                'limit': limite,
                'addressdetails': 1,
                'countrycodes': 'mx'
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                results = response.json()
                sugerencias = []
                
                for result in results:
                    lat = float(result['lat'])
                    lng = float(result['lon'])
                    
                    sugerencias.append({
                        'direccion': result.get('display_name', ''),
                        'direccion_corta': self._formatear_direccion_corta(result),
                        'latitud': lat,
                        'longitud': lng,
                        'en_zona': self._esta_en_zona_cobertura(lat, lng),
                        'tipo': result.get('type', 'address')
                    })
                
                return sugerencias
            
            return []
            
        except Exception as e:
            print(f"Error en sugerencias: {e}")
            return []
    
    def _formatear_direccion_corta(self, result: Dict) -> str:
        """Formatea una dirección en formato corto mexicano"""
        address = result.get('address', {})
        componentes = []
        
        # Calle y número
        if 'house_number' in address and 'road' in address:
            componentes.append(f"{address['road']} {address['house_number']}")
        elif 'road' in address:
            componentes.append(address['road'])
        
        # Colonia
        if 'neighbourhood' in address:
            componentes.append(address['neighbourhood'])
        elif 'suburb' in address:
            componentes.append(address['suburb'])
        
        return ', '.join(componentes[:2])  # Máximo 2 componentes

# Instancia global del servicio
geocoding = GeocodingService()