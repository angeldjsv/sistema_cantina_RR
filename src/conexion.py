import mysql.connector
from mysql.connector import Error

def conectar():
    """Establece la conexión con la base de datos MySQL en XAMPP"""
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='cantina_rr'
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None

if __name__ == "__main__":
    con = conectar()
    if con:
        print("✅ Conexión exitosa a 'cantina_rr'")
        con.close()
        print("🔌 Conexión cerrada.")
    else:
        print("❌ No se pudo conectar.")