# Manual de Usuario Profesional — Bodega 5400

## 1. Objetivo del sistema

**Bodega 5400** es un sistema web de control de inventario diseñado para registrar productos activos de bodega, controlar ingresos y egresos, consultar stock disponible, revisar trazabilidad por operador y descargar reportes CSV para análisis o respaldo.

El sistema está preparado para operar con lector de código de barras tipo teclado/HID, por lo que el usuario puede “pistolear” productos para registrar movimientos o capturar códigos al crear productos nuevos.

---

## 2. Acceso al sistema

El sistema requiere inicio de sesión para acceder a cualquier módulo operativo.

### Usuarios iniciales

| Usuario | Clave inicial |
|---|---|
| Ignacio Pino | Ignacio2026 |
| Jorge Apaz | Jorge2026 |

> Recomendación operacional: cambiar la clave inicial después del primer ingreso.

### Iniciar sesión

1. Abrir la URL del sistema en Render.
2. Ingresar el usuario autorizado.
3. Ingresar la clave correspondiente.
4. Presionar **Entrar al sistema**.

Si las credenciales son correctas, el sistema abrirá el **Dashboard**.

---

## 3. Cambio de clave

Cada usuario puede cambiar su propia clave desde el menú superior.

### Procedimiento

1. Ingresar al sistema.
2. Presionar **Cambiar clave**.
3. Escribir la clave actual.
4. Escribir la nueva clave.
5. Confirmar la nueva clave.
6. Presionar **Guardar nueva clave**.

### Reglas

- La nueva clave debe tener al menos 8 caracteres.
- La confirmación debe coincidir con la nueva clave.
- Una vez cambiada, la clave inicial deja de funcionar para ese usuario.

---

## 4. Menú principal

### Dashboard

Muestra el estado general del inventario mediante indicadores, conclusiones automáticas y gráficos.

Incluye:

- Productos activos.
- Stock total disponible.
- Productos bajo mínimo.
- Productos sin stock.
- Movimientos del día.
- Conclusiones automáticas.
- Gráfico de ingresos versus egresos.
- Gráfico de stock por familia.

### Productos

Permite administrar los productos activos de la bodega.

Desde esta sección se puede:

- Buscar productos por código, descripción, familia o talla.
- Registrar productos nuevos.
- Pistolear un código para cargarlo automáticamente en el formulario.
- Validar si un código ya existe antes de guardar.
- Registrar movimientos directos sobre un producto.
- Eliminar productos de la lista activa.
- Descargar el inventario en formato CSV.

### Pistoleo

Permite registrar ingresos o egresos mediante lector de código de barras.

El lector debe funcionar como teclado y enviar **Enter** después de la lectura.

### Operadores

Permite registrar y administrar operadores del servicio.

Los operadores se usan para dejar trazabilidad de quién realizó un ingreso o egreso.

### Movimientos

Muestra el historial de ingresos y egresos registrados.

Desde esta sección se puede:

- Filtrar por tipo de movimiento.
- Buscar por código, producto, familia, operador u observación.
- Revisar stock anterior y stock nuevo.
- Descargar el historial en formato CSV.

---

## 5. Registro de productos

### Crear producto nuevo

1. Ir a **Productos**.
2. En el formulario **Agregar producto activo**, completar:
   - Familia.
   - Código.
   - Descripción.
   - Talla.
   - Stock inicial.
   - Stock mínimo.
3. Presionar **Agregar producto**.

### Registrar producto usando pistoleo del código

1. Ir a **Productos**.
2. Hacer clic en el campo **Código**.
3. Pistolear el producto.
4. El sistema cargará automáticamente el código.
5. Si el código ya existe, el sistema mostrará el producto registrado y evitará duplicarlo.
6. Si el código no existe, completar los datos restantes y guardar.

### Validación de duplicados

El sistema normaliza el código pistoleado, eliminando espacios, Enter, tabuladores y caracteres invisibles. También corrige lecturas que vengan desde planillas con formato terminado en `.0`.

---

## 6. Registro de ingresos y egresos desde Productos

1. Ir a **Productos**.
2. Buscar el producto.
3. Presionar **Movimiento**.
4. Seleccionar:
   - Tipo: Ingreso o Egreso.
   - Cantidad.
   - Operador del servicio.
   - Observación, si corresponde.
5. Presionar **Guardar movimiento**.

### Reglas de control

- El ingreso suma unidades al stock.
- El egreso descuenta unidades del stock.
- El sistema no permite egresar más unidades que el stock disponible.
- Cada movimiento queda guardado con fecha, producto, cantidad, stock anterior, stock nuevo y operador responsable.

---

## 7. Registro por pistoleo

### Ingreso por pistoleo

1. Ir a **Pistoleo**.
2. Seleccionar **Ingreso**.
3. Definir la cantidad por lectura.
4. Seleccionar el operador del servicio.
5. Hacer clic en el campo **Código pistoleado**.
6. Pistolear el producto.
7. El sistema reconoce el código y suma el stock.

### Egreso por pistoleo

1. Ir a **Pistoleo**.
2. Seleccionar **Egreso**.
3. Definir la cantidad por lectura.
4. Seleccionar el operador del servicio.
5. Pistolear el producto.
6. El sistema reconoce el código y descuenta el stock.

### Resultado del pistoleo

Después de cada lectura, el sistema informa:

- Producto reconocido.
- Tipo de movimiento.
- Cantidad registrada.
- Stock nuevo.
- Operador responsable.
- Mensaje de confirmación o rechazo.

---

## 8. Operadores del servicio

Los operadores permiten auditar quién realizó cada movimiento.

### Crear operador

1. Ir a **Operadores**.
2. Completar:
   - Nombre operador.
   - Cargo o rol.
   - Turno o servicio.
3. Presionar **Agregar operador**.

### Desactivar operador

1. Ir a **Operadores**.
2. Buscar el operador activo.
3. Presionar **Desactivar**.

Los movimientos históricos del operador se conservan.

---

## 9. Dashboard y conclusiones

El Dashboard entrega una lectura operacional rápida del inventario.

### Indicadores principales

- **Productos activos:** cantidad de productos disponibles en la bodega.
- **Stock total:** suma total de unidades registradas.
- **Bajo mínimo:** productos cuyo stock está igual o bajo el mínimo configurado.
- **Sin stock:** productos con stock cero.
- **Movimientos hoy:** cantidad de ingresos y egresos del día.

### Gráficos

- **Ingresos vs egresos últimos 14 días:** permite ver tendencia de entradas y salidas.
- **Stock por familia:** permite identificar qué familias concentran mayor volumen de inventario.

### Conclusiones automáticas

El sistema genera observaciones como:

- Cantidad de productos activos.
- Stock total disponible.
- Familia con mayor stock.
- Alertas por mínimo o sin stock.
- Producto con menor stock.
- Operador con más movimientos en los últimos 30 días.

---

## 10. Exportación CSV

### Productos CSV

Disponible dentro de la sección **Productos** mediante el botón **Descargar productos CSV**.

Incluye:

- Familia.
- Código.
- Descripción.
- Talla.
- Stock.
- Stock mínimo.
- Estado.

### Movimientos CSV

Disponible dentro de la sección **Movimientos** mediante el botón **Exportar movimientos CSV**.

Incluye:

- Fecha.
- Tipo de movimiento.
- Cantidad.
- Stock anterior.
- Stock nuevo.
- Familia.
- Código.
- Descripción.
- Talla.
- Operador.
- Responsable manual.
- Observación.

---

## 11. Buenas prácticas de uso

- Crear operadores antes de comenzar la operación diaria.
- Cambiar las claves iniciales al primer ingreso.
- Mantener el campo **Código** con el código real del producto.
- Definir stock mínimo para activar alertas útiles.
- Registrar observaciones cuando el movimiento esté asociado a una entrega, área, vale interno u orden de trabajo.
- Descargar respaldos CSV periódicamente.
- Verificar que el lector de código de barras envíe Enter al finalizar cada lectura.

---

## 12. Solución de problemas frecuentes

### El sistema no reconoce un código pistoleado

Verificar que:

- El producto esté creado y activo.
- El lector esté configurado como teclado/HID.
- El lector envíe Enter al terminar la lectura.
- El código guardado corresponda al código real del producto.

### No permite descontar producto

El egreso se rechaza cuando la cantidad solicitada supera el stock disponible.

### No puedo ingresar al sistema

Verificar usuario y clave. Si la clave fue cambiada, se debe usar la nueva clave.

### No aparece un operador

Verificar que el operador esté activo. Si fue desactivado, se puede volver a crear con el mismo nombre para reactivarlo.

---

## 13. Flujo recomendado diario

1. Ingresar al sistema con usuario autorizado.
2. Revisar Dashboard y alertas.
3. Registrar ingresos por Pistoleo o desde Productos.
4. Registrar egresos por Pistoleo o desde Productos.
5. Revisar Movimientos para validar trazabilidad.
6. Descargar CSV si se requiere respaldo o reporte.
7. Cerrar sesión al terminar la jornada.

---

## 14. Cierre de sesión

Al terminar la operación, presionar **Salir** en el menú superior para cerrar la sesión del usuario activo.
