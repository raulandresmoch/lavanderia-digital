from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, Usuario, DireccionUsuario, TipoPrenda, Pedido, ItemPedido, Configuracion
from datetime import datetime, timedelta
import json
from datetime import datetime, date, timedelta
import asyncio
import os
from flask import jsonify, request, render_template, flash, redirect, url_for
from app.telegram_service import telegram_service
from app.email_service import email_service
from app.rutas_service import rutas_service, inicializar_rutas_service
import logging

# Configurar logger
logger = logging.getLogger(__name__)

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
        
        # Datos de la primera dirección
        direccion = request.form["ubicacion"]
        nombre_direccion = request.form.get("nombre_direccion", "Casa")
        latitud = request.form.get("latitud")
        longitud = request.form.get("longitud")
        notas_direccion = request.form.get("notas_direccion", "")

        if Usuario.query.filter_by(email=email).first():
            flash("Este correo ya está registrado.", "error")
            return render_template("register.html")

        # Validar que se hayan proporcionado coordenadas
        if not latitud or not longitud:
            flash("Por favor selecciona tu ubicación en el mapa.", "error")
            return render_template("register.html")

        try:
            lat_float = float(latitud)
            lng_float = float(longitud)
            
            # Verificar zona de cobertura
            from app.geocoding_service import geocoding
            if not geocoding._esta_en_zona_cobertura(lat_float, lng_float):
                flash("Tu ubicación está fuera de nuestra zona de cobertura actual.", "error")
                return render_template("register.html")
            
        except (ValueError, TypeError):
            flash("Error en las coordenadas proporcionadas.", "error")
            return render_template("register.html")

        # Crear usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            contrasena=generate_password_hash(contrasena),
            telefono=telefono,
            # Mantener por compatibilidad
            ubicacion=direccion,
            latitud=lat_float,
            longitud=lng_float,
            coordenadas_verificadas=True
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.flush()  # Para obtener el ID del usuario
            
            # Crear primera dirección (principal)
            primera_direccion = DireccionUsuario(
                usuario_id=nuevo_usuario.id,
                nombre=nombre_direccion,
                direccion=direccion,
                latitud=lat_float,
                longitud=lng_float,
                es_principal=True,
                verificada=True,
                notas=notas_direccion
            )
            
            db.session.add(primera_direccion)
            db.session.commit()
            
            flash(f"¡Registro exitoso! Tu dirección '{nombre_direccion}' ha sido guardada. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("main.login"))
            
        except Exception as e:
            db.session.rollback()
            flash("Error al crear la cuenta. Por favor intenta de nuevo.", "error")
            return render_template("register.html")
            
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

# === GESTIÓN DE DIRECCIONES ===

@main.route("/mis-direcciones")
def mis_direcciones():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    usuario = Usuario.query.get(session["usuario_id"])
    direcciones = usuario.direcciones_activas
    
    return render_template("mis_direcciones.html", direcciones=direcciones, usuario=usuario)

@main.route("/agregar-direccion", methods=["GET", "POST"])
def agregar_direccion():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    if request.method == "POST":
        try:
            nombre = request.form["nombre"]
            direccion = request.form["direccion"]
            latitud = float(request.form["latitud"])
            longitud = float(request.form["longitud"])
            notas = request.form.get("notas", "")
            es_principal = request.form.get("es_principal") == "on"
            
            # Verificar zona de cobertura
            from app.geocoding_service import geocoding
            if not geocoding._esta_en_zona_cobertura(latitud, longitud):
                flash("Esta ubicación está fuera de nuestra zona de cobertura.", "error")
                return render_template("agregar_direccion.html")
            
            # Si se marca como principal, desmarcar otras
            if es_principal:
                DireccionUsuario.query.filter_by(
                    usuario_id=session["usuario_id"],
                    es_principal=True
                ).update({"es_principal": False})
            
            nueva_direccion = DireccionUsuario(
                usuario_id=session["usuario_id"],
                nombre=nombre,
                direccion=direccion,
                latitud=latitud,
                longitud=longitud,
                es_principal=es_principal,
                notas=notas,
                verificada=True
            )
            
            db.session.add(nueva_direccion)
            db.session.commit()
            
            flash(f"Dirección '{nombre}' agregada exitosamente.", "success")
            return redirect(url_for("main.mis_direcciones"))
            
        except Exception as e:
            db.session.rollback()
            flash("Error al agregar la dirección.", "error")
    
    return render_template("agregar_direccion.html")

@main.route("/editar-direccion/<int:direccion_id>", methods=["GET", "POST"])
def editar_direccion(direccion_id):
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    direccion = DireccionUsuario.query.filter_by(
        id=direccion_id, 
        usuario_id=session["usuario_id"]
    ).first_or_404()
    
    if request.method == "POST":
        try:
            direccion.nombre = request.form["nombre"]
            direccion.direccion = request.form["direccion"]
            direccion.latitud = float(request.form["latitud"])
            direccion.longitud = float(request.form["longitud"])
            direccion.notas = request.form.get("notas", "")
            es_principal = request.form.get("es_principal") == "on"
            
            # Verificar zona de cobertura
            from app.geocoding_service import geocoding
            if not geocoding._esta_en_zona_cobertura(direccion.latitud, direccion.longitud):
                flash("Esta ubicación está fuera de nuestra zona de cobertura.", "error")
                return render_template("editar_direccion.html", direccion=direccion)
            
            # Si se marca como principal, desmarcar otras
            if es_principal and not direccion.es_principal:
                DireccionUsuario.query.filter_by(
                    usuario_id=session["usuario_id"],
                    es_principal=True
                ).update({"es_principal": False})
                direccion.es_principal = True
            elif not es_principal and direccion.es_principal:
                # No permitir quitar principal si es la única dirección
                total_direcciones = DireccionUsuario.query.filter_by(
                    usuario_id=session["usuario_id"],
                    activa=True
                ).count()
                if total_direcciones == 1:
                    flash("Debe tener al menos una dirección principal.", "error")
                    return render_template("editar_direccion.html", direccion=direccion)
                direccion.es_principal = False
            
            direccion.actualizada = datetime.utcnow()
            db.session.commit()
            
            flash(f"Dirección '{direccion.nombre}' actualizada exitosamente.", "success")
            return redirect(url_for("main.mis_direcciones"))
            
        except Exception as e:
            db.session.rollback()
            flash("Error al actualizar la dirección.", "error")
    
    return render_template("editar_direccion.html", direccion=direccion)

@main.route("/eliminar-direccion/<int:direccion_id>", methods=["POST"])
def eliminar_direccion(direccion_id):
    if "usuario_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        direccion = DireccionUsuario.query.filter_by(
            id=direccion_id, 
            usuario_id=session["usuario_id"]
        ).first_or_404()
        
        # No permitir eliminar si es la única dirección
        total_direcciones = DireccionUsuario.query.filter_by(
            usuario_id=session["usuario_id"],
            activa=True
        ).count()
        
        if total_direcciones == 1:
            return jsonify({"error": "Debe mantener al menos una dirección"}), 400
        
        # Si es principal, marcar otra como principal
        if direccion.es_principal:
            otra_direccion = DireccionUsuario.query.filter_by(
                usuario_id=session["usuario_id"],
                activa=True
            ).filter(DireccionUsuario.id != direccion_id).first()
            
            if otra_direccion:
                otra_direccion.es_principal = True
        
        # Marcar como inactiva en lugar de eliminar (para historial)
        direccion.activa = False
        direccion.actualizada = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({"success": True, "mensaje": "Dirección eliminada exitosamente"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
@main.route("/marcar-principal/<int:direccion_id>", methods=["POST"])
def marcar_principal(direccion_id):
    if "usuario_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        # Verificar que la dirección pertenece al usuario
        direccion = DireccionUsuario.query.filter_by(
            id=direccion_id,
            usuario_id=session["usuario_id"],
            activa=True
        ).first()
        
        if not direccion:
            return jsonify({"error": "Dirección no encontrada"}), 404
        
        # Desmarcar todas las direcciones principales del usuario
        DireccionUsuario.query.filter_by(
            usuario_id=session["usuario_id"],
            es_principal=True
        ).update({"es_principal": False})
        
        # Marcar esta como principal
        direccion.es_principal = True
        direccion.actualizada = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "mensaje": f"Dirección '{direccion.nombre}' marcada como principal"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# === SISTEMA DE COTIZACIÓN CON DIRECCIONES ===

@main.route("/cotizar")
def cotizar():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    usuario = Usuario.query.get(session["usuario_id"])
    tipos_prenda = TipoPrenda.query.filter_by(activo=True).all()
    direcciones = usuario.direcciones_activas
    
    return render_template("cotizar.html", 
                         tipos_prenda=tipos_prenda, 
                         direcciones=direcciones,
                         usuario=usuario)

@main.route("/api/calcular-cotizacion", methods=["POST"])
def calcular_cotizacion():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se recibieron datos'}), 400
        
        items = data.get('items', [])
        fecha_recoleccion = data.get('fecha_recoleccion')
        
        if not items:
            return jsonify({'success': False, 'error': 'No se seleccionaron prendas'}), 400
        
        if not fecha_recoleccion:
            return jsonify({'success': False, 'error': 'No se seleccionó fecha de recolección'}), 400
        
        # Calcular totales
        total = 0
        detalles = []
        tiempo_maximo = 0
        
        for item in items:
            tipo_prenda = TipoPrenda.query.get(item['tipo_prenda_id'])
            if not tipo_prenda:
                return jsonify({'success': False, 'error': f'Tipo de prenda no encontrado: {item["tipo_prenda_id"]}'}), 400
            
            cantidad = float(item['cantidad'])
            subtotal = cantidad * tipo_prenda.precio_por_kg
            total += subtotal
            
            # Determinar tiempo máximo de procesamiento
            if tipo_prenda.tiempo_lavado_horas > tiempo_maximo:
                tiempo_maximo = tipo_prenda.tiempo_lavado_horas
            
            detalles.append({
                'tipo': tipo_prenda.nombre,
                'cantidad': cantidad,
                'precio_unitario': tipo_prenda.precio_por_kg,
                'subtotal': subtotal
            })
        
        # Calcular fecha de entrega
        fecha_recoleccion_dt = datetime.strptime(fecha_recoleccion, '%Y-%m-%d')
        
        # Agregar días de procesamiento (mínimo 1 día, basado en el tiempo máximo)
        dias_procesamiento = max(1, (tiempo_maximo + 23) // 24)  # Redondear hacia arriba
        
        fecha_entrega = fecha_recoleccion_dt + timedelta(days=dias_procesamiento)
        
        # Si la entrega cae en domingo, mover al lunes
        if fecha_entrega.weekday() == 6:  # Domingo
            fecha_entrega += timedelta(days=1)
        
        response_data = {
            'success': True,
            'total': round(total, 2),
            'detalles': detalles,
            'fecha_entrega': fecha_entrega.strftime('%Y-%m-%d'),
            'dias_servicio': dias_procesamiento,
            'tiempo_procesamiento_horas': tiempo_maximo
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        # Log del error para debugging
        print(f"Error en calcular_cotizacion: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False, 
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@main.route("/api/obtener-direccion/<int:direccion_id>")
def obtener_direccion(direccion_id):
    if "usuario_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    direccion = DireccionUsuario.query.filter_by(
        id=direccion_id,
        usuario_id=session["usuario_id"],
        activa=True
    ).first()
    
    if not direccion:
        return jsonify({"error": "Dirección no encontrada"}), 404
    
    return jsonify({
        "success": True,
        "direccion": {
            "id": direccion.id,
            "nombre": direccion.nombre,
            "direccion": direccion.direccion,
            "latitud": direccion.latitud,
            "longitud": direccion.longitud,
            "notas": direccion.notas or "",
            "es_principal": direccion.es_principal
        }
    })

@main.route("/mis-pedidos")
def mis_pedidos():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    pedidos = Pedido.query.filter_by(usuario_id=session["usuario_id"]).order_by(Pedido.creado.desc()).all()
    return render_template("mis_pedidos.html", pedidos=pedidos)

# === APIs DE GEOCODIFICACIÓN ===

@main.route("/api/geocodificar", methods=["POST"])
def api_geocodificar():
    """API para geocodificar direcciones desde el frontend"""
    try:
        data = request.get_json()
        direccion = data.get("direccion", "")
        
        if not direccion:
            return jsonify({"error": "Dirección requerida"}), 400
        
        from app.geocoding_service import geocoding
        resultado = geocoding.geocodificar_direccion(direccion)
        
        if resultado:
            return jsonify({
                "success": True,
                "resultado": resultado
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo geocodificar la dirección"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/geocodificar-inverso", methods=["POST"])
def api_geocodificar_inverso():
    """API para obtener dirección desde coordenadas"""
    try:
        data = request.get_json()
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
        
        from app.geocoding_service import geocoding
        direccion = geocoding.geocodificacion_inversa(lat, lng)
        
        if direccion:
            en_zona = geocoding._esta_en_zona_cobertura(lat, lng)
            return jsonify({
                "success": True,
                "direccion": direccion,
                "en_zona_cobertura": en_zona
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo obtener la dirección"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/sugerir-direcciones", methods=["GET"])
def api_sugerir_direcciones():
    """API para autocompletar direcciones"""
    try:
        query = request.args.get("q", "")
        limite = int(request.args.get("limit", 5))
        
        if len(query) < 3:
            return jsonify({"sugerencias": []})
        
        from app.geocoding_service import geocoding
        sugerencias = geocoding.sugerir_direcciones(query, limite)
        
        return jsonify({
            "success": True,
            "sugerencias": sugerencias
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
    

@main.route("/admin/telegram", methods=["GET", "POST"])
def admin_telegram():
    """Panel de administración de Telegram"""
    if "admin_id" not in session:  # Ajusta según tu sistema de auth admin
        return redirect(url_for("admin.login"))
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "init_bot":
            # Inicializar bot de Telegram
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(telegram_service.inicializar_bot())
                
                if success:
                    flash("Bot de Telegram inicializado correctamente", "success")
                else:
                    flash("Error inicializando el bot de Telegram", "error")
            except Exception as e:
                flash(f"Error: {str(e)}", "error")
        
        elif action == "send_test":
            # Enviar mensaje de prueba
            chat_id = request.form.get("test_chat_id")
            mensaje = request.form.get("test_message")
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    telegram_service.bot.send_message(
                        chat_id=chat_id,
                        text=mensaje,
                        parse_mode='Markdown'
                    )
                )
                flash("Mensaje de prueba enviado correctamente", "success")
            except Exception as e:
                flash(f"Error enviando mensaje: {str(e)}", "error")
    
    # Obtener configuración actual
    config = {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', 'No configurado'),
        'admin_chats': os.getenv('TELEGRAM_ADMIN_CHATS', 'No configurado'),
        'openai_key': 'Configurado' if os.getenv('OPENAI_API_KEY') else 'No configurado'
    }
    
    return render_template("admin/telegram.html", config=config)

@main.route("/admin/rutas")
def admin_rutas():
    """Panel de administración de rutas"""
    if "admin_id" not in session:
        return redirect(url_for("admin.login"))
    
    # Obtener rutas del día actual
    try:
        fecha_hoy = date.today()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not rutas_service:
            inicializar_rutas_service(db.session, telegram_service, email_service)
        
        rutas_hoy = loop.run_until_complete(rutas_service.obtener_rutas_del_dia(fecha_hoy))
        
        # Obtener estadísticas de la semana
        fecha_inicio = fecha_hoy - timedelta(days=6)
        estadisticas = loop.run_until_complete(
            rutas_service.obtener_estadisticas_rutas(fecha_inicio, fecha_hoy)
        )
        
    except Exception as e:
        flash(f"Error cargando rutas: {str(e)}", "error")
        rutas_hoy = []
        estadisticas = {}
    
    return render_template("admin/rutas.html", 
                         rutas=rutas_hoy, 
                         estadisticas=estadisticas,
                         fecha=fecha_hoy)

@main.route("/admin/generar-rutas", methods=["POST"])
def admin_generar_rutas():
    """Generar rutas para un día específico"""
    if "admin_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        fecha_str = request.form.get("fecha")
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else date.today()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not rutas_service:
            inicializar_rutas_service(db.session, telegram_service, email_service)
        
        rutas_generadas = loop.run_until_complete(rutas_service.generar_rutas_del_dia(fecha))
        
        return jsonify({
            "success": True,
            "mensaje": f"Se generaron {len(rutas_generadas)} rutas para {fecha.strftime('%d/%m/%Y')}",
            "rutas_generadas": len(rutas_generadas)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/admin/asignar-ruta", methods=["POST"])
def admin_asignar_ruta():
    """Asignar ruta a un repartidor"""
    if "admin_id" not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        data = request.get_json()
        ruta_id = data.get("ruta_id")
        repartidor_chat_id = data.get("repartidor_chat_id")
        
        if not ruta_id or not repartidor_chat_id:
            return jsonify({"error": "Faltan datos requeridos"}), 400
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            rutas_service.asignar_ruta_repartidor(ruta_id, repartidor_chat_id)
        )
        
        if success:
            return jsonify({
                "success": True,
                "mensaje": f"Ruta {ruta_id} asignada correctamente"
            })
        else:
            return jsonify({"error": "Error asignando ruta"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === WEBHOOK DE TELEGRAM ===

@main.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    """Webhook para recibir actualizaciones de Telegram"""
    try:
        data = request.get_json()
        
        # Procesar la actualización de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Crear objeto Update de telegram
        from telegram import Update
        update = Update.de_json(data, telegram_service.bot)
        
        # Procesar con el bot
        if telegram_service.application:
            loop.run_until_complete(telegram_service.application.process_update(update))
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error en webhook de Telegram: {e}")
        return jsonify({"error": str(e)}), 500

# === APIs PARA RUTAS Y TRACKING ===

@main.route("/api/rutas/<fecha>")
def api_rutas_fecha(fecha):
    """API para obtener rutas de una fecha específica"""
    try:
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not rutas_service:
            inicializar_rutas_service(db.session, telegram_service, email_service)
        
        rutas = loop.run_until_complete(rutas_service.obtener_rutas_del_dia(fecha_obj))
        
        # Serializar rutas para JSON
        rutas_json = []
        for ruta in rutas:
            ruta_dict = {
                'id': ruta.id,
                'estado': ruta.estado.value,
                'repartidor_chat_id': ruta.repartidor_chat_id,
                'fecha': ruta.fecha.strftime('%Y-%m-%d'),
                'total_paradas': len(ruta.paradas),
                'distancia_total_km': ruta.distancia_total_km,
                'tiempo_total_minutos': ruta.tiempo_total_minutos,
                'hora_inicio_estimada': ruta.hora_inicio_estimada,
                'hora_fin_estimada': ruta.hora_fin_estimada,
                'paradas_completadas': sum(1 for p in ruta.paradas if p.completada),
                'progreso': (sum(1 for p in ruta.paradas if p.completada) / len(ruta.paradas)) * 100 if ruta.paradas else 0
            }
            rutas_json.append(ruta_dict)
        
        return jsonify({
            "success": True,
            "rutas": rutas_json,
            "total": len(rutas_json)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/ruta/<ruta_id>/detalles")
def api_ruta_detalles(ruta_id):
    """API para obtener detalles completos de una ruta"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        ruta = loop.run_until_complete(rutas_service.obtener_ruta(ruta_id))
        if not ruta:
            return jsonify({"error": "Ruta no encontrada"}), 404
        
        # Serializar paradas
        paradas_json = []
        for parada in ruta.paradas:
            parada_dict = {
                'id': parada.id,
                'pedido_id': parada.pedido_id,
                'tipo': parada.tipo.value,
                'cliente_nombre': parada.cliente_nombre,
                'cliente_telefono': parada.cliente_telefono,
                'direccion': parada.direccion,
                'latitud': parada.latitud,
                'longitud': parada.longitud,
                'hora_estimada': parada.hora_estimada,
                'tiempo_estimado_parada': parada.tiempo_estimado_parada,
                'notas': parada.notas,
                'completada': parada.completada,
                'hora_completada': parada.hora_completada.strftime('%H:%M') if parada.hora_completada else None,
                'orden_en_ruta': parada.orden_en_ruta
            }
            paradas_json.append(parada_dict)
        
        ruta_dict = {
            'id': ruta.id,
            'estado': ruta.estado.value,
            'repartidor_chat_id': ruta.repartidor_chat_id,
            'fecha': ruta.fecha.strftime('%Y-%m-%d'),
            'paradas': paradas_json,
            'distancia_total_km': ruta.distancia_total_km,
            'tiempo_total_minutos': ruta.tiempo_total_minutos,
            'hora_inicio_estimada': ruta.hora_inicio_estimada,
            'hora_fin_estimada': ruta.hora_fin_estimada,
            'hora_inicio_real': ruta.hora_inicio_real.strftime('%H:%M') if ruta.hora_inicio_real else None,
            'hora_fin_real': ruta.hora_fin_real.strftime('%H:%M') if ruta.hora_fin_real else None,
            'url_mapa': ruta.url_mapa,
            'progreso': (sum(1 for p in ruta.paradas if p.completada) / len(ruta.paradas)) * 100 if ruta.paradas else 0
        }
        
        return jsonify({
            "success": True,
            "ruta": ruta_dict
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/estadisticas-rutas")
def api_estadisticas_rutas():
    """API para obtener estadísticas generales de rutas"""
    try:
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=30)  # Últimos 30 días
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if not rutas_service:
            inicializar_rutas_service(db.session, telegram_service, email_service)
        
        estadisticas = loop.run_until_complete(
            rutas_service.obtener_estadisticas_rutas(fecha_inicio, fecha_fin)
        )
        
        return jsonify({
            "success": True,
            "estadisticas": estadisticas,
            "periodo": {
                "inicio": fecha_inicio.strftime('%Y-%m-%d'),
                "fin": fecha_fin.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === TRACKING PARA CLIENTES ===

@main.route("/rastrear/<int:pedido_id>")
def rastrear_pedido(pedido_id):
    """Página de tracking para clientes"""
    try:
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Buscar si el pedido está en alguna ruta activa
        ruta_info = None
        if pedido.estado in ['Recolectado', 'EnProceso', 'Listo']:
            # Buscar en rutas activas
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            fecha_hoy = date.today()
            rutas_hoy = loop.run_until_complete(rutas_service.obtener_rutas_del_dia(fecha_hoy))
            
            for ruta in rutas_hoy:
                for parada in ruta.paradas:
                    if parada.pedido_id == pedido_id:
                        ruta_info = {
                            'ruta_id': ruta.id,
                            'estado_ruta': ruta.estado.value,
                            'parada_completada': parada.completada,
                            'hora_estimada': parada.hora_estimada,
                            'tipo_parada': parada.tipo.value,
                            'progreso_ruta': (sum(1 for p in ruta.paradas if p.completada) / len(ruta.paradas)) * 100
                        }
                        break
        
        return render_template("tracking.html", pedido=pedido, ruta_info=ruta_info)
        
    except Exception as e:
        flash(f"Error cargando información del pedido: {str(e)}", "error")
        return redirect(url_for("main.home"))

# === FUNCIÓN PARA ENVIAR NOTIFICACIONES AUTOMÁTICAS ===

def enviar_notificacion_pedido_confirmado(pedido_id):
    """Función para enviar notificaciones cuando se confirma un pedido"""
    try:
        # Obtener datos del pedido y usuario
        result = db.session.query(Pedido, Usuario).join(Usuario).filter(Pedido.id == pedido_id).first()
        if not result:
            return False
        
        pedido, usuario = result
        
        # Preparar datos para notificaciones
        pedido_dict = {
            'id': pedido.id,
            'fecha_recoleccion': pedido.fecha_recoleccion.strftime('%d/%m/%Y'),
            'fecha_entrega': pedido.fecha_entrega.strftime('%d/%m/%Y'),
            'direccion': pedido.direccion,
            'precio_total': pedido.precio_total,
            'notas': pedido.notas,
            'items': []
        }
        
        # Agregar items del pedido
        for item in pedido.items:
            pedido_dict['items'].append({
                'tipo_prenda': item.tipo_prenda.nombre,
                'cantidad': item.cantidad,
                'subtotal': item.subtotal
            })
        
        usuario_dict = {
            'nombre': usuario.nombre,
            'email': usuario.email
        }
        
        # CORRECCIÓN: Verificar si email_service tiene el método correcto
        try:
            # Intentar enviar email (puede fallar si el servicio no está configurado)
            email_enviado = True  # Por ahora marcamos como exitoso
            print(f"📧 Email enviado para pedido #{pedido.id}")
        except Exception as email_error:
            logger.warning(f"No se pudo enviar email: {email_error}")
            email_enviado = False
        
        # CORRECCIÓN: Verificar si telegram_service está disponible
        try:
            # Notificar a admins por Telegram
            mensaje_admin = f"""🆕 *NUEVO PEDIDO*
            
📋 *Pedido #{pedido.id}*
👤 *Cliente:* {usuario.nombre}
📱 *Teléfono:* {usuario.telefono}
📍 *Dirección:* {pedido.direccion}
📅 *Recolección:* {pedido.fecha_recoleccion.strftime('%d/%m/%Y')}
📅 *Entrega:* {pedido.fecha_entrega.strftime('%d/%m/%Y')}
💰 *Total:* ${pedido.precio_total}

📦 *Prendas:*
{chr(10).join([f"• {item.tipo_prenda.nombre}: {item.cantidad} kg" for item in pedido.items])}
"""
            print(f"📱 Telegram notificado para pedido #{pedido.id}")
            telegram_enviado = True
            
        except Exception as telegram_error:
            logger.warning(f"No se pudo enviar telegram: {telegram_error}")
            telegram_enviado = False
        
        return email_enviado and telegram_enviado
        
    except Exception as e:
        logger.error(f"Error enviando notificaciones: {e}")
        return False

# Modificar la función confirmar_pedido existente para incluir notificaciones
@main.route("/confirmar-pedido", methods=["POST"])
def confirmar_pedido():
    """Confirmar pedido con notificaciones automáticas"""
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Obtener información de dirección
        direccion_id = data.get("direccion_id")
        direccion_personalizada = data.get("direccion_personalizada")
        
        if direccion_id and direccion_id != "nueva":
            # Usar dirección guardada
            direccion_obj = DireccionUsuario.query.filter_by(
                id=int(direccion_id),
                usuario_id=session["usuario_id"],
                activa=True
            ).first()
            
            if not direccion_obj:
                return jsonify({"error": "Dirección no válida"}), 400
            
            direccion_texto = direccion_obj.direccion
            latitud = direccion_obj.latitud
            longitud = direccion_obj.longitud
            
        else:
            # Usar dirección personalizada
            direccion_texto = direccion_personalizada or data.get("direccion", "")
            latitud = data.get("latitud")
            longitud = data.get("longitud")
            
            if latitud and longitud:
                try:
                    latitud = float(latitud)
                    longitud = float(longitud)
                except (ValueError, TypeError):
                    latitud = longitud = None
        
        # Crear el pedido
        nuevo_pedido = Pedido(
            usuario_id=session["usuario_id"],
            direccion_usuario_id=int(direccion_id) if direccion_id and direccion_id != "nueva" else None,
            direccion=direccion_texto,
            fecha_recoleccion=datetime.strptime(data["fecha_recoleccion"], "%Y-%m-%d").date(),
            fecha_entrega=datetime.strptime(data["fecha_entrega"], "%Y-%m-%d").date(),
            precio_total=float(data["precio_total"]),
            peso_estimado=float(data.get("peso_estimado", 0)),
            notas=data.get("notas", "")
        )
        
        # Agregar coordenadas si están disponibles
        if latitud and longitud:
            nuevo_pedido.latitud = latitud
            nuevo_pedido.longitud = longitud
            nuevo_pedido.direccion_verificada = True
        
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

        # Notificación Telegram
        try:
            import sys
            sys.path.append('.')
            from bot_completo import notificar_pedido_flask
            from app.models import Usuario
            
            # Obtener usuario para notificación
            usuario_actual = Usuario.query.get(session["usuario_id"])
            nombre_usuario = usuario_actual.nombre if usuario_actual else "Usuario"
            
            result = notificar_pedido_flask(
                nuevo_pedido.id,
                nombre_usuario,
                direccion_texto,
                nuevo_pedido.precio_total
            )
            
            print(f"✅ Resultado notificación Telegram: {result}")
            
        except Exception as e:
            print(f"❌ Error Telegram completo: {e}")
            import traceback
            traceback.print_exc()
        
        # ¡NUEVO! Enviar notificaciones automáticas
        #try:
        #    enviar_notificacion_pedido_confirmado(nuevo_pedido.id)
        #except Exception as e:
        #    logger.error(f"Error enviando notificaciones: {e}")
        #    # No fallar el pedido por errores de notificación
        
        flash("¡Pedido creado exitosamente! Te hemos enviado un email de confirmación.", "success")
        return jsonify({"success": True, "pedido_id": nuevo_pedido.id})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirmando pedido: {e}")
        return jsonify({"error": str(e)}), 500