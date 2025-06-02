from flask import Blueprint, render_template, request, redirect, url_for
from .models import Pedido
from . import db
from datetime import datetime

main = Blueprint("main", __name__)

@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nombre = request.form["nombre"]
        direccion = request.form["direccion"]
        fecha_recoleccion = datetime.strptime(request.form["fecha_recoleccion"], "%Y-%m-%d")
        fecha_entrega = datetime.strptime(request.form["fecha_entrega"], "%Y-%m-%d")
        notas = request.form.get("notas")

        nuevo_pedido = Pedido(
            nombre=nombre,
            direccion=direccion,
            fecha_recoleccion=fecha_recoleccion,
            fecha_entrega=fecha_entrega,
            notas=notas
        )

        db.session.add(nuevo_pedido)
        db.session.commit()
        return redirect(url_for("main.index"))

    pedidos = Pedido.query.order_by(Pedido.creado.desc()).all()
    return render_template("index.html", pedidos=pedidos)
