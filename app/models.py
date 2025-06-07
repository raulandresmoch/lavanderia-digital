# app/models.py - Modelos actualizados con sistema de repartidores
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import event
import json

class Usuario(db.Model):
    """Modelo de usuario cliente"""
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    
    # Campos de ubicación (por compatibilidad)
    ubicacion = db.Column(db.Text)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    coordenadas_verificadas = db.Column(db.Boolean, default=False)
    
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    direcciones = db.relationship('DireccionUsuario', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    @property
    def direccion_principal(self):
        """Obtener la dirección principal del usuario"""
        return DireccionUsuario.query.filter_by(
            usuario_id=self.id, 
            es_principal=True
        ).first()
    
    def verificar_contrasena(self, contrasena):
        return check_password_hash(self.contrasena, contrasena)
    
    def __repr__(self):
        return f'<Usuario {self.email}>'

class DireccionUsuario(db.Model):
    """Modelo para direcciones múltiples de usuarios"""
    __tablename__ = 'direccion_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    nombre = db.Column(db.String(100), nullable=False)  # Casa, Trabajo, etc.
    direccion = db.Column(db.Text, nullable=False)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    
    es_principal = db.Column(db.Boolean, default=False)
    verificada = db.Column(db.Boolean, default=False)
    en_zona_cobertura = db.Column(db.Boolean, default=True)
    
    notas = db.Column(db.Text)  # Referencias adicionales
    creada = db.Column(db.DateTime, default=datetime.utcnow)
    actualizada = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Direccion {self.nombre} - {self.usuario.nombre}>'

class Repartidor(db.Model):
    """Modelo para gestionar repartidores"""
    __tablename__ = 'repartidor'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Estado y disponibilidad
    estado = db.Column(db.String(20), default='disponible')  # disponible, en_ruta, ocupado, desconectado
    activo = db.Column(db.Boolean, default=True)
    verificado = db.Column(db.Boolean, default=False)
    
    # Información adicional
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_actividad = db.Column(db.DateTime, default=datetime.utcnow)
    ubicacion_actual_lat = db.Column(db.Float)
    ubicacion_actual_lng = db.Column(db.Float)
    ultima_ubicacion = db.Column(db.DateTime)
    
    # Estadísticas
    pedidos_completados = db.Column(db.Integer, default=0)
    calificacion_promedio = db.Column(db.Float, default=5.0)
    tiempo_promedio_entrega = db.Column(db.Integer)  # en minutos
    
    # Configuración
    notificaciones_activas = db.Column(db.Boolean, default=True)
    tracking_activo = db.Column(db.Boolean, default=False)
    
    # Relaciones
    rutas_asignadas = db.relationship('RutaAsignada', backref='repartidor', lazy=True)
    ubicaciones_historial = db.relationship('UbicacionRepartidor', backref='repartidor', lazy=True, cascade='all, delete-orphan')
    
    def actualizar_actividad(self):
        """Actualizar timestamp de última actividad"""
        self.ultima_actividad = datetime.utcnow()
        db.session.commit()
    
    def actualizar_ubicacion(self, latitud, longitud):
        """Actualizar ubicación actual del repartidor"""
        self.ubicacion_actual_lat = latitud
        self.ubicacion_actual_lng = longitud
        self.ultima_ubicacion = datetime.utcnow()
        
        # Guardar en historial si está en ruta
        if self.estado == 'en_ruta':
            ubicacion_historial = UbicacionRepartidor(
                repartidor_id=self.id,
                latitud=latitud,
                longitud=longitud,
                timestamp=datetime.utcnow()
            )
            db.session.add(ubicacion_historial)
        
        db.session.commit()
    
    def obtener_ruta_activa(self):
        """Obtener la ruta actualmente activa del repartidor"""
        return RutaAsignada.query.filter_by(
            repartidor_id=self.id,
            estado='activa'
        ).first()
    
    def __repr__(self):
        return f'<Repartidor {self.nombre} - {self.telegram_chat_id}>'

class RutaAsignada(db.Model):
    """Modelo para rutas asignadas a repartidores"""
    __tablename__ = 'ruta_asignada'
    
    id = db.Column(db.Integer, primary_key=True)
    repartidor_id = db.Column(db.Integer, db.ForeignKey('repartidor.id'), nullable=False)
    
    # Información de la ruta
    codigo_ruta = db.Column(db.String(100), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # recoleccion, entrega
    fecha_programada = db.Column(db.Date, nullable=False)
    
    # Estados: asignada, aceptada, en_progreso, completada, cancelada
    estado = db.Column(db.String(20), default='asignada')
    
    # Metadatos de la ruta
    total_pedidos = db.Column(db.Integer, default=0)
    pedidos_completados = db.Column(db.Integer, default=0)
    distancia_estimada = db.Column(db.Float)  # en km
    tiempo_estimado = db.Column(db.Integer)  # en minutos
    
    # Timestamps
    asignada_en = db.Column(db.DateTime, default=datetime.utcnow)
    iniciada_en = db.Column(db.DateTime)
    completada_en = db.Column(db.DateTime)
    
    # Datos de la ruta (JSON)
    datos_ruta = db.Column(db.Text)  # JSON con detalles de paradas
    observaciones = db.Column(db.Text)
    
    # Relaciones
    pedidos_ruta = db.relationship('PedidoRuta', backref='ruta_asignada', lazy=True, cascade='all, delete-orphan')
    reportes = db.relationship('ReporteIncidencia', backref='ruta', lazy=True)
    
    def obtener_datos_ruta(self):
        """Obtener datos de la ruta como diccionario"""
        if self.datos_ruta:
            return json.loads(self.datos_ruta)
        return {}
    
    def establecer_datos_ruta(self, datos):
        """Establecer datos de la ruta como JSON"""
        self.datos_ruta = json.dumps(datos, ensure_ascii=False)
    
    def calcular_progreso(self):
        """Calcular porcentaje de progreso"""
        if self.total_pedidos == 0:
            return 0
        return (self.pedidos_completados / self.total_pedidos) * 100
    
    def iniciar_ruta(self):
        """Marcar ruta como iniciada"""
        self.estado = 'en_progreso'
        self.iniciada_en = datetime.utcnow()
        self.repartidor.estado = 'en_ruta'
        db.session.commit()
    
    def completar_ruta(self):
        """Marcar ruta como completada"""
        self.estado = 'completada'
        self.completada_en = datetime.utcnow()
        self.repartidor.estado = 'disponible'
        self.pedidos_completados = self.total_pedidos
        db.session.commit()
    
    def __repr__(self):
        return f'<RutaAsignada {self.codigo_ruta} - {self.repartidor.nombre}>'

class PedidoRuta(db.Model):
    """Relación entre pedidos y rutas asignadas"""
    __tablename__ = 'pedido_ruta'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    ruta_asignada_id = db.Column(db.Integer, db.ForeignKey('ruta_asignada.id'), nullable=False)
    
    orden_en_ruta = db.Column(db.Integer, nullable=False)  # Orden de visita
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, completado, fallido
    
    hora_llegada = db.Column(db.DateTime)
    hora_completado = db.Column(db.DateTime)
    observaciones = db.Column(db.Text)
    
    # Relación con pedido
    pedido = db.relationship('Pedido', backref='rutas_asignadas')
    
    def marcar_completado(self):
        """Marcar pedido como completado en la ruta"""
        self.estado = 'completado'
        self.hora_completado = datetime.utcnow()
        
        # Actualizar contador en ruta
        self.ruta_asignada.pedidos_completados += 1
        
        # Actualizar estado del pedido principal
        if self.ruta_asignada.tipo == 'recoleccion':
            self.pedido.estado = 'Recolectado'
        elif self.ruta_asignada.tipo == 'entrega':
            self.pedido.estado = 'Entregado'
        
        db.session.commit()

class UbicacionRepartidor(db.Model):
    """Historial de ubicaciones de repartidores"""
    __tablename__ = 'ubicacion_repartidor'
    
    id = db.Column(db.Integer, primary_key=True)
    repartidor_id = db.Column(db.Integer, db.ForeignKey('repartidor.id'), nullable=False)
    
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contexto adicional
    en_ruta = db.Column(db.Boolean, default=False)
    velocidad = db.Column(db.Float)  # km/h si está disponible
    precision = db.Column(db.Float)  # precisión GPS en metros
    
    def __repr__(self):
        return f'<UbicacionRepartidor {self.repartidor.nombre} - {self.timestamp}>'

class ReporteIncidencia(db.Model):
    """Reportes de problemas o incidencias"""
    __tablename__ = 'reporte_incidencia'
    
    id = db.Column(db.Integer, primary_key=True)
    repartidor_id = db.Column(db.Integer, db.ForeignKey('repartidor.id'), nullable=False)
    ruta_id = db.Column(db.Integer, db.ForeignKey('ruta_asignada.id'), nullable=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=True)
    
    # Tipo de incidencia
    tipo = db.Column(db.String(50), nullable=False)  # vehiculo, pedido, cliente, ruta, sistema
    prioridad = db.Column(db.String(20), default='media')  # baja, media, alta, critica
    estado = db.Column(db.String(20), default='abierto')  # abierto, en_proceso, resuelto, cerrado
    
    # Contenido del reporte
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    ubicacion_lat = db.Column(db.Float)
    ubicacion_lng = db.Column(db.Float)
    
    # Timestamps
    reportado_en = db.Column(db.DateTime, default=datetime.utcnow)
    resuelto_en = db.Column(db.DateTime)
    
    # Resolución
    resolucion = db.Column(db.Text)
    resuelto_por = db.Column(db.String(100))
    
    # Relaciones
    repartidor = db.relationship('Repartidor', backref='reportes')
    pedido = db.relationship('Pedido', backref='reportes')
    
    def resolver(self, resolucion, resuelto_por):
        """Marcar incidencia como resuelta"""
        self.estado = 'resuelto'
        self.resolucion = resolucion
        self.resuelto_por = resuelto_por
        self.resuelto_en = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<ReporteIncidencia {self.tipo} - {self.repartidor.nombre}>'

# Modelos existentes actualizados

class Pedido(db.Model):
    """Modelo de pedido actualizado"""
    __tablename__ = 'pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    direccion_usuario_id = db.Column(db.Integer, db.ForeignKey('direccion_usuario.id'))
    
    # Información de la dirección (puede ser personalizada)
    direccion = db.Column(db.Text, nullable=False)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    
    # Fechas de servicio
    fecha_recoleccion = db.Column(db.Date, nullable=False)
    fecha_entrega = db.Column(db.Date, nullable=False)
    hora_recoleccion = db.Column(db.String(20), default="9:00-12:00")
    hora_entrega = db.Column(db.String(20), default="14:00-18:00")
    
    # Información del pedido
    precio_total = db.Column(db.Float, nullable=False)
    peso_estimado = db.Column(db.Float)
    
    # Estados: Solicitado, Recolectado, EnProceso, Listo, Entregado, Cancelado
    estado = db.Column(db.String(20), default='Solicitado')
    pagado = db.Column(db.Boolean, default=False)
    
    # Notas y observaciones
    notas = db.Column(db.Text)
    notas_internas = db.Column(db.Text)  # Solo para admin
    
    # Timestamps
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    items = db.relationship('PedidoItem', backref='pedido', lazy=True, cascade='all, delete-orphan')
    direccion_guardada = db.relationship('DireccionUsuario', backref='pedidos_asociados')
    
    @property
    def direccion_completa(self):
        """Obtener dirección completa (guardada o personalizada)"""
        if self.direccion_guardada:
            return self.direccion_guardada.direccion
        return self.direccion
    
    @property
    def coordenadas(self):
        """Obtener coordenadas (guardadas o personalizadas)"""
        if self.direccion_guardada:
            return (self.direccion_guardada.latitud, self.direccion_guardada.longitud)
        return (self.latitud, self.longitud)
    
    def puede_ser_recolectado(self):
        """Verificar si el pedido puede ser recolectado hoy"""
        return (self.estado == 'Solicitado' and 
                self.fecha_recoleccion <= datetime.now().date())
    
    def puede_ser_entregado(self):
        """Verificar si el pedido puede ser entregado hoy"""
        return (self.estado == 'Listo' and 
                self.fecha_entrega <= datetime.now().date())
    
    def __repr__(self):
        return f'<Pedido {self.id} - {self.usuario.nombre}>'

class PedidoItem(db.Model):
    """Items de un pedido"""
    __tablename__ = 'pedido_item'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    tipo_prenda_id = db.Column(db.Integer, db.ForeignKey('tipo_prenda.id'), nullable=False)
    
    cantidad = db.Column(db.Float, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relación con tipo de prenda
    tipo_prenda = db.relationship('TipoPrenda', backref='pedido_items')

class TipoPrenda(db.Model):
    """Tipos de prendas y precios"""
    __tablename__ = 'tipo_prenda'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio_por_kg = db.Column(db.Float, nullable=False)
    tiempo_lavado_horas = db.Column(db.Integer, default=24)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)

class Admin(db.Model):
    """Administradores del sistema"""
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)
    
    def verificar_contrasena(self, contrasena):
        return check_password_hash(self.contrasena, contrasena)

class Configuracion(db.Model):
    """Configuraciones del sistema"""
    __tablename__ = 'configuracion'
    
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.String(50), default='string')
    
    @classmethod
    def obtener(cls, clave, default=None):
        """Obtener valor de configuración"""
        config = cls.query.filter_by(clave=clave).first()
        return config.valor if config else default
    
    @classmethod
    def establecer(cls, clave, valor, descripcion=None):
        """Establecer valor de configuración"""
        config = cls.query.filter_by(clave=clave).first()
        if config:
            config.valor = valor
            if descripcion:
                config.descripcion = descripcion
        else:
            config = cls(clave=clave, valor=valor, descripcion=descripcion)
            db.session.add(config)
        db.session.commit()

# Event listeners para mantener consistencia

@event.listens_for(DireccionUsuario, 'before_insert')
@event.listens_for(DireccionUsuario, 'before_update')
def validar_direccion_principal(mapper, connection, target):
    """Asegurar que solo haya una dirección principal por usuario"""
    if target.es_principal:
        # Remover principal de otras direcciones del mismo usuario
        connection.execute(
            db.update(DireccionUsuario.__table__)
            .where(DireccionUsuario.usuario_id == target.usuario_id)
            .where(DireccionUsuario.id != target.id)
            .values(es_principal=False)
        )

@event.listens_for(RutaAsignada, 'before_insert')
@event.listens_for(RutaAsignada, 'before_update')
def validar_ruta_activa(mapper, connection, target):
    """Asegurar que un repartidor solo tenga una ruta activa"""
    if target.estado in ['aceptada', 'en_progreso']:
        # Desactivar otras rutas del mismo repartidor
        connection.execute(
            db.update(RutaAsignada.__table__)
            .where(RutaAsignada.repartidor_id == target.repartidor_id)
            .where(RutaAsignada.id != target.id)
            .where(RutaAsignada.estado.in_(['aceptada', 'en_progreso']))
            .values(estado='pausada')
        )