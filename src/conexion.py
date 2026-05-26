import os
import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()  # Carga las variables de entorno desde el archivo .env

def conectar():
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

if __name__ == "__main__":
    con = conectar()
    if con:
        print("✅ Conexión exitosa a 'cantina_rr'")
        con.close()
        print("🔌 Conexión cerrada.")
    else:
        print("❌ No se pudo conectar.")