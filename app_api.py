import mysql.connector
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CONFIGURACIÓN DE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FUNCIÓN DE CONEXIÓN A RAILWAY ---
def conectar():
    return mysql.connector.connect(
        host="tramway.proxy.rlwy.net",
        user="root",
        password="UoIWKLOUCqSrMhnrGmrVPxLQfRtgtdVh",
        database="railway",
        port=59943,
        autocommit=True
    )

@app.post("/login")
def login(username: str = Query(...), password: str = Query(...)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, rol, nombre_completo FROM usuarios WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        if user['rol'] == 'CLIENTE':
            cursor.execute("SELECT id_cliente FROM clientes WHERE id_usuario=%s", (user['id_usuario'],))
            cliente_info = cursor.fetchone()
            if cliente_info:
                user['id_cliente'] = cliente_info['id_cliente']
            else:
                user['id_cliente'] = None 

        return {"status": "success", "user": user}
    finally:
        db.close()

@app.post("/registrar_cliente")
def registrar(username: str = Query(...), passw: str = Query(...), nombre: str = Query(...), curp: str = Query(...)):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password, rol, nombre_completo, estado) VALUES (%s, %s, 'CLIENTE', %s, 'Activo')", (username, passw, nombre))
        id_u = cursor.lastrowid
        cursor.execute("INSERT INTO clientes (id_usuario, curp, estatus) VALUES (%s, %s, 'Activo')", (id_u, curp))
        return {"status": "success", "detail": "Usuario registrado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/cliente/prestamo")
def solicitar_prestamo(id_cliente: int = Query(...), monto: float = Query(...), meses: int = Query(...)):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO prestamos (id_cliente, monto, meses, estado) VALUES (%s, %s, %s, 'Pendiente')",
            (id_cliente, monto, meses)
        )
        return {"status": "success", "message": "Solicitud enviada"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        db.close()

# --- CORRECCIÓN DE SANGRIÁ AQUÍ: Esta función ya no está dentro de la anterior ---
@app.get("/cliente/mis_prestamos")
def obtener_prestamos(id_cliente: int = Query(...)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT id_prestamo, monto, meses, estado FROM prestamos WHERE id_cliente = %s"
        cursor.execute(query, (id_cliente,))
        prestamos = cursor.fetchall()
        return prestamos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
