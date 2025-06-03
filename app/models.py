from .extensions import db
from datetime import datetime, timedelta

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    
    # Mantenemos ubicacion por compatibilidad, pero ahora usaremos DireccionUsuario
    ubicacion = db.Column(db.String(200))
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    coordenadas_verificadas = db.Column(db.Boolean, default=False)
    
    # Relaciones
    direcciones = db.relationship('DireccionUsuario', backref='usuario', lazy=True, cascade='all, delete-orphan')
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def direccion_principal(self):
        """Retorna la dirección marcada como principal"""
        return DireccionUsuario.query.filter_by(
            usuario_id=self.id, 
            es_principal=True, 
            activa=True
        ).first()
    
    @property
    def direcciones_activas(self):
        """Retorna todas las direcciones activas del usuario"""
        return DireccionUsuario.query.filter_by(
            usuario_id=self.id, 
            activa=True
        ).order_by(DireccionUsuario.es_principal.desc(), DireccionUsuario.nombre).all()

class DireccionUsuario(db.Model):
    """Modelo para manejar múltiples direcciones por usuario"""
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Información de la dirección
    nombre = db.Column(db.String(50), nullable=False)  # "Casa", "Trabajo", "Casa de mamá", etc.
    direccion = db.Column(db.String(300), nullable=False)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    
    # Metadatos
    es_principal = db.Column(db.Boolean, default=False)
    activa = db.Column(db.Boolean, default=True)
    verificada = db.Column(db.Boolean, default=True)
    
    # Información adicional
    notas = db.Column(db.Text)  # Referencias, instrucciones especiales
    zona_cobertura = db.Column(db.String(50))
    
    # Timestamps
    creada = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con pedidos
    pedidos = db.relationship('Pedido', backref='direccion_usuario', lazy=True)
    
    @property
    def coordenadas_json(self):
        """Retorna coordenadas en formato JSON para JavaScript"""
        return {'lat': self.latitud, 'lng': self.longitud}
    
    @property
    def en_zona_cobertura(self):
        """Verifica si está en zona de cobertura"""
        from app.geocoding_service import geocoding
        return geocoding._esta_en_zona_cobertura(self.latitud, self.longitud)
    
    def __repr__(self):
        return f'<DireccionUsuario {self.nombre}: {self.direccion[:50]}...>'

class TipoPrenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)  # ej: "Ropa normal", "Edredones", "Ropa delicada"
    precio_por_kg = db.Column(db.Float, nullable=False)
    tiempo_lavado_horas = db.Column(db.Integer, nullable=False)  # tiempo en horas
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Referencia a la dirección utilizada (opcional, para mantener historial)
    direccion_usuario_id = db.Column(db.Integer, db.ForeignKey('direccion_usuario.id'))
    
    # Información de dirección (snapshot del momento del pedido)
    direccion = db.Column(db.String(300), nullable=False)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    direccion_verificada = db.Column(db.Boolean, default=False)
    
    fecha_recoleccion = db.Column(db.Date, nullable=False)
    fecha_entrega = db.Column(db.Date, nullable=False)
    hora_recoleccion = db.Column(db.String(20), default="Mañana (9:00-12:00)")
    hora_entrega = db.Column(db.String(20), default="Tarde (14:00-18:00)")
    
    # Detalles del pedido
    peso_estimado = db.Column(db.Float)  # kg estimados
    precio_total = db.Column(db.Float, nullable=False)
    notas = db.Column(db.Text)
    
    # Estados del pedido
    estado = db.Column(db.String(20), default="Solicitado")  # Solicitado, Recolectado, EnProceso, Listo, Entregado
    pagado = db.Column(db.Boolean, default=False)
    
    # Timestamps
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con items del pedido
    items = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade='all, delete-orphan')
    
    @property
    def coordenadas_json(self):
        """Retorna coordenadas en formato JSON para JavaScript"""
        if self.latitud and self.longitud:
            return {'lat': self.latitud, 'lng': self.longitud}
        return None
    
    @property
    def distancia_desde_base(self):
        """Calcula distancia desde base de operaciones"""
        # Coordenadas base (Ciudad de México centro como ejemplo)
        base_lat, base_lng = 19.4326, -99.1332
        if self.latitud and self.longitud:
            # Fórmula haversine simplificada
            import math
            dlat = math.radians(self.latitud - base_lat)
            dlng = math.radians(self.longitud - base_lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(base_lat)) * math.cos(math.radians(self.latitud)) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return 6371 * c  # Radio de la Tierra en km
        return None

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    tipo_prenda_id = db.Column(db.Integer, db.ForeignKey('tipo_prenda.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)  # número de piezas o kg
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relación
    tipo_prenda = db.relationship('TipoPrenda', backref='items')

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

# Tabla para configuración del sistema
class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    
    @staticmethod
    def get_valor(clave, default=None):
        config = Configuracion.query.filter_by(clave=clave).first()
        return config.valor if config else default
    
    @staticmethod
    def set_valor(clave, valor, descripcion=None):
        config = Configuracion.query.filter_by(clave=clave).first()
        if config:
            config.valor = valor
            if descripcion:
                config.descripcion = descripcion
        else:
            config = Configuracion(clave=clave, valor=valor, descripcion=descripcion)
            db.session.add(config)
        db.session.commit()

# Funciones auxiliares para estadísticas
class EstadisticasPedidos:
    @staticmethod
    def pedidos_hoy():
        hoy = datetime.now().date()
        return Pedido.query.filter(Pedido.fecha_recoleccion == hoy).count()
    
    @staticmethod
    def pedidos_por_estado():
        from sqlalchemy import func
        return db.session.query(
            Pedido.estado, 
            func.count(Pedido.id).label('cantidad')
        ).group_by(Pedido.estado).all()
    
    @staticmethod
    def ingresos_mes_actual():
        from sqlalchemy import func, extract
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        
        result = db.session.query(
            func.sum(Pedido.precio_total).label('total')
        ).filter(
            extract('month', Pedido.creado) == mes_actual,
            extract('year', Pedido.creado) == año_actual,
            Pedido.estado != 'Cancelado'
        ).first()
        
        return result.total if result.total else 0
    
    @staticmethod
    def pedidos_por_zona():
        from sqlalchemy import func
        return db.session.query(
            func.substr(Pedido.direccion, 1, 20).label('zona'),
            func.count(Pedido.id).label('cantidad')
        ).group_by('zona').limit(10).all()