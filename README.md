# Bodega 5400

Sistema web en Python/Flask para controlar productos activos en bodega, registrar ingresos, registrar egresos y mantener el stock disponible.

## Funcionalidades incluidas

- Dashboard con estética roja/naranja inspirada en la referencia entregada.
- Logos Aramark y Escondida | BHP integrados en el encabezado.
- Carga inicial de los productos del cuadro enviado.
- Alta de nuevos productos activos.
- Eliminación lógica de productos activos, conservando historial.
- Registro de ingresos y egresos por producto.
- Validación para impedir egresos superiores al stock disponible.
- Historial de movimientos con filtros.
- Exportación CSV de productos y movimientos.
- Configuración lista para Render.com con `render.yaml`, `Procfile`, `requirements.txt` y `gunicorn`.

## Estructura

```text
bodega_5400/
├── app.py
├── .python-version
├── runtime.txt
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
├── data/productos_iniciales.csv
├── static/
│   ├── css/styles.css
│   ├── js/app.js
│   └── img/
│       ├── aramark.png
│       └── escondida_bhp.png
└── templates/
    ├── base.html
    ├── index.html
    └── movements.html
```

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Luego abre:

```text
http://localhost:5000
```

En local, si no existe `DATABASE_URL`, la aplicación usa SQLite automáticamente en `instance/bodega_5400.db`.


## Corrección importante para Render

El proyecto incluye `.python-version` con `3.11.9` para evitar que Render use Python 3.14 por defecto. En despliegues manuales, confirma también esta variable en **Environment**:

```text
PYTHON_VERSION=3.11.9
```

Si Render ya había creado el servicio antes de agregar esta variable o el archivo `.python-version`, ejecuta **Clear build cache & deploy** para que reconstruya el entorno virtual con Python 3.11.9.

## Despliegue en Render.com

### Opción A: Blueprint

1. Sube este proyecto a GitHub.
2. En Render, selecciona **New +** → **Blueprint**.
3. Conecta el repositorio.
4. Render leerá `render.yaml`, creará el servicio web y una base PostgreSQL.

### Opción B: Web Service manual

1. Crea una base PostgreSQL en Render.
2. Crea un Web Service desde el repositorio.
3. Usa:

```bash
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

4. Agrega variables de entorno:

```text
PYTHON_VERSION=3.11.9
SECRET_KEY=una-clave-segura
DATABASE_URL=<connection string de PostgreSQL en Render>
```

La app convierte automáticamente URLs `postgres://` a `postgresql://`, por compatibilidad con SQLAlchemy.

## Campos del producto

- Familia
- Código
- Descripción
- Talla
- Stock
- Stock mínimo
- Activo/Inactivo

## Nota de persistencia

Para Render se recomienda usar PostgreSQL mediante `DATABASE_URL`. SQLite funciona para pruebas locales, pero no es lo recomendable para producción en servicios efímeros.
