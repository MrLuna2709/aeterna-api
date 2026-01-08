import mysql.connector
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Esto permite que cualquier aplicación (Web o Android) se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],
)

# Función para conectar con Workbench
def conectar():
    return mysql.connector.connect(
        host="tramway.proxy.rlwy.net",
        user="root",
        password="UoIWKLOUCqSrMhnrGmrVPxLQfRtgtdVh", 
        database="railway",
        port=59943
    )

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginData):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    # Buscamos en la base de datos
    cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", 
                   (data.username, data.password))
    usuario = cursor.fetchone()
    db.close()
    
    if usuario:
        return {"status": "ok", "mensaje": "Bienvenido"}
    raise HTTPException(status_code=401, detail="Error de acceso")

# --- AQUÍ ESTÁ EL CORAZÓN DEL CASO 8 ---
class Prestamo(BaseModel):
    cliente: str
    monto: float
    meses: int


@app.post("/registrar_prestamo")
def registrar(p: Prestamo):
    # Lógica del Caso 8 (5% de interés mensual sobre el monto)
    # Ejemplo: Si pide 1000 a 10 meses -> Pago base 100 + Interés 50 = 150 mensual
    pago_base = p.monto / p.meses
    interes_mensual = p.monto * 0.05
    cuota_final = pago_base + interes_mensual
    
    db = conectar()
    cursor = db.cursor()
    
    # Asegúrate de que los nombres de las columnas coincidan con tu tabla
    sql = "INSERT INTO prestamos (cliente, monto_prestamo, plazo_meses, cuota_mensual) VALUES (%s, %s, %s, %s)"
    valores = (p.cliente, p.monto, p.meses, cuota_final)
    
    cursor.execute(sql, valores)
    
    db.commit() # <--- ¡ESTA LÍNEA ES VITAL! Sin esto, Railway no guarda nada.
    
    db.close()
    
    return {
        "status": "success", 
        "cuota": round(cuota_final, 2)
    }