# Bodega 5400

Sistema web en Python/Flask para controlar productos activos en bodega, registrar ingresos, registrar egresos y mantener el stock disponible. Está preparado para desplegarse en Render.com con PostgreSQL.

## Funcionalidades incluidas

- Dashboard con estética roja/naranja inspirada en la referencia entregada.
- Logos Aramark y Escondida | BHP integrados en el encabezado.
- Dashboard con conclusiones automáticas y gráficos:
  - Tendencia de ingresos vs egresos de los últimos 14 días.
  - Stock disponible por familia.
  - Alertas por stock mínimo y productos sin stock.
- Carga inicial de productos del cuadro enviado.
- Alta de nuevos productos activos.
- Registro de productos por pistoleo del código:
  - En el formulario de producto, haz clic en **Código** y pistolea.
  - Si el código ya existe, el sistema muestra el producto y evita duplicarlo.
  - Si el código está disponible, permite completar los datos y guardarlo.
- Eliminación lógica de productos activos, conservando historial.
- Registro manual de ingresos y egresos por producto.
- Pistoleo operativo para ingresos o egresos automáticos.
- Administración de operadores del servicio.
- Cada ingreso o egreso guarda el operador responsable.
- Validación para impedir egresos superiores al stock disponible.
- Historial de movimientos con filtros por producto, operador, tipo u observación.
- Exportación CSV de productos y movimientos, incluyendo operador responsable.
- Configuración lista para Render.com con `render.yaml`, `Procfile`, `requirements.txt` y `gunicorn`.

## Menú principal

- **Dashboard:** resumen operativo, conclusiones y gráficos.
- **Productos:** listado y registro de productos activos.
- **Pistoleo:** ingreso o egreso por lector de código de barras.
- **Operadores:** alta y desactivación de operadores del servicio.
- **Movimientos:** historial trazable de ingresos y egresos.
- **Productos CSV:** descarga el inventario actual.
- **Movimientos CSV:** descarga el historial de movimientos.

## Uso del pistoleo

El lector debe estar configurado como teclado/HID y enviar **Enter** al terminar la lectura.

### Para registrar producto nuevo

1. Entra al Dashboard.
2. En **Agregar producto activo**, haz clic en el campo **Código**.
3. Pistolea el producto.
4. El sistema valida el código:
   - Si no existe, permite completar familia, descripción, talla, stock inicial y mínimo.
   - Si existe, muestra el producto ya registrado para evitar duplicados.
5. Guarda el producto.

### Para ingresar o descontar stock

1. Entra a **Pistoleo**.
2. Selecciona **Ingreso** o **Egreso**.
3. Indica cantidad por pistoleo.
4. Selecciona el operador del servicio.
5. Pistolea el código.
6. El sistema reconoce el producto, actualiza stock y guarda el movimiento.

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
    ├── scanner.html
    ├── operators.html
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
2. Crea un Web Service desde tu repositorio.
3. Usa:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

4. Agrega variables de entorno:

```text
DATABASE_URL=<connection string de PostgreSQL>
SECRET_KEY=<clave segura>
PYTHON_VERSION=3.11.9
```

## Nota sobre actualización desde una versión anterior

El archivo `app.py` incluye una migración ligera para agregar la columna `operator_id` a la tabla `movements` si la base ya existía. También corrige códigos semilla antiguos que quedaron sin ceros intermedios.

## Ajuste de reconocimiento de códigos

Esta versión normaliza los códigos leídos por pistola antes de buscarlos:

- Elimina espacios, Enter, tabuladores y caracteres invisibles.
- Quita separadores agregados accidentalmente por el lector.
- Convierte letras a mayúscula.
- Corrige códigos que llegan desde Excel con terminación `.0`.
- Compara contra códigos guardados aunque existan diferencias menores de formato.

Esto permite que un código ya existente sea reconocido tanto en **Agregar producto activo** como en **Pistoleo**.
