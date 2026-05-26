"""
database.py
===========
Capa de acceso a datos - Cantina R.R.
Todas las consultas a MySQL viven aquí.
main.py solo llama estas funciones, nunca toca MySQL directamente.
"""

import mysql.connector
from conexion import conectar


# ============================================================
# TASA BCV
# ============================================================

def obtener_tasa_bcv() -> dict:
    """
    Retorna la tasa BCV más reciente guardada en BD.
    Resultado: {"tasa": 517.96, "fecha": "19/05/2026"}
    Lanza excepción si no hay datos o falla la conexión.
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar a la base de datos.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT tasa, fecha FROM tasa_bcv ORDER BY fecha DESC LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("No hay tasas BCV registradas.")
        return {
            "tasa":  float(row[0]),
            "fecha": row[1].strftime("%d/%m/%Y") if hasattr(row[1], "strftime") else str(row[1])
        }
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener tasa BCV: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def guardar_tasa_bcv(tasa: float, fecha: str) -> None:
    """
    Guarda o actualiza la tasa BCV.
    fecha formato: "YYYY-MM-DD"
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar a la base de datos.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO tasa_bcv (tasa, fecha) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE tasa = %s",
            (tasa, fecha, tasa)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al guardar tasa BCV: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_tasa_bcv_online() -> dict:
    """
    Intenta obtener la tasa BCV actual desde DolarApi (Moderna y estable).
    Resultado: {"tasa": 36.50, "fecha": "19/05/2026"}
    Lanza excepción si no hay internet o falla la API.
    """
    import urllib.request
    import json
    from datetime import date

    url = "https://ve.dolarapi.com/v1/dolares/oficial"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            # DolarApi retorna el promedio oficial del BCV en la llave 'promedio'
            tasa = float(data.get("promedio", 0))
            
            if tasa <= 0:
                raise ValueError("La API devolvió un valor inválido.")
                
            return {
                "tasa":  tasa,
                "fecha": date.today().strftime("%d/%m/%Y")
            }
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
                (f"%{filtro}%",)
            )
        elif categoria:
            cur.execute(
                "SELECT id_producto, nombre, precio_usd FROM productos "
                "WHERE estado='Disponible' AND categoria=%s ORDER BY nombre",
                (categoria,)
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
            "INSERT INTO productos (nombre, categoria, precio_usd) VALUES (%s,%s,%s)",
            (nombre, categoria, precio_usd)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al guardar producto: {e}")
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
            "UPDATE productos SET estado=%s WHERE id_producto=%s",
            (nuevo, id_producto)
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

def obtener_cuentas() -> list:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_cuenta, nombre_referencia, telefono, tipo_usuario, "
            "saldo_deuda, saldo_favor FROM cuentas ORDER BY nombre_referencia"
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
            "VALUES (%s,%s,%s)",
            (nombre_ref, telefono, tipo)
        )
        con.commit()
        return cur.lastrowid
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al crear cuenta: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def actualizar_cuenta(id_cuenta: int, nombre_ref: str,
                      telefono: str, tipo: str) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE cuentas SET nombre_referencia=%s, telefono=%s, "
            "tipo_usuario=%s WHERE id_cuenta=%s",
            (nombre_ref, telefono, tipo, id_cuenta)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar cuenta: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def buscar_cuentas(filtro: str) -> list:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_cuenta, nombre_referencia, saldo_deuda FROM cuentas "
            "WHERE nombre_referencia LIKE %s LIMIT 6",
            (f"%{filtro}%",)
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
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_persona, nombre, apellido, tipo, grado_seccion "
            "FROM personas WHERE id_cuenta=%s",
            (id_cuenta,)
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
    Retorna: (id_persona, nombre, apellido, tipo, id_cuenta, nombre_referencia)
    """
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT p.id_persona, p.nombre, p.apellido, p.tipo,
                      c.id_cuenta, c.nombre_referencia
               FROM personas p
               JOIN cuentas c ON p.id_cuenta = c.id_cuenta
               WHERE p.nombre LIKE %s OR p.apellido LIKE %s
                  OR CONCAT(p.nombre,' ',p.apellido) LIKE %s
               LIMIT 6""",
            (f"%{texto}%",) * 3
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al buscar personas: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def crear_persona(nombre: str, apellido: str, tipo: str,
                  grado: str, id_cuenta: int) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO personas (nombre, apellido, tipo, grado_seccion, id_cuenta) "
            "VALUES (%s,%s,%s,%s,%s)",
            (nombre, apellido, tipo, grado or None, id_cuenta)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al crear persona: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def actualizar_persona(id_persona: int, nombre: str, apellido: str,
                       tipo: str, grado: str) -> None:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE personas SET nombre=%s, apellido=%s, "
            "tipo=%s, grado_seccion=%s WHERE id_persona=%s",
            (nombre, apellido, tipo, grado or None, id_persona)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar persona: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


# ============================================================
# TRANSACCIONES
# ============================================================

def registrar_venta(id_cuenta: int, id_persona: int, carrito: list,
                    tasa: float, metodo: str) -> int:
    """
    Registra una venta completa con rollback si algo falla.
    Retorna el id de la transacción creada.
    """
    total_usd = round(sum(p["subtotal"] for p in carrito), 2)
    total_bs  = round(total_usd * tasa, 2)
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO transacciones "
            "(id_cuenta, id_persona, tipo, monto_total_usd, monto_total_bs, "
            "tasa_aplicada, metodo_pago) VALUES (%s,%s,'Consumo',%s,%s,%s,%s)",
            (id_cuenta, id_persona, total_usd, total_bs, tasa, metodo)
        )
        id_trans = cur.lastrowid
        for p in carrito:
            cur.execute(
                "INSERT INTO detalles_transaccion "
                "(id_transaccion, id_producto, cantidad, "
                "precio_unitario_usd, subtotal_usd) VALUES (%s,%s,%s,%s,%s)",
                (id_trans, p["id"], p["cantidad"], p["precio"], p["subtotal"])
            )
        campo = "saldo_deuda" if metodo == "Pendiente" else "saldo_favor"
        cur.execute(
            f"UPDATE cuentas SET {campo}={campo}+%s WHERE id_cuenta=%s",
            (total_usd, id_cuenta)
        )
        con.commit()
        return id_trans
    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al registrar venta: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def registrar_abono(id_cuenta: int, monto: float,
                    tasa: float, metodo: str) -> None:
    monto_bs = round(monto * tasa, 2)
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO transacciones "
            "(id_cuenta, tipo, monto_total_usd, monto_total_bs, "
            "tasa_aplicada, metodo_pago) VALUES (%s,'Abono',%s,%s,%s,%s)",
            (id_cuenta, monto, monto_bs, tasa, metodo)
        )
        cur.execute(
            "UPDATE cuentas SET saldo_deuda=GREATEST(0, saldo_deuda-%s) "
            "WHERE id_cuenta=%s",
            (monto, id_cuenta)
        )
        con.commit()
    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al registrar abono: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_historial(filtro: str = "") -> list:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        sql = """
            SELECT t.id_transaccion,
                   COALESCE(CONCAT(p.nombre,' ',p.apellido), '—'),
                   c.nombre_referencia, t.fecha,
                   t.monto_total_usd, t.monto_total_bs,
                   t.metodo_pago, t.tipo
            FROM transacciones t
            JOIN cuentas c ON t.id_cuenta = c.id_cuenta
            LEFT JOIN personas p ON t.id_persona = p.id_persona
        """
        if filtro:
            sql += (" WHERE c.nombre_referencia LIKE %s "
                    "OR p.nombre LIKE %s OR p.apellido LIKE %s")
            cur.execute(sql + " ORDER BY t.fecha DESC", (f"%{filtro}%",) * 3)
        else:
            cur.execute(sql + " ORDER BY t.fecha DESC")
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener historial: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def obtener_detalle_transaccion(id_transaccion: int) -> list:
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT pr.nombre, d.cantidad,
                      d.precio_unitario_usd, d.subtotal_usd
               FROM detalles_transaccion d
               JOIN productos pr ON d.id_producto = pr.id_producto
               WHERE d.id_transaccion=%s""",
            (id_transaccion,)
        )
        return cur.fetchall()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al obtener detalle: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def actualizar_transaccion(id_trans: int, nuevo_monto: float,
                           nuevo_metodo: str, tasa: float) -> None:
    nuevo_bs = round(nuevo_monto * tasa, 2)
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE transacciones SET monto_total_usd=%s, monto_total_bs=%s, "
            "metodo_pago=%s WHERE id_transaccion=%s",
            (nuevo_monto, nuevo_bs, nuevo_metodo, id_trans)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar transacción: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()


def eliminar_transaccion(id_trans: int) -> None:
    """Elimina una transacción y revierte el saldo automáticamente."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id_cuenta, monto_total_usd, metodo_pago, tipo "
            "FROM transacciones WHERE id_transaccion=%s",
            (id_trans,)
        )
        row = cur.fetchone()
        if row:
            id_c, monto, metodo, tipo = row
            if tipo == "Consumo":
                campo = "saldo_deuda" if metodo == "Pendiente" else "saldo_favor"
                cur.execute(
                    f"UPDATE cuentas SET {campo}=GREATEST(0,{campo}-%s) "
                    "WHERE id_cuenta=%s",
                    (monto, id_c)
                )
            elif tipo == "Abono":
                cur.execute(
                    "UPDATE cuentas SET saldo_deuda=saldo_deuda+%s "
                    "WHERE id_cuenta=%s",
                    (monto, id_c)
                )
        cur.execute(
            "DELETE FROM transacciones WHERE id_transaccion=%s", (id_trans,)
        )
        con.commit()
    except mysql.connector.Error as e:
        con.rollback()
        raise RuntimeError(f"Error al eliminar transacción: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()

def actualizar_producto(id_producto: int, nombre: str, categoria: str,
                        precio_usd: float, estado: str) -> None:
    """Actualiza todos los campos de un producto existente."""
    con = conectar()
    if not con:
        raise ConnectionError("No se pudo conectar.")
    try:
        cur = con.cursor()
        cur.execute(
            "UPDATE productos SET nombre=%s, categoria=%s, "
            "precio_usd=%s, estado=%s WHERE id_producto=%s",
            (nombre, categoria, precio_usd, estado, id_producto)
        )
        con.commit()
    except mysql.connector.Error as e:
        raise RuntimeError(f"Error al actualizar producto: {e}")
    finally:
        if con.is_connected():
            cur.close()
            con.close()