import mysql.connector
from decimal import Decimal
from datetime import date, datetime
import os
#----CONEXIÓN A LA BASE DE DATOS

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )



def query(sql, params=None):
    db = get_connection()               #LLAMA A GET  CONNECTION()
    cursor = db.cursor(dictionary=True) #CREA UN CURSOR QUE DEVUELVE DICCIONARIOS
    cursor.execute(sql, params or ())   #EJECUTA SQL
    results = cursor.fetchall()         #OBTIENE LOS REGISTROS(LISTA DE DICCIONARIOS)

    #----CONVERSION DE TIPOS NO SERIALIZABLES
    for row in results:
        for key, value in row.items():
            # Decimal → float
            if isinstance(value, Decimal):
                row[key] = float(value)  
            # date → string
            elif isinstance(value, date):
                row[key] = value.strftime("%Y-%m-%d")
            # datetime → string
            elif isinstance(value, datetime):
                row[key] = value.strftime("%Y-%m-%d %H:%M:%S")

    cursor.close()
    db.close()
    return results