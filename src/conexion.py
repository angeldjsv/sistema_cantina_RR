import mysql.connector
from mysql.connector import Error

def conectar():
    """ Establece la conexión con la base de datos MySQL en XAMPP """
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',       # Usuario por defecto de XAMPP
            password='',       # Por defecto XAMPP no tiene contraseña
            database='cantina_rr'
        )

        if conexion.is_connected():
            print("✅ Conexión exitosa a la base de datos 'cantina_rr'")
            return conexion

    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None

# Prueba de conexión rápida
if __name__ == "__main__":
    con = conectar()
    if con:
        con.close()
        print("🔌 Conexión cerrada.")