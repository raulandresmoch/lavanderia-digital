from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, Admin, Pedido, Usuario, TipoPrenda, EstadisticasPedidos, DireccionUsuario
from datetime import datetime, timedelta
from functools import wraps
import logging

# Configurar logger
logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    """Decorador para requerir autenticación de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated_function

# === AUTENTICACIÓN ADMIN ===

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]

        admin = Admin.query.filter_by(usuario=usuario, activo=True).first()

        if admin and check_password_hash(admin.contrasena, contrasena):
            session["admin_id"] = admin.id
            session["admin_nombre"] = admin.nombre
            return redirect(url_for("admin.dashboard"))

        flash("Credenciales inválidas.", "error")
    
    return render_template("admin/login.html")

@admin_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    session.pop("admin_nombre", None)
    return redirect(url_for("admin.login"))

# === DASHBOARD PRINCIPAL ===

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    # Estadísticas del día
    hoy = datetime.now().date()
    
    # Pedidos de hoy
    pedidos_hoy = Pedido.query.filter(Pedido.fecha_recoleccion == hoy).all()
    entregas_hoy = Pedido.query.filter(Pedido.fecha_entrega == hoy).all()
    
    # Estadísticas generales
    stats = {
        'pedidos_hoy': len(pedidos_hoy),
        'entregas_hoy': len(entregas_hoy),
        'ingresos_mes': EstadisticasPedidos.ingresos_mes_actual(),
        'estados': EstadisticasPedidos.pedidos_por_estado()
    }
    
    # Pedidos recientes (últimos 10)
    pedidos_recientes = Pedido.query.order_by(Pedido.creado.desc()).limit(10).all()
    
    return render_template("admin/dashboard.html", 
                         stats=stats, 
                         pedidos_hoy=pedidos_hoy,
                         entregas_hoy=entregas_hoy,
                         pedidos_recientes=pedidos_recientes)

# === GESTIÓN DE PEDIDOS ===

@admin_bp.route("/pedidos")
@admin_required
def pedidos():
    # Filtros
    fecha_filtro = request.args.get('fecha')
    estado_filtro = request.args.get('estado')
    
    query = Pedido.query
    
    if fecha_filtro:
        fecha = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
        query = query.filter(
            (Pedido.fecha_recoleccion == fecha) | 
            (Pedido.fecha_entrega == fecha)
        )
    
    if estado_filtro and estado_filtro != 'todos':
        query = query.filter(Pedido.estado == estado_filtro)
    
    pedidos = query.order_by(Pedido.creado.desc()).all()
    
    # Estados disponibles para el filtro
    estados = ['todos', 'Solicitado', 'Recolectado', 'EnProceso', 'Listo', 'Entregado']
    
    return render_template("admin/pedidos.html", 
                         pedidos=pedidos, 
                         estados=estados,
                         fecha_filtro=fecha_filtro,
                         estado_filtro=estado_filtro)

@admin_bp.route("/pedido/<int:pedido_id>")
@admin_required
def detalle_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template("admin/detalle_pedido.html", pedido=pedido)

@admin_bp.route("/api/actualizar-estado", methods=["POST"])
@admin_required
def actualizar_estado():
    try:
        data = request.get_json()
        pedido_id = data.get("pedido_id")
        nuevo_estado = data.get("estado")
        
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return jsonify({"error": "Pedido no encontrado"}), 404
        
        pedido.estado = nuevo_estado
        pedido.actualizado = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "mensaje": f"Estado actualizado a {nuevo_estado}",
            "pedido_id": pedido_id,
            "nuevo_estado": nuevo_estado
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error actualizando estado: {e}")
        return jsonify({"error": str(e)}), 500

# === RUTAS DIARIAS ===

@admin_bp.route("/rutas")
@admin_required
def rutas():
    fecha_str = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha = datetime.now().date()
        fecha_str = fecha.strftime('%Y-%m-%d')
    
    # Recolecciones del día
    recolecciones = Pedido.query.filter(
        Pedido.fecha_recoleccion == fecha,
        Pedido.estado.in_(['Solicitado', 'Recolectado'])
    ).order_by(Pedido.direccion).all()
    
    # Entregas del día
    entregas = Pedido.query.filter(
        Pedido.fecha_entrega == fecha,
        Pedido.estado.in_(['Listo', 'Entregado'])
    ).order_by(Pedido.direccion).all()
    
    return render_template("admin/rutas.html", 
                         fecha=fecha,
                         fecha_str=fecha_str,
                         recolecciones=recolecciones,
                         entregas=entregas)

@admin_bp.route("/api/generar-ruta-optimizada", methods=["POST"])
@admin_required
def generar_ruta_optimizada():
    """Generar ruta optimizada básica (por zona)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        fecha_str = data.get("fecha")
        tipo = data.get("tipo")  # 'recoleccion' o 'entrega'
        
        if not fecha_str or not tipo:
            return jsonify({"error": "Faltan parámetros requeridos"}), 400
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido"}), 400
        
        logger.info(f"Generando ruta para {fecha} tipo {tipo}")
        
        # Obtener pedidos según el tipo
        if tipo == 'recoleccion':
            pedidos = Pedido.query.filter(
                Pedido.fecha_recoleccion == fecha,
                Pedido.estado == 'Solicitado'
            ).all()
        elif tipo == 'entrega':
            pedidos = Pedido.query.filter(
                Pedido.fecha_entrega == fecha,
                Pedido.estado == 'Listo'
            ).all()
        else:
            return jsonify({"error": "Tipo de ruta inválido"}), 400
        
        logger.info(f"Encontrados {len(pedidos)} pedidos para procesar")
        
        if not pedidos:
            return jsonify({
                "success": True,
                "rutas": {},
                "total_pedidos": 0,
                "mensaje": f"No hay pedidos de {tipo} para esta fecha"
            })
        
        # Agrupación básica por zona (primeras 3 palabras de la dirección)
        rutas_por_zona = {}
        
        for pedido in pedidos:
            try:
                # Crear zona basada en las primeras palabras de la dirección
                palabras_direccion = pedido.direccion.split()
                zona = ' '.join(palabras_direccion[:3]) if len(palabras_direccion) >= 3 else pedido.direccion
                
                if zona not in rutas_por_zona:
                    rutas_por_zona[zona] = []
                
                # Obtener información del usuario
                usuario = pedido.usuario
                telefono = usuario.telefono if usuario.telefono else 'No registrado'
                
                pedido_info = {
                    'id': pedido.id,
                    'direccion': pedido.direccion,
                    'cliente': usuario.nombre,
                    'telefono': telefono,
                    'notas': pedido.notas or '',
                    'total': float(pedido.precio_total),
                    'estado': pedido.estado
                }
                
                rutas_por_zona[zona].append(pedido_info)
                
            except Exception as e:
                logger.error(f"Error procesando pedido {pedido.id}: {e}")
                continue
        
        logger.info(f"Rutas generadas: {len(rutas_por_zona)} zonas")
        
        return jsonify({
            "success": True,
            "rutas": rutas_por_zona,
            "total_pedidos": len(pedidos),
            "tipo": tipo,
            "fecha": fecha_str
        })
        
    except Exception as e:
        logger.error(f"Error en generar_ruta_optimizada: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

# === REPORTES ===

@admin_bp.route("/reportes")
@admin_required
def reportes():
    # Estadísticas del último mes
    fecha_inicio = datetime.now() - timedelta(days=30)
    
    pedidos_mes = Pedido.query.filter(Pedido.creado >= fecha_inicio).count()
    ingresos_mes = EstadisticasPedidos.ingresos_mes_actual()
    
    # Pedidos por día (últimos 7 días)
    pedidos_por_dia = []
    for i in range(7):
        fecha = datetime.now().date() - timedelta(days=i)
        count = Pedido.query.filter(Pedido.fecha_recoleccion == fecha).count()
        pedidos_por_dia.append({
            'fecha': fecha.strftime('%d/%m'),
            'cantidad': count
        })
    
    pedidos_por_dia.reverse()
    
    return render_template("admin/reportes.html",
                         pedidos_mes=pedidos_mes,
                         ingresos_mes=ingresos_mes,
                         pedidos_por_dia=pedidos_por_dia)