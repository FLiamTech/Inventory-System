from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from db import user_collection, insumos_collection, movimientos_collection, compras_collection
from datetime import datetime
from bson import ObjectId
import os

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

app.secret_key = 'secreto_odontologia_super_seguro'

# Primer ruta: LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = user_collection.find_one({"email" : email})
        if user and check_password_hash(user['password'], password):
            session['email'] = user['email']
            session['rol'] = user['rol']
            session['nombre'] = user['nombre']

            if user['rol'] == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('consumo'))
        else:
            flash('Correo o contraseña incorrectos, ', 'danger')
    
    return render_template('login.html')

# Segunda ruta: DASHBOARD (Admin)
@app.route('/dashboard')
def dashboard():
    if 'email' not in session or  session['rol'] != 'admin':
        return redirect(url_for('login')) # Proteccion de ruta
    
    return render_template('dashboard.html', nombre = session['nombre'])

# Tercera ruta: Registro de consumo(Medico y admin)
@app.route('/consumo', methods=['GET','POST'])
def consumo():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Obtenemos el insumo
        id_insumo = request.form['id_insumo']
        cantidad = int(request.form['cantidad'])

        # Buscamos en la DB
        insumo = insumos_collection.find_one({"_id": ObjectId(id_insumo)})

        # Validacion de stock
        if insumo and insumo['stock'] >= cantidad:
            nuevo_stock = insumo['stock'] - cantidad

            # A: Actualizar el stock de la coleccion
            insumos_collection.update_one(
                {"_id" : ObjectId(id_insumo)},
                {"$set": {"stock" : nuevo_stock}}
            )

            # B: Registrar el movimiento en el historial
            movimientos_collection.insert_one({
                "id_insumo": ObjectId(id_insumo),
                "nombre_insumo": insumo['nombre'],
                "usuario": session['email'],
                "tipo": "SALIDA",
                "cantidad": cantidad,
                "fecha": datetime.now()
            })

            flash(f'Se descontaron {cantidad} unidades de {insumo["nombre"]}. Stock restante: {nuevo_stock}', 'success')
        else:
            flash('Error: Stock insuficiente para realizar esta operación.', 'danger')
        return redirect(url_for('consumo'))
    
    lista_insumos = insumos_collection.find()
    return render_template('consumo.html', insumos=lista_insumos, nombre=session['nombre'])

# Cuarta ruta: Inventario
@app.route('/inventario', methods=['GET','POST'])
def inventario():
    
    if 'email' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        descripcion = request.form['descripcion']
        unidad = request.form['unidad']
        costo = float(request.form['costo'])
        stock = int(request.form['stock'])
        minimo = int(request.form['minimo'])
        proveedor = request.form['proveedor']

        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
        total_compra = costo * stock

        producto_existente = insumos_collection.find_one({
            "nombre" : {"$regex" : f"^{nombre}$", "$options" : "i"}
        })
        
        if producto_existente:
            nuevo_stock_total = producto_existente['stock'] + stock
            insumos_collection.update_one(
                {"_id": producto_existente['_id']},
                {"$set": {
                    "stock": nuevo_stock_total,
                    "costo": costo,
                    "proveedor": proveedor,
                    "descripcion": descripcion 
                }}
            )
            flash(f'🔄 Producto "{nombre}" ya existía. Se sumaron {stock} unidades al stock.', 'info')
        else:
            # Lógica de creación (Nuevo producto)
            insumos_collection.insert_one({
                "nombre" : nombre,
                "descripcion" : descripcion,
                "unidad" : unidad,
                "costo" : costo,
                "stock" : stock,
                "stock_minimo" : minimo,
                "proveedor" : proveedor
            })
            flash(f'Producto "{nombre}" creado exitosamente.', 'success')
        
        # Registrar en Historial de Compras (Siempre pasa)
        compras_collection.insert_one({
            "fecha": fecha_actual,
            "proveedor": proveedor,
            "producto": nombre,
            "cantidad": stock,
            "precio_unitario": costo,
            "total": total_compra
        })
        return redirect(url_for('inventario'))
    
    lista_insumos = insumos_collection.find()
    return render_template('inventario.html', insumos=lista_insumos, nombre=session['nombre'])

# Quinta ruta: Eliminar producto
@app.route('/eliminar_insumo/<string:id_insumo>')
def eliminar_insumo(id_insumo):
    if 'email' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    insumos_collection.delete_one({"_id" : ObjectId(id_insumo)})
    flash('🗑️ Producto eliminado.', 'warning')
    return redirect(url_for('inventario'))

# Sexta ruta: Reporte de alertas
@app.route('/reportes')
def reportes():
    if 'email' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    
    # Decimos: "dame solo los productos donde stock <= stock_minimo"
    productos_criticos = insumos_collection.find({
        "$expr" : { "$lte" : ["$stock", "$stock_minimo"] }
    })

    # Convertimos a lista para poder contar
    lista_criticos = list(productos_criticos)
    return render_template('reportes.html', insumos = lista_criticos, nombre=session['nombre'])

# Septima ruta: Reporte compras
@app.route('/compras')
def compras():
    if 'email' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    
    compras_db = compras_collection.find().sort("__id", -1)
    return render_template('compras.html', compras=list(compras_db), nombre=session['nombre'])

# Octava ruta: editar_insumo
@app.route('/editar_insumo/<string:id_insumo>', methods=['GET', 'POST'])
def editar_insumo(id_insumo):
    if 'email' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        unidad = request.form['unidad']
        costo = float(request.form['costo'])
        stock = int(request.form['stock'])

        insumos_collection.update_one(
            {"_id": ObjectId(id_insumo)},
            {"$set": {
                "nombre": nombre,
                "descripcion": descripcion,
                "unidad": unidad,
                "costo": costo,
                "stock": stock
            }}
        )
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('inventario'))
    insumo_a_editar = insumos_collection.find_one({"_id" : ObjectId(id_insumo)})
    return render_template('editar_insumo.html', insumo = insumo_a_editar, nombre = session['nombre'])

# Novena ruta: Cerrar sesion
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)