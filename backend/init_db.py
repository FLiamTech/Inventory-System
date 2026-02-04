from db import user_collection, insumos_collection
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    print("Inicializando carga de datos...")

    # Creamos el usuario
    if user_collection.count_documents({}) == 0:
        usuarios = [
            {
                "nombre": "Dra. Ana Mosquera",
                "email": "amosquera@om.com",
                "password": generate_password_hash("admin123"), # Contraseña encriptada
                "rol": "admin",
                "fecha_creacion": datetime.now()
            },
            {
                "nombre": "Asistente Fabian",
                "email": "fliam@om.com",
                "password": generate_password_hash("prueba123"),
                "rol": "medico",
                "fecha_creacion": datetime.now()
            }
        ]
        user_collection.insert_many(usuarios)
        print("Usuarios creados: Admin | Prueba")
    else:
        print("Hubo un error en la creacion de datos")
    # Creacion de insumos
    if insumos_collection.count_documents({}) == 0:
        insumos = [
            {
                "nombre": "Anestesia Local (Lidocaína)",
                "descripcion": "Caja x 50 cartuchos",
                "unidad": "Caja",
                "costo": 15.50,
                "stock": 20,
                "stock_minimo": 5,
                "proveedor": "Dental Corp"
            },
            {
                "nombre": "Resina Compuesta 3M",
                "descripcion": "Jeringa 4g Tono A2",
                "unidad": "Unidad",
                "costo": 25.00,
                "stock": 3, # STOCK BAJO INTENCIONAL (Para probar la alerta)
                "stock_minimo": 5,
                "proveedor": "Importadora Dental"
            },
            {
                "nombre": "Guantes de Látex",
                "descripcion": "Caja x 100 unidades Talla M",
                "unidad": "Caja",
                "costo": 8.00,
                "stock": 50,
                "stock_minimo": 10,
                "proveedor": "Distribuidora Médica"
            }
        ]
        insumos_collection.insert_many(insumos)
        print("Insumos de prueba cargados!")
    else:
        print("El inventario ya tiene datos!")

if __name__ == "__main__":
    init_db()