"""
database.py
===========
Capa de acceso a datos - Cantina Escolar R.R.
Esquema v3: pedidos + detalle_pedido + pagos + vistas
Todas las consultas a MySQL viven aquí.
main.py nunca toca MySQL directamente.
"""

import hashlib
import mysql.connector
from conexion import conectar
import requests
from datetime import datetime

# ============================================================
# TASA BCV
# ============================================================


def obtener_tasa_bcv() -> dict:
    """
    Retorna la tasa BCV más reciente guardada en BD.
    Resultado: {"tasa": 517.96, "fecha": "19/05/2026"}
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar a la base de datos.")
    try:
        cur = con.cursor()
        cur.execute("SELECT tasa, fecha FROM tasa_bcv ORDER BY fecha DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise ValueError("No hay tasas BCV registradas.")
        return {
            "tasa": float(row[0]),
            "fecha": (
                row[1].strftime("%d/%m/%Y")
                if hasattr(row[1], "strftime")
                else str(row[1])
            ),
        }
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener tasa BCV: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def guardar_tasa_bcv(tasa: float, fecha: str) -> None:
    """Guarda o actualiza la tasa BCV. fecha formato: 'YYYY-MM-DD'"""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO tasa_bcv (tasa, fecha) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE tasa = %s",
            (tasa, fecha, tasa),
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al guardar tasa BCV: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_tasa_bcv_online():
    url = "https://ve.dolarapi.com/v1/dolares/oficial"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()

        fecha = datetime.fromisoformat(
            data["fechaActualizacion"].replace("Z", "+00:00")
        ).strftime("%d/%m/%Y")

        return {"tasa": float(data["promedio"]), "fecha": fecha}

    except Exception as e:
        raise RuntimeError(f"No se pudo obtener la tasa online: {e}")


# ============================================================
# PRODUCTOS
# ============================================================


def obtener_productos(categoria: str = None, filtro: str = None) -> list:
    """
    Retorna productos disponibles.
    Cada fila: (id_producto, nombre, precio_usd)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        if filtro:
            cur.execute(
                "SELECT id_producto, nombre, precio_usd FROM productos "
                "WHERE estado='Disponible' AND nombre LIKE %s "
                "ORDER BY categoria, nombre",
                (f"%{filtro}%",),
            )
        elif categoria:
            cur.execute(
                "SELECT id_producto, nombre, precio_usd FROM productos "
                "WHERE estado='Disponible' AND categoria=%s ORDER BY nombre",
                (categoria,),
            )
        else:
            cur.execute(
                "SELECT id_producto, nombre, precio_usd FROM productos "
                "WHERE estado='Disponible' ORDER BY categoria, nombre"
            )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener productos: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_todos_productos() -> dict:
    """
    Retorna todos los productos agrupados por categoría.
    { "Por Unidad": [(id, nombre, cat, precio_usd, estado), ...], ... }
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_producto, nombre, categoria, precio_usd, estado "
            "FROM productos ORDER BY categoria, nombre"
        )
        resultado = {}
        for row in cur.fetchall():
            resultado.setdefault(row[2], []).append(row)
        return resultado
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener productos: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def guardar_producto(nombre: str, categoria: str, precio_usd: float) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO productos (nombre, categoria, precio_usd) "
            "VALUES (%s, %s, %s)",
            (nombre, categoria, precio_usd),
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al guardar producto: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def actualizar_producto(
    id_producto: int, nombre: str, categoria: str, precio_usd: float, estado: str
) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE productos SET nombre=%s, categoria=%s, "
            "precio_usd=%s, estado=%s WHERE id_producto=%s",
            (nombre, categoria, precio_usd, estado, id_producto),
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar producto: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def toggle_estado_producto(id_producto: int, disponible_actual: bool) -> None:
    nuevo = "Agotado" if disponible_actual else "Disponible"
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE productos SET estado=%s WHERE id_producto=%s", (nuevo, id_producto)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al cambiar estado: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# CUENTAS
# ============================================================


def obtener_cuentas(filtro: str = "") -> list:
    """
    Retorna cuentas con saldo calculado desde la vista.
    Cada fila: (id_cuenta, nombre_referencia, telefono,
                tipo_usuario, deuda_usd)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        if filtro:
            cur.execute(
                "SELECT id_cuenta, nombre_referencia, telefono, "
                "tipo_usuario, deuda_usd "
                "FROM vista_saldos "
                "WHERE nombre_referencia LIKE %s "
                "ORDER BY nombre_referencia",
                (f"%{filtro}%",),
            )
        else:
            cur.execute(
                "SELECT id_cuenta, nombre_referencia, telefono, "
                "tipo_usuario, deuda_usd "
                "FROM vista_saldos ORDER BY nombre_referencia"
            )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener cuentas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def crear_cuenta(nombre_ref: str, telefono: str, tipo: str) -> int:
    """Crea una cuenta y retorna su id."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO cuentas (nombre_referencia, telefono, tipo_usuario) "
            "VALUES (%s, %s, %s)",
            (nombre_ref, telefono, tipo),
        )
        con.commit()
        return cur.lastrowid
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al crear cuenta: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def actualizar_cuenta(
    id_cuenta: int, nombre_ref: str, telefono: str, tipo: str
) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE cuentas SET nombre_referencia=%s, telefono=%s, "
            "tipo_usuario=%s WHERE id_cuenta=%s",
            (nombre_ref, telefono, tipo, id_cuenta),
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar cuenta: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def buscar_cuentas(filtro: str) -> list:
    """Búsqueda rápida de cuentas por nombre. Devuelve (id, nombre, deuda)."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_cuenta, nombre_referencia, deuda_usd "
            "FROM vista_saldos "
            "WHERE nombre_referencia LIKE %s LIMIT 8",
            (f"%{filtro}%",),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al buscar cuentas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# PERSONAS
# ============================================================


def obtener_personas(id_cuenta: int) -> list:
    """Retorna personas vinculadas a una cuenta."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_persona, nombre, apellido, tipo, grado_seccion "
            "FROM personas WHERE id_cuenta=%s ORDER BY nombre",
            (id_cuenta,),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener personas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def buscar_personas(texto: str) -> list:
    """
    Busca personas por nombre o apellido.
    Retorna: (id_persona, nombre, apellido, tipo,
              grado_seccion, id_cuenta, nombre_referencia, telefono)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT p.id_persona, p.nombre, p.apellido, p.tipo,
                      p.grado_seccion, c.id_cuenta,
                      c.nombre_referencia, c.telefono
               FROM personas p
               JOIN cuentas c ON p.id_cuenta = c.id_cuenta
               WHERE p.nombre LIKE %s OR p.apellido LIKE %s
                  OR CONCAT(p.nombre,' ',p.apellido) LIKE %s
               ORDER BY p.apellido, p.nombre
               LIMIT 10""",
            (f"%{texto}%",) * 3,
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al buscar personas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def buscar_personas_por_grado(grado: str) -> list:
    """
    Retorna todas las personas de un grado específico.
    Útil para filtrar por receso (Primaria baja, alta, etc.)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT p.id_persona, p.nombre, p.apellido, p.tipo,
                      p.grado_seccion, c.id_cuenta,
                      c.nombre_referencia, c.telefono
               FROM personas p
               JOIN cuentas c ON p.id_cuenta = c.id_cuenta
               WHERE p.grado_seccion LIKE %s
               ORDER BY p.apellido, p.nombre""",
            (f"%{grado}%",),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al buscar por grado: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def crear_persona(
    nombre: str, apellido: str, tipo: str, grado: str, id_cuenta: int
) -> int:
    """Crea una persona y retorna su id."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO personas (nombre, apellido, tipo, "
            "grado_seccion, id_cuenta) VALUES (%s,%s,%s,%s,%s)",
            (nombre, apellido, tipo, grado or None, id_cuenta),
        )
        con.commit()
        return cur.lastrowid
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al crear persona: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def actualizar_persona(
    id_persona: int, nombre: str, apellido: str, tipo: str, grado: str
) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE personas SET nombre=%s, apellido=%s, "
            "tipo=%s, grado_seccion=%s WHERE id_persona=%s",
            (nombre, apellido, tipo, grado or None, id_persona),
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar persona: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# PEDIDOS
# ============================================================


def registrar_pedido(
    id_persona: int, carrito: list, tasa: float, metodo_pago: str
) -> int:
    """
    Registra un pedido completo con sus detalles.
    Si el método es distinto de 'Crédito', registra también el pago.
    Retorna el id del pedido creado.
    """
    total_usd = round(sum(p["subtotal"] for p in carrito), 2)
    total_bs = round(total_usd * tasa, 2)

    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()

        # Determinar estado_pago inicial
        if metodo_pago == "Crédito":
            estado_pago = "Pendiente"
        else:
            estado_pago = "Pagado"

        # Insertar pedido
        cur.execute(
            "INSERT INTO pedidos "
            "(id_persona, estado_pago, total_usd, total_bs, tasa_aplicada) "
            "VALUES (%s, %s, %s, %s, %s)",
            (id_persona, estado_pago, total_usd, total_bs, tasa),
        )
        id_pedido = cur.lastrowid

        # Insertar detalles
        for p in carrito:
            cur.execute(
                "INSERT INTO detalle_pedido "
                "(id_pedido, id_producto, cantidad, "
                "precio_unitario_usd, subtotal_usd) "
                "VALUES (%s, %s, %s, %s, %s)",
                (id_pedido, p["id"], p["cantidad"], p["precio"], p["subtotal"]),
            )

        # Si pagó en ese momento, registrar el pago
        if metodo_pago != "Crédito":
            # Obtener id_cuenta desde la persona
            cur.execute(
                "SELECT id_cuenta FROM personas WHERE id_persona=%s", (id_persona,)
            )
            id_cuenta = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO pagos "
                "(id_pedido, id_cuenta, monto_usd, monto_bs, metodo_pago) "
                "VALUES (%s, %s, %s, %s, %s)",
                (id_pedido, id_cuenta, total_usd, total_bs, metodo_pago),
            )

        con.commit()
        return id_pedido

    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al registrar pedido: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_pedidos(filtro: str = "", limit: int = 60, offset: int = 0) -> list:
    """
    Retorna pedidos con info del cliente, paginados.
    Cada fila: (id_pedido, nombre_persona, grado,
                nombre_cuenta, fecha, total_usd,
                estado_pago, pagado_usd)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        sql = """
            SELECT
                ped.id_pedido,
                CONCAT(per.nombre, ' ', per.apellido) AS nombre_persona,
                per.grado_seccion,
                c.nombre_referencia,
                ped.fecha_pedido,
                ped.total_usd,
                ped.estado_pago,
                COALESCE(
                    (SELECT SUM(monto_usd) FROM pagos
                     WHERE id_pedido = ped.id_pedido), 0
                ) AS pagado_usd
            FROM pedidos ped
            JOIN personas per ON ped.id_persona = per.id_persona
            JOIN cuentas c    ON per.id_cuenta  = c.id_cuenta
        """
        if filtro:
            sql += (
                " WHERE per.nombre LIKE %s OR per.apellido LIKE %s "
                "OR c.nombre_referencia LIKE %s "
                "OR CONCAT(per.nombre,' ',per.apellido) LIKE %s"
            )
            sql += " ORDER BY ped.fecha_pedido DESC LIMIT %s OFFSET %s"
            cur.execute(sql, (f"%{filtro}%",) * 4 + (limit, offset))
        else:
            sql += " ORDER BY ped.fecha_pedido DESC LIMIT %s OFFSET %s"
            cur.execute(sql, (limit, offset))
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener pedidos: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_detalle_pedido(id_pedido: int) -> list:
    """
    Retorna los productos de un pedido.
    Cada fila: (nombre_producto, cantidad,
                precio_unitario_usd, subtotal_usd)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT pr.nombre, d.cantidad,
                      d.precio_unitario_usd, d.subtotal_usd
               FROM detalle_pedido d
               JOIN productos pr ON d.id_producto = pr.id_producto
               WHERE d.id_pedido=%s""",
            (id_pedido,),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener detalle: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def eliminar_pedido(id_pedido: int) -> None:
    """
    Elimina un pedido y sus pagos.
    Los detalles se borran solos por ON DELETE CASCADE.
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM pagos WHERE id_pedido=%s", (id_pedido,))
        cur.execute("DELETE FROM pedidos WHERE id_pedido=%s", (id_pedido,))
        con.commit()
    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al eliminar pedido: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# PAGOS
# ============================================================


def registrar_pago(
    id_pedido: int, id_cuenta: int, monto_usd: float, tasa: float, metodo: str
) -> None:
    """
    Registra un pago (total o parcial) sobre un pedido existente.
    Actualiza el estado_pago del pedido automáticamente.
    """
    monto_bs = round(monto_usd * tasa, 2)
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()

        # Insertar el pago
        cur.execute(
            "INSERT INTO pagos "
            "(id_pedido, id_cuenta, monto_usd, monto_bs, metodo_pago) "
            "VALUES (%s, %s, %s, %s, %s)",
            (id_pedido, id_cuenta, monto_usd, monto_bs, metodo),
        )

        # Calcular total pagado vs total pedido
        cur.execute("SELECT total_usd FROM pedidos WHERE id_pedido=%s", (id_pedido,))
        total_pedido = float(cur.fetchone()[0])

        cur.execute(
            "SELECT COALESCE(SUM(monto_usd), 0) FROM pagos " "WHERE id_pedido=%s",
            (id_pedido,),
        )
        total_pagado = float(cur.fetchone()[0])

        # Actualizar estado_pago
        if total_pagado >= total_pedido:
            nuevo_estado = "Pagado"
        elif total_pagado > 0:
            nuevo_estado = "Parcial"
        else:
            nuevo_estado = "Pendiente"

        cur.execute(
            "UPDATE pedidos SET estado_pago=%s WHERE id_pedido=%s",
            (nuevo_estado, id_pedido),
        )
        con.commit()

    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al registrar pago: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_pagos_pedido(id_pedido: int) -> list:
    """Retorna todos los pagos de un pedido específico."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_pago, monto_usd, monto_bs, metodo_pago, fecha_pago "
            "FROM pagos WHERE id_pedido=%s ORDER BY fecha_pago",
            (id_pedido,),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener pagos: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def eliminar_pago(id_pago: int) -> None:
    """
    Elimina un pago y recalcula el estado_pago del pedido.
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()

        # Obtener id_pedido antes de borrar
        cur.execute("SELECT id_pedido FROM pagos WHERE id_pago=%s", (id_pago,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Pago no encontrado.")
        id_pedido = row[0]

        # Eliminar el pago
        cur.execute("DELETE FROM pagos WHERE id_pago=%s", (id_pago,))

        # Recalcular estado_pago del pedido
        cur.execute("SELECT total_usd FROM pedidos WHERE id_pedido=%s", (id_pedido,))
        total_pedido = float(cur.fetchone()[0])

        cur.execute(
            "SELECT COALESCE(SUM(monto_usd), 0) FROM pagos " "WHERE id_pedido=%s",
            (id_pedido,),
        )
        total_pagado = float(cur.fetchone()[0])

        if total_pagado >= total_pedido:
            nuevo_estado = "Pagado"
        elif total_pagado > 0:
            nuevo_estado = "Parcial"
        else:
            nuevo_estado = "Pendiente"

        cur.execute(
            "UPDATE pedidos SET estado_pago=%s WHERE id_pedido=%s",
            (nuevo_estado, id_pedido),
        )
        con.commit()

    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al eliminar pago: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# CUENTAS POR COBRAR
# ============================================================


def obtener_cuentas_con_deuda() -> list:
    """
    Retorna todas las cuentas con deuda > 0, ordenadas por deuda desc.
    Cada fila: (id_cuenta, nombre_referencia, telefono,
                tipo_usuario, deuda_usd)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_cuenta, nombre_referencia, telefono, "
            "tipo_usuario, deuda_usd "
            "FROM vista_saldos "
            "WHERE deuda_usd > 0 "
            "ORDER BY deuda_usd DESC"
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener deudas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_detalle_deuda_cuenta(id_cuenta: int) -> list:
    """
    Retorna el detalle de pedidos con deuda pendiente de una cuenta,
    con el desglose de productos por pedido.
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        # Pedidos con saldo pendiente de esta cuenta
        cur.execute(
            """SELECT
                   ped.id_pedido,
                   CONCAT(per.nombre, ' ', per.apellido) AS persona,
                   ped.fecha_pedido,
                   ped.total_usd,
                   COALESCE(
                       (SELECT SUM(monto_usd) FROM pagos
                        WHERE id_pedido = ped.id_pedido), 0
                   ) AS pagado_usd,
                   ped.total_usd - COALESCE(
                       (SELECT SUM(monto_usd) FROM pagos
                        WHERE id_pedido = ped.id_pedido), 0
                   ) AS pendiente_usd,
                   ped.estado_pago
               FROM pedidos ped
               JOIN personas per ON ped.id_persona = per.id_persona
               WHERE per.id_cuenta = %s
                 AND ped.estado_pago IN ('Pendiente', 'Parcial')
               ORDER BY ped.fecha_pedido""",
            (id_cuenta,),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener detalle de deuda: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# DASHBOARD — MÉTRICAS
# ============================================================


def obtener_metricas_dia(fecha: str) -> dict:
    """
    Retorna métricas del día especificado.
    fecha formato: 'YYYY-MM-DD'
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()

        cur.execute(
            "SELECT COUNT(*), COALESCE(SUM(total_usd), 0) "
            "FROM pedidos WHERE DATE(fecha_pedido)=%s",
            (fecha,),
        )
        total_pedidos, ventas_usd = cur.fetchone()

        cur.execute(
            "SELECT COUNT(*) FROM pedidos "
            "WHERE DATE(fecha_pedido)=%s AND estado_pago='Pagado'",
            (fecha,),
        )
        pedidos_pagados = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM pedidos "
            "WHERE DATE(fecha_pedido)=%s "
            "AND estado_pago IN ('Pendiente', 'Parcial')",
            (fecha,),
        )
        pedidos_pendientes = cur.fetchone()[0]

        cur.execute(
            "SELECT COALESCE(SUM(monto_usd), 0) FROM pagos "
            "WHERE DATE(fecha_pago)=%s",
            (fecha,),
        )
        cobrado_usd = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(SUM(deuda_usd), 0) FROM vista_saldos")
        deuda_total = cur.fetchone()[0]

        return {
            "total_pedidos": int(total_pedidos),
            "ventas_usd": float(ventas_usd),
            "pedidos_pagados": int(pedidos_pagados),
            "pedidos_pendientes": int(pedidos_pendientes),
            "cobrado_usd": float(cobrado_usd),
            "deuda_total_usd": float(deuda_total),
        }
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener métricas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_productos_mas_vendidos(limite: int = 10) -> list:
    """Retorna los productos más vendidos por cantidad total."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT pr.nombre, SUM(d.cantidad) AS total_vendido,
                      SUM(d.subtotal_usd) AS ingresos_usd
               FROM detalle_pedido d
               JOIN productos pr ON d.id_producto = pr.id_producto
               GROUP BY pr.id_producto, pr.nombre
               ORDER BY total_vendido DESC
               LIMIT %s""",
            (limite,),
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener productos más vendidos: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def eliminar_persona(id_persona: int) -> None:
    """
    Elimina una persona y su cuenta si no tiene otras personas vinculadas.
    Los pedidos se eliminan en cascada.
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        # Obtener id_cuenta de esta persona
        cur.execute("SELECT id_cuenta FROM personas WHERE id_persona=%s", (id_persona,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Persona no encontrada.")
        id_cuenta = row[0]

        # Eliminar pedidos de esta persona (pagos en cascada)
        cur.execute("SELECT id_pedido FROM pedidos WHERE id_persona=%s", (id_persona,))
        pedidos = cur.fetchall()
        for (id_p,) in pedidos:
            cur.execute("DELETE FROM pagos WHERE id_pedido=%s", (id_p,))
        cur.execute("DELETE FROM pedidos WHERE id_persona=%s", (id_persona,))

        # Eliminar la persona
        cur.execute("DELETE FROM personas WHERE id_persona=%s", (id_persona,))

        # Si la cuenta ya no tiene personas, eliminarla también
        cur.execute("SELECT COUNT(*) FROM personas WHERE id_cuenta=%s", (id_cuenta,))
        if cur.fetchone()[0] == 0:
            cur.execute("DELETE FROM cuentas WHERE id_cuenta=%s", (id_cuenta,))

        con.commit()
    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al eliminar persona: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()
