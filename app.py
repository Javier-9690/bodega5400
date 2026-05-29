import csv
import io
import os
from datetime import datetime, timedelta, timezone

from flask import Flask, Response, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_


db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    familia = db.Column(db.String(80), nullable=False)
    codigo = db.Column(db.String(80), nullable=False, unique=True, index=True)
    descripcion = db.Column(db.String(220), nullable=False)
    talla = db.Column(db.String(40), default="")
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimientos = db.relationship("Movement", backref="producto", lazy=True, cascade="all, delete-orphan")

    @property
    def estado_stock(self):
        if self.stock <= 0:
            return "sin-stock"
        if self.stock_minimo > 0 and self.stock <= self.stock_minimo:
            return "stock-bajo"
        return "ok"


class Movement(db.Model):
    __tablename__ = "movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False)  # ingreso | egreso
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_nuevo = db.Column(db.Integer, nullable=False)
    observacion = db.Column(db.String(250), default="")
    responsable = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-render")

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Render puede entregar la URL con el esquema postgres://.
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bodega_5400.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    register_routes(app)

    with app.app_context():
        db.create_all()
        seed_initial_products()

    return app


def parse_positive_int(value, default=0):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def seed_initial_products():
    if Product.query.count() > 0:
        return

    initial_products = [
        ("Guantes", "5010130006010", "Ninja Multi-Tech (Naranjos)", "XL", 0),
        ("Guantes", "5010130006009", "Ninja Multi-Tech (Naranjos)", "L", 0),
        ("Guantes", "5010130006007", "Ninja Multi-Tech (Naranjos)", "S", 0),
        ("Guantes", "7798145206465", "Guantes Nitrilo verde", "S", 0),
        ("Guantes", "7798145201255", "Guantes Nitrilo verde", "M", 0),
        ("Guantes", "7798145206489", "Guantes Nitrilo verde", "L", 0),
        ("Guantes", "7798145209787", "Guantes Nitrilo verde", "XS", 0),
        ("Guantes", "713740374477", "Guantes Showa Amarillo", "S", 0),
        ("Guantes", "713740374491", "Guantes Showa Amarillo", "L", 0),
        ("Guantes", "5010300000006", "Guantes ninja negro", "XS", 0),
        ("Guantes", "5010300000007", "Guantes ninja negro", "S", 0),
        ("Guantes", "5010300000008", "Guantes ninja negro", "M", 0),
        ("Guantes", "5010300000009", "Guantes ninja negro", "L", 0),
        ("Guantes", "5010300000010", "Guantes ninja negro", "XL", 0),
        ("Guantes", "5010930089000", "Ninja Razar (manguilla Kevlar amarilla)", "", 0),
    ]

    for familia, codigo, descripcion, talla, stock in initial_products:
        db.session.add(
            Product(
                familia=familia,
                codigo=codigo,
                descripcion=descripcion,
                talla=talla,
                stock=stock,
                stock_minimo=0,
                activo=True,
            )
        )
    db.session.commit()


def register_routes(app):
    @app.route("/healthz")
    def healthz():
        return {"status": "ok", "service": "Bodega 5400"}

    @app.route("/")
    def index():
        search = request.args.get("q", "").strip()
        stock_filter = request.args.get("stock", "todos")

        query = Product.query.filter_by(activo=True)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Product.familia.ilike(like),
                    Product.codigo.ilike(like),
                    Product.descripcion.ilike(like),
                    Product.talla.ilike(like),
                )
            )

        productos = query.order_by(Product.familia.asc(), Product.descripcion.asc(), Product.talla.asc()).all()

        if stock_filter == "sin-stock":
            productos = [p for p in productos if p.stock <= 0]
        elif stock_filter == "bajo":
            productos = [p for p in productos if p.stock_minimo > 0 and p.stock <= p.stock_minimo]
        elif stock_filter == "disponible":
            productos = [p for p in productos if p.stock > 0]

        productos_activos = Product.query.filter_by(activo=True).all()
        total_stock = sum(p.stock for p in productos_activos)
        stock_bajo = sum(1 for p in productos_activos if p.stock_minimo > 0 and p.stock <= p.stock_minimo)
        sin_stock = sum(1 for p in productos_activos if p.stock <= 0)
        desde_semana = datetime.utcnow() - timedelta(days=7)
        movimientos_semana = Movement.query.filter(Movement.created_at >= desde_semana).count()
        movimientos_recientes = Movement.query.order_by(Movement.created_at.desc()).limit(10).all()

        return render_template(
            "index.html",
            productos=productos,
            search=search,
            stock_filter=stock_filter,
            total_productos=len(productos_activos),
            total_stock=total_stock,
            stock_bajo=stock_bajo,
            sin_stock=sin_stock,
            movimientos_semana=movimientos_semana,
            movimientos_recientes=movimientos_recientes,
        )

    @app.route("/productos", methods=["POST"])
    def add_product():
        familia = request.form.get("familia", "").strip()
        codigo = request.form.get("codigo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        talla = request.form.get("talla", "").strip().upper()
        stock = parse_positive_int(request.form.get("stock"), 0)
        stock_minimo = parse_positive_int(request.form.get("stock_minimo"), 0)

        if not familia or not codigo or not descripcion:
            flash("Familia, código y descripción son obligatorios.", "error")
            return redirect(url_for("index"))

        existing = Product.query.filter_by(codigo=codigo).first()
        if existing and existing.activo:
            flash("Ya existe un producto activo con ese código.", "error")
            return redirect(url_for("index"))

        if existing and not existing.activo:
            existing.familia = familia
            existing.descripcion = descripcion
            existing.talla = talla
            existing.stock = stock
            existing.stock_minimo = stock_minimo
            existing.activo = True
            flash("Producto reactivado correctamente.", "success")
        else:
            db.session.add(
                Product(
                    familia=familia,
                    codigo=codigo,
                    descripcion=descripcion,
                    talla=talla,
                    stock=stock,
                    stock_minimo=stock_minimo,
                    activo=True,
                )
            )
            flash("Producto agregado correctamente.", "success")

        db.session.commit()
        return redirect(url_for("index"))

    @app.route("/productos/<int:product_id>/eliminar", methods=["POST"])
    def delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        product.activo = False
        db.session.commit()
        flash("Producto eliminado de activos. Sus movimientos históricos se conservan.", "success")
        return redirect(url_for("index"))

    @app.route("/productos/<int:product_id>/movimiento", methods=["POST"])
    def register_movement(product_id):
        product = Product.query.get_or_404(product_id)
        if not product.activo:
            flash("No se puede registrar movimiento sobre un producto inactivo.", "error")
            return redirect(url_for("index"))

        tipo = request.form.get("tipo", "").strip().lower()
        cantidad = parse_positive_int(request.form.get("cantidad"), 0)
        observacion = request.form.get("observacion", "").strip()
        responsable = request.form.get("responsable", "").strip()

        if tipo not in {"ingreso", "egreso"}:
            flash("Tipo de movimiento inválido.", "error")
            return redirect(url_for("index"))
        if cantidad <= 0:
            flash("La cantidad debe ser mayor que cero.", "error")
            return redirect(url_for("index"))
        if tipo == "egreso" and cantidad > product.stock:
            flash("Egreso rechazado: la cantidad supera el stock disponible.", "error")
            return redirect(url_for("index"))

        stock_anterior = product.stock
        product.stock = product.stock + cantidad if tipo == "ingreso" else product.stock - cantidad
        movement = Movement(
            product_id=product.id,
            tipo=tipo,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=product.stock,
            observacion=observacion,
            responsable=responsable,
        )
        db.session.add(movement)
        db.session.commit()
        flash("Movimiento registrado correctamente.", "success")
        return redirect(url_for("index"))

    @app.route("/movimientos")
    def movements():
        search = request.args.get("q", "").strip()
        tipo = request.args.get("tipo", "todos")
        query = Movement.query.join(Product)

        if tipo in {"ingreso", "egreso"}:
            query = query.filter(Movement.tipo == tipo)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Product.codigo.ilike(like),
                    Product.descripcion.ilike(like),
                    Product.familia.ilike(like),
                    Movement.responsable.ilike(like),
                    Movement.observacion.ilike(like),
                )
            )

        movimientos = query.order_by(Movement.created_at.desc()).limit(250).all()
        return render_template("movements.html", movimientos=movimientos, search=search, tipo=tipo)

    @app.route("/export/productos.csv")
    def export_products_csv():
        productos = Product.query.filter_by(activo=True).order_by(Product.familia, Product.descripcion, Product.talla).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["familia", "codigo", "descripcion", "talla", "stock", "stock_minimo"])
        for p in productos:
            writer.writerow([p.familia, p.codigo, p.descripcion, p.talla, p.stock, p.stock_minimo])

        return Response(
            output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=bodega_5400_productos.csv"},
        )

    @app.route("/export/movimientos.csv")
    def export_movements_csv():
        movimientos = Movement.query.order_by(Movement.created_at.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "fecha_utc",
            "tipo",
            "cantidad",
            "stock_anterior",
            "stock_nuevo",
            "familia",
            "codigo",
            "descripcion",
            "talla",
            "responsable",
            "observacion",
        ])
        for m in movimientos:
            p = m.producto
            writer.writerow([
                m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                m.tipo,
                m.cantidad,
                m.stock_anterior,
                m.stock_nuevo,
                p.familia,
                p.codigo,
                p.descripcion,
                p.talla,
                m.responsable,
                m.observacion,
            ])

        return Response(
            output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=bodega_5400_movimientos.csv"},
        )

    @app.template_filter("fecha")
    def format_date(value):
        if not value:
            return ""
        return value.strftime("%d-%m-%Y %H:%M")


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
