import os
import mysql.connector
from dotenv import load_dotenv

# carga las credenciales del archivo .env
load_dotenv()

# lee los datos de conexión
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")

# FUNCIÓN : crea una conexión nueva con mysql y la devuelve
def make_connection():
    mydb = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    )
    return mydb