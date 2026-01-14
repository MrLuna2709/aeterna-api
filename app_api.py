import mysql.connector
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CONFIGURACIÓN DE CORS (Indispensable para la Persona O) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite conexiones desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FUNCIÓN DE CONEXIÓN A RAILWAY ---
def conectar():
    return mysql.connector.connect(
        host="tramway.proxy.rlwy.net",
        user="root",
        password="UoIWKLOUCqSrMhnrGmrVPxLQfRtgtdVh", # Tu Master Password
        database="railway",
        port=59943,
        autocommit=True
    )

# --- ENDPOINT: LOGIN ---
@app.post("/login")
def login(username: str = Query(...), password: str = Query(...)):
    print(f"DEBUG: Intento de login para usuario: {username}")
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Buscamos al usuario por credenciales
        query = "SELECT id_usuario, rol, nombre_completo, sesion_activa FROM usuarios WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        # Si es un CLIENTE, obtenemos su ID de la tabla clientes
        if user['rol'] == 'CLIENTE':
            cursor.execute("SELECT id_cliente FROM clientes WHERE id_usuario=%s", (user['id_usuario'],))
            cliente_data = cursor.fetchone()
            if cliente_data:
                user['id_cliente'] = cliente_data['id_cliente']

        return {"status": "success", "user": user}
    
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error de DB: {err}")
    finally:
        cursor.close()
        db.close()

# --- ENDPOINT: REGISTRO DE CLIENTE ---
@app.post("/registrar_cliente")
def registrar(username: str = Query(...), passw: str = Query(...), nombre: str = Query(...), curp: str = Query(...)):
    db = conectar()
    cursor = db.cursor()
    try:
        # 1. Insertar en la tabla usuarios
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo, estado) VALUES (%s, %s, 'CLIENTE', %s, 'Activo')",
            (username, passw, nombre)
        )
        id_u = cursor.lastrowid

        # 2. Insertar en la tabla clientes
        cursor.execute(
            "INSERT INTO clientes (id_usuario, curp, estatus) VALUES (%s, %s, 'Activo')",
            (id_u, curp)
        )
        
        return {"status": "success", "message": "Cliente registrado correctamente"}
    
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error al registrar: {err}")
    finally:
        cursor.close()
        db.close()

# --- ENDPOINT: SOLICITUD DE PRÉSTAMO ---
@app.post("/cliente/prestamo")
def solicitar_prestamo(id_cliente: int = Query(...), monto: float = Query(...), meses: int = Query(...)):
    db = conectar()
    cursor = db.cursor()
    try:
        # Insertar la solicitud (Ajusta los nombres de columna según tu tabla prestamos)
        cursor.execute(
            "INSERT INTO prestamos (id_cliente, monto, meses, estado) VALUES (%s, %s, %s, 'Pendiente')",
            (id_cliente, monto, meses)
        )
        return {"status": "success", "message": "Solicitud enviada"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
