import csv
import io
import os
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Flask, Response, flash, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, or_, text


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


class Operator(db.Model):
    __tablename__ = "operators"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True, index=True)
    cargo = db.Column(db.String(120), default="")
    turno = db.Column(db.String(80), default="")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimientos = db.relationship("Movement", backref="operador", lazy=True)

    @property
    def etiqueta(self):
        partes = [self.nombre]
        extras = " / ".join([x for x in [self.cargo, self.turno] if x])
        if extras:
            partes.append(f"({extras})")
        return " ".join(partes)


class Movement(db.Model):
    __tablename__ = "movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey("operators.id"), nullable=True, index=True)
    tipo = db.Column(db.String(20), nullable=False)  # ingreso | egreso
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_nuevo = db.Column(db.Integer, nullable=False)
    observacion = db.Column(db.String(250), default="")
    responsable = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    @property
    def responsable_visible(self):
        if self.operador:
            return self.operador.nombre
        return self.responsable or "No informado"


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
        ensure_schema_updates()
        seed_initial_products()
        normalize_seed_codes()

    return app


def parse_positive_int(value, default=0):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def ensure_schema_updates():
    """Pequeña migración segura para Render sin usar Alembic.

    db.create_all() crea tablas nuevas, pero no agrega columnas en tablas existentes.
    Esta función permite que una base antigua incorpore operator_id en movements.
    """
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    if "operators" not in table_names:
        Operator.__table__.create(db.engine, checkfirst=True)

    if "movements" in table_names:
        movement_columns = {column["name"] for column in inspector.get_columns("movements")}
        if "operator_id" not in movement_columns:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE movements ADD COLUMN operator_id INTEGER"))


def seed_initial_products():
    if Product.query.count() > 0:
        return

    initial_products = [
        ("Guantes", "50101300060010", "Ninja Multi-Tech (Naranjos)", "XL", 0),
        ("Guantes", "50101300060009", "Ninja Multi-Tech (Naranjos)", "L", 0),
        ("Guantes", "50101300060007", "Ninja Multi-Tech (Naranjos)", "S", 0),
        ("Guantes", "7798145206465", "Guantes Nitrilo verde", "S", 0),
        ("Guantes", "7798145201255", "Guantes Nitrilo verde", "M", 0),
        ("Guantes", "7798145206489", "Guantes Nitrilo verde", "L", 0),
        ("Guantes", "7798145209787", "Guantes Nitrilo verde", "XS", 0),
        ("Guantes", "713740374477", "Guantes Showa Amarillo", "S", 0),
        ("Guantes", "713740374491", "Guantes Showa Amarillo", "L", 0),
        ("Guantes", "50103000000006", "Guantes ninja negro", "XS", 0),
        ("Guantes", "50103000000007", "Guantes ninja negro", "S", 0),
        ("Guantes", "50103000000008", "Guantes ninja negro", "M", 0),
        ("Guantes", "50103000000009", "Guantes ninja negro", "L", 0),
        ("Guantes", "50103000000010", "Guantes ninja negro", "XL", 0),
        ("Guantes", "5010930089000", "Ninja Razar (manguilla Kevlar amarilla)", "Única", 0),
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



def normalize_seed_codes():
    """Corrige códigos semilla de versiones antiguas que quedaron sin ceros intermedios."""
    corrections = {
        "5010130006010": "50101300060010",
        "5010130006009": "50101300060009",
        "5010130006007": "50101300060007",
        "5010300000006": "50103000000006",
        "5010300000007": "50103000000007",
        "5010300000008": "50103000000008",
        "5010300000009": "50103000000009",
        "5010300000010": "50103000000010",
    }
    changed = False
    for old_code, new_code in corrections.items():
        product = Product.query.filter_by(codigo=old_code).first()
        target = Product.query.filter_by(codigo=new_code).first()
        if product and not target:
            product.codigo = new_code
            changed = True
    if changed:
        db.session.commit()

def active_operators():
    return Operator.query.filter_by(activo=True).order_by(Operator.nombre.asc()).all()


def resolve_operator_from_form(form):
    operator_id = parse_positive_int(form.get("operator_id"), 0)
    operator = None
    if operator_id > 0:
        operator = Operator.query.filter_by(id=operator_id, activo=True).first()
    responsable_manual = str(form.get("responsable", "")).strip()
    return operator, responsable_manual


def product_payload(product):
    return {
        "id": product.id,
        "familia": product.familia,
        "codigo": product.codigo,
        "descripcion": product.descripcion,
        "talla": product.talla or "—",
        "stock": product.stock,
        "stock_minimo": product.stock_minimo,
        "estado_stock": product.estado_stock,
        "activo": product.activo,
    }


def build_dashboard_data(productos_activos):
    total_stock = sum(p.stock for p in productos_activos)
    stock_bajo = sum(1 for p in productos_activos if p.stock_minimo > 0 and p.stock <= p.stock_minimo)
    sin_stock = sum(1 for p in productos_activos if p.stock <= 0)

    today = datetime.utcnow().date()
    start_day = today - timedelta(days=13)
    start_dt = datetime.combine(start_day, datetime.min.time())

    movimientos_14 = Movement.query.filter(Movement.created_at >= start_dt).order_by(Movement.created_at.asc()).all()
    ingresos_by_day = defaultdict(int)
    egresos_by_day = defaultdict(int)

    for movement in movimientos_14:
        key = movement.created_at.date().isoformat()
        if movement.tipo == "ingreso":
            ingresos_by_day[key] += movement.cantidad
        elif movement.tipo == "egreso":
            egresos_by_day[key] += movement.cantidad

    trend_labels = []
    ingresos = []
    egresos = []
    for offset in range(14):
        day = start_day + timedelta(days=offset)
        key = day.isoformat()
        trend_labels.append(day.strftime("%d/%m"))
        ingresos.append(ingresos_by_day[key])
        egresos.append(egresos_by_day[key])

    family_stock = defaultdict(int)
    family_count = defaultdict(int)
    for product in productos_activos:
        family_stock[product.familia] += product.stock
        family_count[product.familia] += 1

    families_sorted = sorted(family_stock.items(), key=lambda item: item[1], reverse=True)[:8]
    family_chart = {
        "labels": [item[0] for item in families_sorted] or ["Sin datos"],
        "values": [item[1] for item in families_sorted] or [0],
    }

    movimientos_hoy = Movement.query.filter(Movement.created_at >= datetime.combine(today, datetime.min.time())).count()
    movimientos_semana = Movement.query.filter(Movement.created_at >= datetime.utcnow() - timedelta(days=7)).count()
    ingresos_semana = db.session.query(db.func.coalesce(db.func.sum(Movement.cantidad), 0)).filter(
        Movement.tipo == "ingreso",
        Movement.created_at >= datetime.utcnow() - timedelta(days=7),
    ).scalar() or 0
    egresos_semana = db.session.query(db.func.coalesce(db.func.sum(Movement.cantidad), 0)).filter(
        Movement.tipo == "egreso",
        Movement.created_at >= datetime.utcnow() - timedelta(days=7),
    ).scalar() or 0

    producto_menor_stock = None
    if productos_activos:
        producto_menor_stock = min(productos_activos, key=lambda p: (p.stock, p.descripcion, p.talla or ""))

    familia_mayor_stock = families_sorted[0][0] if families_sorted else "Sin datos"
    stock_familia_mayor = families_sorted[0][1] if families_sorted else 0

    operador_top = (
        db.session.query(Operator.nombre, db.func.count(Movement.id).label("total"))
        .join(Movement, Movement.operator_id == Operator.id)
        .filter(Movement.created_at >= datetime.utcnow() - timedelta(days=30))
        .group_by(Operator.nombre)
        .order_by(text("total DESC"))
        .first()
    )

    conclusions = [
        f"Productos activos registrados: {len(productos_activos)}.",
        f"Stock total disponible: {total_stock} unidades.",
        f"Familia con mayor stock: {familia_mayor_stock} ({stock_familia_mayor} unidades).",
        f"Alertas por stock mínimo o sin stock: {stock_bajo + sin_stock}.",
    ]
    if producto_menor_stock:
        conclusions.append(
            f"Producto con menor stock: {producto_menor_stock.descripcion} {producto_menor_stock.talla or ''} "
            f"({producto_menor_stock.stock} unidades)."
        )
    if operador_top:
        conclusions.append(f"Operador con más movimientos últimos 30 días: {operador_top.nombre} ({operador_top.total}).")

    return {
        "total_stock": total_stock,
        "stock_bajo": stock_bajo,
        "sin_stock": sin_stock,
        "movimientos_hoy": movimientos_hoy,
        "movimientos_semana": movimientos_semana,
        "ingresos_semana": int(ingresos_semana),
        "egresos_semana": int(egresos_semana),
        "trend_chart": {"labels": trend_labels, "ingresos": ingresos, "egresos": egresos},
        "family_chart": family_chart,
        "conclusions": conclusions,
    }


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
        dashboard = build_dashboard_data(productos_activos)
        movimientos_recientes = Movement.query.order_by(Movement.created_at.desc()).limit(8).all()

        return render_template(
            "index.html",
            productos=productos,
            search=search,
            stock_filter=stock_filter,
            total_productos=len(productos_activos),
            operadores=active_operators(),
            movimientos_recientes=movimientos_recientes,
            **dashboard,
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
            return redirect(url_for("index", _anchor="nuevo-producto"))

        existing = Product.query.filter_by(codigo=codigo).first()
        if existing and existing.activo:
            flash(
                f"El código ya existe: {existing.descripcion} {existing.talla or ''}. No se duplicó el producto.",
                "error",
            )
            return redirect(url_for("index", q=codigo, _anchor="productos"))

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
        return redirect(url_for("index", q=codigo, _anchor="productos"))

    @app.route("/productos/<int:product_id>/eliminar", methods=["POST"])
    def delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        product.activo = False
        db.session.commit()
        flash("Producto eliminado de activos. Sus movimientos históricos se conservan.", "success")
        return redirect(url_for("index", _anchor="productos"))

    @app.route("/productos/<int:product_id>/movimiento", methods=["POST"])
    def register_movement(product_id):
        product = Product.query.get_or_404(product_id)
        if not product.activo:
            flash("No se puede registrar movimiento sobre un producto inactivo.", "error")
            return redirect(url_for("index", _anchor="productos"))

        tipo = request.form.get("tipo", "").strip().lower()
        cantidad = parse_positive_int(request.form.get("cantidad"), 0)
        observacion = request.form.get("observacion", "").strip()
        operator, responsable_manual = resolve_operator_from_form(request.form)
        responsable = operator.nombre if operator else responsable_manual

        if tipo not in {"ingreso", "egreso"}:
            flash("Tipo de movimiento inválido.", "error")
            return redirect(url_for("index", _anchor="productos"))
        if cantidad <= 0:
            flash("La cantidad debe ser mayor que cero.", "error")
            return redirect(url_for("index", _anchor="productos"))
        if not responsable:
            flash("Debes seleccionar o escribir el operador responsable del movimiento.", "error")
            return redirect(url_for("index", _anchor="productos"))
        if tipo == "egreso" and cantidad > product.stock:
            flash("Egreso rechazado: la cantidad supera el stock disponible.", "error")
            return redirect(url_for("index", _anchor="productos"))

        stock_anterior = product.stock
        product.stock = product.stock + cantidad if tipo == "ingreso" else product.stock - cantidad
        movement = Movement(
            product_id=product.id,
            operator_id=operator.id if operator else None,
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
        return redirect(url_for("index", q=product.codigo, _anchor="productos"))

    @app.route("/api/productos/lookup")
    def api_product_lookup():
        codigo = request.args.get("codigo", "").strip()
        if not codigo:
            return jsonify(ok=False, message="Código vacío."), 400

        product = Product.query.filter_by(codigo=codigo).first()
        if not product:
            return jsonify(ok=True, exists=False, codigo=codigo, message="Código disponible para registrar producto nuevo.")

        return jsonify(
            ok=True,
            exists=True,
            product=product_payload(product),
            message="Código reconocido en inventario." if product.activo else "Código existe, pero está inactivo. Al guardar se reactivará.",
        )

    @app.route("/pistoleo")
    def scanner():
        productos_activos = Product.query.filter_by(activo=True).count()
        total_stock = sum(p.stock for p in Product.query.filter_by(activo=True).all())
        return render_template(
            "scanner.html",
            productos_activos=productos_activos,
            total_stock=total_stock,
            operadores=active_operators(),
        )

    @app.route("/api/pistoleo", methods=["POST"])
    def api_scanner_movement():
        data = request.get_json(silent=True) or request.form
        codigo = str(data.get("codigo", "")).strip()
        tipo = str(data.get("tipo", "")).strip().lower()
        cantidad = parse_positive_int(data.get("cantidad"), 1)
        operator, responsable_manual = resolve_operator_from_form(data)
        responsable = operator.nombre if operator else responsable_manual
        observacion = str(data.get("observacion", "")).strip()

        if not codigo:
            return jsonify(ok=False, message="Debes pistolear o ingresar un código."), 400
        if tipo not in {"ingreso", "egreso"}:
            return jsonify(ok=False, message="Selecciona si el pistoleo será ingreso o egreso."), 400
        if cantidad <= 0:
            return jsonify(ok=False, message="La cantidad por pistoleo debe ser mayor que cero."), 400
        if not responsable:
            return jsonify(ok=False, message="Selecciona o escribe el operador responsable."), 400

        product = Product.query.filter_by(codigo=codigo, activo=True).first()
        if not product:
            return jsonify(
                ok=False,
                code="not_found",
                codigo=codigo,
                message=f"Código {codigo} no encontrado en productos activos.",
            ), 404

        if tipo == "egreso" and cantidad > product.stock:
            return jsonify(
                ok=False,
                code="insufficient_stock",
                codigo=codigo,
                product=product_payload(product),
                message=f"Egreso rechazado: stock disponible {product.stock}, cantidad solicitada {cantidad}.",
            ), 409

        stock_anterior = product.stock
        product.stock = product.stock + cantidad if tipo == "ingreso" else product.stock - cantidad
        movement = Movement(
            product_id=product.id,
            operator_id=operator.id if operator else None,
            tipo=tipo,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_nuevo=product.stock,
            observacion=observacion or "Movimiento registrado desde pistoleo",
            responsable=responsable,
        )
        db.session.add(movement)
        db.session.commit()

        return jsonify(
            ok=True,
            message="Producto reconocido y movimiento registrado.",
            movement={
                "id": movement.id,
                "tipo": movement.tipo,
                "cantidad": movement.cantidad,
                "stock_anterior": movement.stock_anterior,
                "stock_nuevo": movement.stock_nuevo,
                "fecha": movement.created_at.strftime("%d-%m-%Y %H:%M"),
                "responsable": movement.responsable_visible,
            },
            product=product_payload(product),
        )

    @app.route("/operadores", methods=["GET", "POST"])
    def operators():
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            cargo = request.form.get("cargo", "").strip()
            turno = request.form.get("turno", "").strip()

            if not nombre:
                flash("El nombre del operador es obligatorio.", "error")
                return redirect(url_for("operators"))

            existing = Operator.query.filter(db.func.lower(Operator.nombre) == nombre.lower()).first()
            if existing and existing.activo:
                flash("Ese operador ya está activo.", "error")
                return redirect(url_for("operators"))
            if existing and not existing.activo:
                existing.cargo = cargo
                existing.turno = turno
                existing.activo = True
                flash("Operador reactivado correctamente.", "success")
            else:
                db.session.add(Operator(nombre=nombre, cargo=cargo, turno=turno, activo=True))
                flash("Operador agregado correctamente.", "success")

            db.session.commit()
            return redirect(url_for("operators"))

        operadores_activos = Operator.query.filter_by(activo=True).order_by(Operator.nombre.asc()).all()
        operadores_inactivos = Operator.query.filter_by(activo=False).order_by(Operator.nombre.asc()).all()
        return render_template("operators.html", operadores=operadores_activos, operadores_inactivos=operadores_inactivos)

    @app.route("/operadores/<int:operator_id>/eliminar", methods=["POST"])
    def delete_operator(operator_id):
        operator = Operator.query.get_or_404(operator_id)
        operator.activo = False
        db.session.commit()
        flash("Operador desactivado. Sus movimientos históricos se conservan.", "success")
        return redirect(url_for("operators"))

    @app.route("/movimientos")
    def movements():
        search = request.args.get("q", "").strip()
        tipo = request.args.get("tipo", "todos")
        query = Movement.query.join(Product).outerjoin(Operator)

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
                    Operator.nombre.ilike(like),
                )
            )

        movimientos = query.order_by(Movement.created_at.desc()).limit(250).all()
        return render_template("movements.html", movimientos=movimientos, search=search, tipo=tipo)

    @app.route("/export/productos.csv")
    def export_products_csv():
        productos = Product.query.filter_by(activo=True).order_by(Product.familia, Product.descripcion, Product.talla).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["familia", "codigo", "descripcion", "talla", "stock", "stock_minimo", "estado"])
        for p in productos:
            writer.writerow([p.familia, p.codigo, p.descripcion, p.talla, p.stock, p.stock_minimo, p.estado_stock])

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
            "operador",
            "responsable_manual",
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
                m.operador.nombre if m.operador else "",
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
