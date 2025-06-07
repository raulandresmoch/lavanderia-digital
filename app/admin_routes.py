# admin_routes.py - Rutas admin actualizadas con Google Maps
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, flash
from datetime import datetime, date, timedelta
from app.models import db, Pedido, Usuario, Admin
from app.extensions import db
from app.bot_repartidor_completo import obtener_repartidores_disponibles, enviar_ruta_a_repartidor, BotRepartidor
import requests
import os
from google_maps_utils import GoogleMapsIntegration, enviar_ruta_con_mapas_telegram

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator para requerir autenticación de admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de administradores"""
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')
        
        admin = Admin.query.filter_by(usuario=usuario).first()
        
        if admin and admin.verificar_contrasena(contrasena):
            session['admin_id'] = admin.id
            session['admin_usuario'] = admin.usuario
            session['admin_nombre'] = admin.nombre
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Credenciales incorrectas', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Logout de administradores"""
    session.clear()
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard principal del admin"""
    # Estadísticas básicas
    today = date.today()
    
    # Pedidos de hoy
    pedidos_hoy = Pedido.query.filter(
        Pedido.fecha_recoleccion == today
    ).count()
    
    entregas_hoy = Pedido.query.filter(
        Pedido.fecha_entrega == today
    ).count()
    
    # Ingresos del mes
    inicio_mes = today.replace(day=1)
    ingresos_mes = db.session.query(db.func.sum(Pedido.precio_total)).filter(
        Pedido.creado >= inicio_mes,
        Pedido.estado.in_(['Entregado', 'Listo'])
    ).scalar() or 0
    
    # Pedidos recientes
    pedidos_recientes = Pedido.query.order_by(Pedido.creado.desc()).limit(10).all()
    
    stats = {
        'pedidos_hoy': pedidos_hoy,
        'entregas_hoy': entregas_hoy,
        'ingresos_mes': ingresos_mes
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         pedidos_recientes=pedidos_recientes)

@admin_bp.route('/pedidos')
@admin_required
def pedidos():
    """Gestión de todos los pedidos"""
    pedidos = Pedido.query.order_by(Pedido.creado.desc()).all()
    return render_template('admin/pedidos.html', pedidos=pedidos)

@admin_bp.route('/rutas')
@admin_required
def rutas():
    """Gestión de rutas con Google Maps integrado"""
    # Obtener fecha del parámetro o usar hoy
    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_obj = date.today()
    else:
        fecha_obj = date.today()
    
       # Obtener pedidos para recolección con información del usuario
    recolecciones = Pedido.query.join(Usuario).filter(
        Pedido.fecha_recoleccion == fecha_obj,
        Pedido.estado == 'Solicitado'
    ).all()
    
    # Obtener pedidos para entrega con información del usuario
    entregas = Pedido.query.join(Usuario).filter(
        Pedido.fecha_entrega == fecha_obj,
        Pedido.estado == 'Listo'
    ).all()
    return render_template('admin/rutas.html', 
                         fecha=fecha_obj,
                         fecha_str=fecha_obj.strftime('%Y-%m-%d'),
                         recolecciones=recolecciones,
                         entregas=entregas)

@admin_bp.route('/api/generar-ruta-optimizada', methods=['POST'])
@admin_required
def generar_ruta_optimizada():
    """Generar rutas optimizadas con integración de Google Maps"""
    try:
        data = request.get_json()
        fecha_str = data.get('fecha')
        tipo = data.get('tipo')  # 'recoleccion' o 'entrega'
        
        # Validar parámetros
        if not fecha_str or not tipo:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros requeridos'
            }), 400
        
        # Parsear fecha
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Formato de fecha inválido'
            }), 400
        
        # Obtener pedidos según el tipo
        # Obtener pedidos según el tipo
        if tipo == 'recoleccion':
            pedidos = Pedido.query.filter(
                Pedido.fecha_recoleccion == fecha_obj,
                Pedido.estado == 'Solicitado'
            ).all()
        elif tipo == 'entrega':
            pedidos = Pedido.query.filter(
                Pedido.fecha_entrega == fecha_obj,
                Pedido.estado == 'Listo'
            ).all()
        else:
            return jsonify({
                'success': False,
                'error': 'Tipo de ruta inválido'
            }), 400

        if not pedidos:
            return jsonify({
                'success': True,
                'rutas': {},
                'total_pedidos': 0,
                'mensaje': f'No hay pedidos de {tipo} para {fecha_str}'
            })

        # Debug: imprimir información de pedidos
        print(f"📊 Encontrados {len(pedidos)} pedidos de {tipo}")
        for p in pedidos:
            print(f"  - Pedido #{p.id}: {p.usuario.nombre} - {p.direccion}")
        
        # Generar rutas optimizadas por zona
        rutas_por_zona = agrupar_pedidos_por_zona(pedidos)
        
        # Convertir a formato para respuesta con Google Maps
        # Convertir a formato para respuesta con Google Maps
        rutas_response = {}
        total_estimaciones = {
            'tiempo_total': 0,
            'distancia_total': 0,
            'paradas_total': 0
        }
        
        for zona, pedidos_zona in rutas_por_zona.items():
            # CORRECCIÓN: Los pedidos ya son diccionarios, no necesitan conversión
            pedidos_dict = pedidos_zona  # Ya son diccionarios desde agrupar_pedidos_por_zona
            
            # Generar información de Google Maps para esta zona
            estimacion_zona = GoogleMapsIntegration.generar_estimacion_tiempo(pedidos_dict)
            url_ruta_zona = GoogleMapsIntegration.generar_ruta_completa(pedidos_dict) if len(pedidos_dict) > 1 else None
            
            rutas_response[zona] = {
                'pedidos': pedidos_dict,
                'estimaciones': estimacion_zona,
                'url_google_maps': url_ruta_zona,
                'total_paradas': len(pedidos_dict)
            }
            
            # Sumar a totales
            total_estimaciones['tiempo_total'] += estimacion_zona['tiempo_total']
            total_estimaciones['distancia_total'] += estimacion_zona['distancia_total']
            total_estimaciones['paradas_total'] += estimacion_zona['paradas']
        
        # Generar URL para ruta completa del día
        todos_pedidos = []
        for zona_data in rutas_response.values():
            todos_pedidos.extend(zona_data['pedidos'])
        
        url_ruta_completa = GoogleMapsIntegration.generar_ruta_completa(todos_pedidos) if len(todos_pedidos) > 1 else None
        
        return jsonify({
            'success': True,
            'rutas': rutas_response,
            'total_pedidos': len(pedidos),
            'tipo': tipo,
            'fecha': fecha_str,
            'estimaciones_totales': total_estimaciones,
            'url_ruta_completa_dia': url_ruta_completa,
            'total_zonas': len(rutas_response)
        })
        
    except Exception as e:
        print(f"❌ Error generando ruta: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500

@admin_bp.route('/api/enviar-ruta-telegram', methods=['POST'])
@admin_required
def enviar_ruta_telegram():
    """Enviar ruta completa por Telegram con Google Maps"""
    try:
        data = request.get_json()
        repartidor_chat_id = data.get('repartidor_chat_id')
        ruta_data = data.get('ruta_data')
        # ruta_id = data.get('ruta_id', f"RUTA_{datetime.now().strftime('%Y%m%d_%H%M%S')}") # ruta_id no se usa más aquí
        
        if not repartidor_chat_id or not ruta_data:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros requeridos'
            }), 400
        
        # Obtener información del repartidor (simulado por ahora, idealmente de la DB de repartidores)
        repartidor_nombre = f"Repartidor_{repartidor_chat_id[-4:]}" # Podría obtenerse de repartidores.db si estuviera sincronizado

        # Intentar asignar la ruta y enviar notificación inicial
        exito_asignacion = enviar_ruta_a_repartidor(repartidor_chat_id, ruta_data)

        if exito_asignacion:
            # Si la asignación fue exitosa, enviar el mensaje detallado con mapas
            mensaje_mapas = GoogleMapsIntegration.generar_mensaje_telegram_con_mapas(ruta_data, repartidor_nombre)

            bot = BotRepartidor()
            bot.send_message(repartidor_chat_id, mensaje_mapas, parse_mode='Markdown')
            
            return jsonify({
                'success': True,
                'mensaje': f'Ruta enviada y asignada exitosamente a {repartidor_nombre}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error asignando la ruta en la base de datos del repartidor.'
            }), 500
            
    except Exception as e:
        print(f"❌ Error enviando ruta por Telegram: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500

@admin_bp.route('/api/repartidores-disponibles', methods=['GET'])
@admin_required
def repartidores_disponibles():
    """Obtener lista de repartidores disponibles"""
    try:
        repartidores = obtener_repartidores_disponibles()
        
        return jsonify({
            'success': True,
            'repartidores': repartidores
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo repartidores: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500

@admin_bp.route('/api/actualizar-estado', methods=['POST'])
@admin_required
def actualizar_estado():
    """Actualizar estado de un pedido"""
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        nuevo_estado = data.get('estado')
        
        if not pedido_id or not nuevo_estado:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros requeridos'
            }), 400
        
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({
                'success': False,
                'error': 'Pedido no encontrado'
            }), 404
        
        pedido.estado = nuevo_estado
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Estado actualizado a {nuevo_estado}'
        })
        
    except Exception as e:
        print(f"❌ Error actualizando estado: {e}")
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500

@admin_bp.route('/telegram')
@admin_required
def telegram():
    """Panel de configuración de Telegram"""
    # Obtener configuración actual
    config = {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'No configurado'),
        'admin_chats': os.getenv('TELEGRAM_ADMIN_CHATS', 'No configurado'),
        'openai_key': 'Configurado' if os.getenv('OPENAI_API_KEY') else 'No configurado'
    }
    
    return render_template('admin/telegram.html', config=config)

# Funciones auxiliares

# Líneas 393-420 aproximadamente en admin_routes.py
def agrupar_pedidos_por_zona(pedidos):
    """Agrupar pedidos por zona geográfica"""
    rutas_por_zona = {}
    
    for pedido in pedidos:
        # Determinar zona basada en la dirección
        zona = determinar_zona_por_direccion(pedido.direccion)
        
        if zona not in rutas_por_zona:
            rutas_por_zona[zona] = []
        
        # CORRECCIÓN: Convertir el objeto pedido a diccionario
        pedido_dict = {
            'id': pedido.id,
            'cliente': pedido.usuario.nombre,
            'telefono': pedido.usuario.telefono or 'No disponible',
            'direccion': pedido.direccion,
            'latitud': pedido.latitud or 19.4326,
            'longitud': pedido.longitud or -99.1332,
            'notas': pedido.notas or '',
            'precio': float(pedido.precio_total),
            'peso': float(pedido.peso_estimado or 0)
        }
        
        rutas_por_zona[zona].append(pedido_dict)
    
    # Optimizar orden dentro de cada zona
    for zona in rutas_por_zona:
        rutas_por_zona[zona] = optimizar_orden_zona(rutas_por_zona[zona])
    
    return rutas_por_zona

def determinar_zona_por_direccion(direccion):
    """Determinar zona geográfica basada en la dirección"""
    direccion_lower = direccion.lower()
    
    # Zonas de Ciudad de México
    zonas = {
        'Roma Norte': ['roma norte', 'roma', 'condesa'],
        'Polanco': ['polanco', 'anzures', 'nueva anzures'],
        'Del Valle': ['del valle', 'narvarte', 'piedad narvarte'],
        'Centro': ['centro', 'histórico', 'alameda'],
        'Santa Fe': ['santa fe', 'álvaro obregón'],
        'Zona Sur': ['coyoacán', 'san ángel', 'pedregal'],
        'Zona Norte': ['lindavista', 'gustavo a. madero', 'villa'],
        'Zona Oriente': ['iztapalapa', 'iztacalco', 'venustiano carranza'],
        'Otras Zonas': []  # Default
    }
    
    for zona, keywords in zonas.items():
        for keyword in keywords:
            if keyword in direccion_lower:
                return zona
    
    return 'Otras Zonas'

# Líneas 470-510 aproximadamente en admin_routes.py
def optimizar_orden_zona(pedidos_zona):
    """Optimizar el orden de los pedidos dentro de una zona"""
    if len(pedidos_zona) <= 1:
        return pedidos_zona
    
    # CORRECCIÓN: Los pedidos ya son diccionarios, no objetos SQLAlchemy
    pedidos_optimizados = []
    pedidos_restantes = pedidos_zona.copy()
    
    # Comenzar con el primer pedido
    actual = pedidos_restantes.pop(0)
    pedidos_optimizados.append(actual)
    
    # Agregar el pedido más cercano en cada iteración
    while pedidos_restantes:
        lat_actual = actual['latitud']
        lng_actual = actual['longitud']
        
        distancia_minima = float('inf')
        pedido_mas_cercano = None
        
        for pedido in pedidos_restantes:
            lat_pedido = pedido['latitud']
            lng_pedido = pedido['longitud']
            
            distancia = GoogleMapsIntegration.calcular_distancia_aproximada(
                lat_actual, lng_actual, lat_pedido, lng_pedido
            )
            
            if distancia < distancia_minima:
                distancia_minima = distancia
                pedido_mas_cercano = pedido
        
        if pedido_mas_cercano:
            pedidos_restantes.remove(pedido_mas_cercano)
            pedidos_optimizados.append(pedido_mas_cercano)
            actual = pedido_mas_cercano
    
    return pedidos_optimizados

def generar_codigo_ruta(tipo, fecha):
    """Generar código único para la ruta"""
    fecha_str = fecha.strftime('%Y%m%d') if hasattr(fecha, 'strftime') else fecha
    timestamp = datetime.now().strftime('%H%M%S')
    return f"{tipo.upper()}_{fecha_str}_{timestamp}"