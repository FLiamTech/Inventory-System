from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Carga de variables
load_dotenv()

# Uri del archivo
MONGO_URI = os.getenv('MONGO_URI')

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database()
    print("Conexion exitosa con la base de datos")
except Exception as e:
    print("Error al conectarse con la base de datos", e)

user_collection = db['usuarios']
insumos_collection = db['insumos']
movimientos_collection = db['movimientos']
compras_collection = db['compras']