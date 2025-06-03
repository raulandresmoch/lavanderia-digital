from .extensions import db
from datetime import datetime, timedelta

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    ubicacion = db.Column(db.String(200), nullable=False)
    coordenadas = db.Column(db.String(50))  # lat,lng para optimización de rutas
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

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
    direccion = db.Column(db.String(200), nullable=False)
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

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    tipo_prenda_id = db.Column(db.Integer, db.ForeignKey('tipo_prenda.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)  # número de piezas o kg
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relación
    tipo_prenda = db.relationship('TipoPrenda', backref='items')

# Tabla para configuración del sistema
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

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