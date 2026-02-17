import mysql.connector
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

app = FastAPI(title="Monte de Piedad API", version="2.1.1")

# ==================== CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== CONEXIÓN ====================
def conectar():
    return mysql.connector.connect(
        host="tramway.proxy.rlwy.net",
        user="root",
        password="UoIWKLOUCqSrMhnrGmrVPxLQfRtgtdVh",
        database="railway",
        port=59943,
        autocommit=False
    )

# ==================== MODELOS PYDANTIC ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class RegistroRequest(BaseModel):
    username: str
    password: str
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    telefono: str
    email: str
    direccion: str
    fecha_nacimiento: str  # formato: YYYY-MM-DD
    identificacion: str
    curp: str

class PrestamoRequest(BaseModel):
    id_cliente: int
    monto: float
    meses: int

class ConfiguracionRequest(BaseModel):
    tasa_interes: float
    plazo_maximo: int
    monto_minimo: float
    monto_maximo: float

class AprobarPrestamoRequest(BaseModel):
    id_prestamo: int
    aprobado: bool

# ==================== HELPER ====================

def generar_calendario_pagos(cursor, id_prestamo, monto, tasa_mensual, plazo_meses):
    """Genera calendario de pagos - ✅ Todo float, sin Decimal"""
    monto = float(monto)
    tasa_mensual = float(tasa_mensual)
    plazo_meses = int(plazo_meses)

    if tasa_mensual == 0:
        cuota = monto / plazo_meses
    else:
        # Fórmula Sistema Francés (cuota nivelada)
        factor = (1 + tasa_mensual) ** plazo_meses
        cuota = monto * (tasa_mensual * factor) / (factor - 1)

    fecha_base = datetime.now()

    for i in range(plazo_meses):
        fecha_vencimiento = fecha_base + timedelta(days=30 * (i + 1))
        cursor.execute("""
            INSERT INTO pagos (id_prestamo, numero_pago, monto, fecha_vencimiento, estado)
            VALUES (%s, %s, %s, %s, 'PENDIENTE')
        """, (id_prestamo, i + 1, round(cuota, 2), fecha_vencimiento))

# ==================== ENDPOINTS ====================

# ROOT
@app.get("/")
def root():
    return {
        "message": "API Monte de Piedad - Activa",
        "version": "2.0",
        "endpoints": [
            "/login",
            "/registrar_cliente",
            "/cliente/prestamo",
            "/cliente/mis_prestamos",
            "/cliente/cartera",
            "/cliente/pagos/{id_prestamo}",
            "/configuracion_sistema",
            "/admin/prestamos_pendientes",
            "/admin/aprobar_prestamo",
            "/admin/estadisticas"
        ]
    }

# 1. LOGIN
@app.post("/login")
def login(request: LoginRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, rol, nombre_completo, estado 
            FROM usuarios 
            WHERE username=%s AND password=%s
        """, (request.username, request.password))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        if user['estado'] != 'Activo':
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        if user['rol'] == 'CLIENTE':
            cursor.execute("SELECT id_cliente FROM clientes WHERE id_usuario=%s", (user['id_usuario'],))
            cliente_info = cursor.fetchone()
            user['id_cliente'] = cliente_info['id_cliente'] if cliente_info else None
        else:
            user['id_cliente'] = None

        return {"status": "success", "user": user}
    finally:
        db.close()

# 2. REGISTRO COMPLETO
@app.post("/registrar_cliente")
def registrar_cliente(request: RegistroRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        db.start_transaction()

        # Verificar correo duplicado
        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (request.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        # Verificar CURP duplicado
        cursor.execute("SELECT id_cliente FROM clientes WHERE curp = %s", (request.curp,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El CURP ya está registrado")

        nombre_completo = f"{request.nombre} {request.apellido_paterno} {request.apellido_materno}"

        cursor.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, rol, estado) 
            VALUES (%s, %s, %s, 'CLIENTE', 'Activo')
        """, (request.username, request.password, nombre_completo))

        id_usuario = cursor.lastrowid

        cursor.execute("""
            INSERT INTO clientes (
                id_usuario, nombre, apellido_paterno, apellido_materno,
                telefono, email, direccion, fecha_nacimiento, identificacion, curp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            id_usuario,
            request.nombre,
            request.apellido_paterno,
            request.apellido_materno,
            request.telefono,
            request.email,
            request.direccion,
            request.fecha_nacimiento,
            request.identificacion,
            request.curp
        ))

        db.commit()
        return {"status": "success", "message": "Cliente registrado correctamente"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 3. SOLICITAR PRÉSTAMO ✅ CORREGIDO (sin Decimal)
@app.post("/cliente/prestamo")
def solicitar_prestamo(request: PrestamoRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT tasa_interes FROM configuracion_sistema ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()

        # ✅ float() elimina el error de Decimal
        tasa = float(config[0]) if config else 0.05
        monto = float(request.monto)
        meses = int(request.meses)

        cursor.execute("""
            INSERT INTO prestamos (
                id_cliente, monto_total, saldo_pendiente,
                tasa_interes, plazo_meses, estado, fecha_creacion
            ) VALUES (%s, %s, %s, %s, %s, 'PENDIENTE', NOW())
        """, (request.id_cliente, monto, monto, tasa, meses))

        id_prestamo = cursor.lastrowid
        generar_calendario_pagos(cursor, id_prestamo, monto, tasa, meses)

        db.commit()
        return {
            "status": "success",
            "message": "Solicitud enviada correctamente",
            "id_prestamo": id_prestamo
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# 4. MIS PRÉSTAMOS
@app.get("/cliente/mis_prestamos")
def obtener_mis_prestamos(id_cliente: int = Query(...)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_prestamo, monto_total, saldo_pendiente,
                   plazo_meses, tasa_interes, estado, fecha_creacion
            FROM prestamos
            WHERE id_cliente = %s
            ORDER BY fecha_creacion DESC
        """, (id_cliente,))
        prestamos = cursor.fetchall()
        for p in prestamos:
            p['monto_total'] = float(p['monto_total'])
            p['saldo_pendiente'] = float(p['saldo_pendiente'])
            p['tasa_interes'] = float(p['tasa_interes'])
            p['fecha_creacion'] = p['fecha_creacion'].strftime('%Y-%m-%d %H:%M:%S')
        return prestamos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 5. CARTERA
@app.get("/cliente/cartera")
def obtener_cartera(id_cliente: int = Query(...)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT SUM(monto_total) as capital_total, SUM(saldo_pendiente) as pendiente_total
            FROM prestamos
            WHERE id_cliente = %s AND estado IN ('ACTIVO', 'MORA', 'PENDIENTE')
        """, (id_cliente,))
        totales = cursor.fetchone()
        capital = float(totales['capital_total'] or 0)
        pendiente = float(totales['pendiente_total'] or 0)
        return {
            "capital_otorgado": capital,
            "monto_liquidado": capital - pendiente,
            "saldo_pendiente": pendiente
        }
    finally:
        db.close()

# 6. CALENDARIO DE PAGOS
@app.get("/cliente/pagos/{id_prestamo}")
def obtener_pagos(id_prestamo: int):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_pago, numero_pago, monto, fecha_vencimiento, fecha_pago, estado
            FROM pagos
            WHERE id_prestamo = %s
            ORDER BY numero_pago
        """, (id_prestamo,))
        pagos = cursor.fetchall()
        for p in pagos:
            p['monto'] = float(p['monto'])
            if p['fecha_vencimiento']:
                p['fecha_vencimiento'] = p['fecha_vencimiento'].strftime('%Y-%m-%d')
            if p['fecha_pago']:
                p['fecha_pago'] = p['fecha_pago'].strftime('%Y-%m-%d')
        return pagos
    finally:
        db.close()

# 7. CONFIGURACIÓN (GET)
@app.get("/configuracion_sistema")
def obtener_configuracion():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM configuracion_sistema ORDER BY id DESC LIMIT 1")
        config = cursor.fetchone()
        if not config:
            return {
                "id": 1,
                "tasa_interes": 0.05,
                "plazo_maximo": 48,
                "monto_minimo": 1000.0,
                "monto_maximo": 100000.0
            }
        return {
            "id": config['id'],
            "tasa_interes": float(config['tasa_interes']),
            "plazo_maximo": config['plazo_maximo'],
            "monto_minimo": float(config['monto_minimo']),
            "monto_maximo": float(config['monto_maximo'])
        }
    finally:
        db.close()

# 8. CONFIGURACIÓN (PUT)
@app.put("/configuracion_sistema/{id_config}")
def actualizar_configuracion(id_config: int, request: ConfiguracionRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE configuracion_sistema
            SET tasa_interes=%s, plazo_maximo=%s, monto_minimo=%s, monto_maximo=%s
            WHERE id=%s
        """, (request.tasa_interes, request.plazo_maximo, request.monto_minimo, request.monto_maximo, id_config))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")

        db.commit()
        return {"status": "success", "message": "Configuración actualizada"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 9. PRÉSTAMOS PENDIENTES (ADMIN)
@app.get("/admin/prestamos_pendientes")
def obtener_prestamos_pendientes():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                p.id_prestamo,
                p.monto_total,
                p.plazo_meses,
                p.fecha_creacion,
                CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) as nombre_cliente,
                c.curp
            FROM prestamos p
            JOIN clientes c ON p.id_cliente = c.id_cliente
            WHERE p.estado = 'PENDIENTE'
            ORDER BY p.fecha_creacion ASC
        """)
        prestamos = cursor.fetchall()
        for p in prestamos:
            p['monto_total'] = float(p['monto_total'])
            p['fecha_creacion'] = p['fecha_creacion'].strftime('%Y-%m-%d %H:%M:%S')
        return prestamos
    finally:
        db.close()

# 10. APROBAR/RECHAZAR PRÉSTAMO (ADMIN)
@app.post("/admin/aprobar_prestamo")
def aprobar_prestamo(request: AprobarPrestamoRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        nuevo_estado = "ACTIVO" if request.aprobado else "RECHAZADO"
        cursor.execute("""
            UPDATE prestamos SET estado=%s WHERE id_prestamo=%s
        """, (nuevo_estado, request.id_prestamo))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")

        db.commit()
        return {"status": "success", "message": f"Préstamo {nuevo_estado.lower()}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 11. ESTADÍSTICAS (ADMIN)
@app.get("/admin/estadisticas")
def obtener_estadisticas():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as total FROM clientes")
        total_clientes = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'ACTIVO'")
        total_activos = cursor.fetchone()['total']

        cursor.execute("SELECT SUM(monto_total) as total FROM prestamos WHERE estado IN ('ACTIVO', 'MORA')")
        capital = cursor.fetchone()
        capital_total = float(capital['total'] or 0)

        cursor.execute("SELECT SUM(saldo_pendiente) as total FROM prestamos WHERE estado IN ('ACTIVO', 'MORA')")
        pendiente = cursor.fetchone()
        saldo_pendiente = float(pendiente['total'] or 0)

        return {
            "total_clientes": total_clientes,
            "prestamos_activos": total_activos,
            "capital_otorgado": capital_total,
            "saldo_pendiente": saldo_pendiente,
            "monto_recuperado": capital_total - saldo_pendiente
        }
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


