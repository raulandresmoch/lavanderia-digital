from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, Usuario, TipoPrenda, Pedido, ItemPedido, Configuracion
from datetime import datetime, timedelta
import json

main = Blueprint("main", __name__)

@main.route("/")
def home():
    if "usuario_id" in session:
        usuario = Usuario.query.get(session["usuario_id"])
        return render_template("index.html", usuario=usuario)
    return redirect(url_for("main.login"))

@main.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        contrasena = request.form["contrasena"]
        telefono = request.form.get("telefono", "")
        ubicacion = request.form["ubicacion"]

        if Usuario.query.filter_by(email=email).first():
            flash("Este correo ya está registrado.", "error")
            return render_template("register.html")

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            contrasena=generate_password_hash(contrasena),
            telefono=telefono,
            ubicacion=ubicacion,
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        contrasena = request.form["contrasena"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.contrasena, contrasena):
            session["usuario_id"] = usuario.id
            return redirect(url_for("main.home"))

        flash("Credenciales inválidas.", "error")
    return render_template("login.html")

@main.route("/logout")
def logout():
    session.pop("usuario_id", None)
    return redirect(url_for("main.login"))

# === SISTEMA DE COTIZACIÓN ===

@main.route("/cotizar")
def cotizar():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    tipos_prenda = TipoPrenda.query.filter_by(activo=True).all()
    return render_template("cotizar.html", tipos_prenda=tipos_prenda)

@main.route("/api/calcular-cotizacion", methods=["POST"])
def calcular_cotizacion():
    if "usuario_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        data = request.get_json()
        items = data.get("items", [])
        fecha_recoleccion = datetime.strptime(data.get("fecha_recoleccion"), "%Y-%m-%d").date()
        
        if not items:
            return jsonify({"error": "No hay items seleccionados"}), 400
        
        # Calcular cotización
        total = 0
        tiempo_max_horas = 0
        detalles = []
        
        for item in items:
            tipo_id = item["tipo_prenda_id"]
            cantidad = float(item["cantidad"])
            
            tipo_prenda = TipoPrenda.query.get(tipo_id)
            if not tipo_prenda:
                continue
                
            subtotal = cantidad * tipo_prenda.precio_por_kg
            total += subtotal
            
            # El tiempo máximo determina cuándo estará listo
            if tipo_prenda.tiempo_lavado_horas > tiempo_max_horas:
                tiempo_max_horas = tipo_prenda.tiempo_lavado_horas
            
            detalles.append({
                "tipo": tipo_prenda.nombre,
                "cantidad": cantidad,
                "precio_unitario": tipo_prenda.precio_por_kg,
                "subtotal": subtotal
            })
        
        # Calcular fecha de entrega
        # Si recolectamos en la mañana, agregamos el tiempo de lavado
        dias_necesarios = max(1, (tiempo_max_horas + 12) // 24)  # +12 para considerar que recolectamos en la mañana
        fecha_entrega = fecha_recoleccion + timedelta(days=dias_necesarios)
        
        # Asegurar que la entrega no sea domingo (día 6)
        while fecha_entrega.weekday() == 6:
            fecha_entrega += timedelta(days=1)
        
        return jsonify({
            "success": True,
            "total": round(total, 2),
            "fecha_entrega": fecha_entrega.strftime("%Y-%m-%d"),
            "dias_servicio": dias_necesarios,
            "detalles": detalles
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/fechas-disponibles")
def fechas_disponibles():
    """Retorna las fechas disponibles para recolección"""
    try:
        fechas = []
        fecha_actual = datetime.now().date()
        
        # Generar fechas disponibles para los próximos 30 días
        # Excluir domingos (día 6)
        for i in range(1, 31):  # Empezar desde mañana
            fecha = fecha_actual + timedelta(days=i)
            if fecha.weekday() != 6:  # No domingo
                fechas.append(fecha.strftime("%Y-%m-%d"))
        
        return jsonify({"fechas": fechas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/confirmar-pedido", methods=["POST"])
def confirmar_pedido():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Crear el pedido
        nuevo_pedido = Pedido(
            usuario_id=session["usuario_id"],
            direccion=data["direccion"],
            fecha_recoleccion=datetime.strptime(data["fecha_recoleccion"], "%Y-%m-%d").date(),
            fecha_entrega=datetime.strptime(data["fecha_entrega"], "%Y-%m-%d").date(),
            precio_total=float(data["precio_total"]),
            peso_estimado=float(data.get("peso_estimado", 0)),
            notas=data.get("notas", "")
        )
        
        db.session.add(nuevo_pedido)
        db.session.flush()  # Para obtener el ID
        
        # Crear los items del pedido
        items = json.loads(data["items"]) if isinstance(data["items"], str) else data["items"]
        for item in items:
            item_pedido = ItemPedido(
                pedido_id=nuevo_pedido.id,
                tipo_prenda_id=item["tipo_prenda_id"],
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"],
                subtotal=item["subtotal"]
            )
            db.session.add(item_pedido)
        
        db.session.commit()
        
        flash("¡Pedido creado exitosamente! Te contactaremos pronto.", "success")
        return jsonify({"success": True, "pedido_id": nuevo_pedido.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main.route("/mis-pedidos")
def mis_pedidos():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    pedidos = Pedido.query.filter_by(usuario_id=session["usuario_id"]).order_by(Pedido.creado.desc()).all()
    return render_template("mis_pedidos.html", pedidos=pedidos)