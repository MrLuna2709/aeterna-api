import mysql.connector
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from notificaciones import (
    email_bienvenida,
    email_prestamo_aprobado,
    email_prestamo_rechazado,
    email_ticket_pago,
    email_prestamo_liquidado
)
import hashlib
import secrets

app = FastAPI(title="Monte de Piedad API", version="3.0")

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

class RegistrarPagoRequest(BaseModel):
    id_pago: int
    id_empleado: int
    metodo_pago: str  # EFECTIVO, TRANSFERENCIA, TARJETA

class CrearEmpleadoRequest(BaseModel):
    username: str
    password: str
    nombre_completo: str
    rol: str  # ADMIN o EMPLEADO

class VerificarCodigoRequest(BaseModel):
    email: str
    codigo: str
    nueva_password: str

class LiquidarPrestamoRequest(BaseModel):
    id_prestamo: int
    id_empleado: int
    metodo_pago: str = "EFECTIVO"

class ActualizarPerfilRequest(BaseModel):
    id_cliente: int
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    telefono: str
    email: str
    direccion: str


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

def generar_folio():
    """Genera folio único para ticket: TKT-YYYYMMDD-XXXXXX"""
    fecha = datetime.now().strftime('%Y%m%d')
    random = secrets.token_hex(3).upper()  # 6 caracteres hexadecimales
    return f"TKT-{fecha}-{random}"

def generar_firma_digital(folio, id_pago, monto):
    """Genera hash SHA256 como firma digital del ticket"""
    data = f"{folio}-{id_pago}-{monto}-{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()

# ==================== ENDPOINTS ====================

# ROOT
@app.get("/")
def root():
    return {
        "message": "API Monte de Piedad - Activa",
        "version": "3.0",
        "endpoints": [
            "POST /login",
            "POST /registrar_cliente",
            "POST /cliente/prestamo",
            "GET /cliente/mis_prestamos",
            "GET /cliente/cartera",
            "GET /cliente/pagos/{id_prestamo}",
            "GET /configuracion_sistema",
            "PUT /configuracion_sistema/{id}",
            "GET /admin/prestamos_pendientes",
            "POST /admin/aprobar_prestamo",
            "GET /admin/estadisticas",
            "POST /admin/crear_empleado",
            "POST /empleado/registrar_pago",
            "GET /empleado/pagos_pendientes",
            "GET /empleado/corte_caja",
            "GET /tickets/{folio}",
            "POST /verificar_codigo",
            "POST /solicitar_codigo"
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
        
        # ✅ Email de bienvenida
        try:
            nombre_completo = f"{request.nombre} {request.apellido_paterno}"
            email_bienvenida(request.email, nombre_completo)
            print(f"✅ Email bienvenida → {request.email}")
        except Exception as e:
            print(f"⚠️ Error email bienvenida: {e}")
        
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
        
        # ✅ VERIFICAR QUE NO EXISTAN PAGOS ANTES DE GENERARLOS
        cursor.execute("SELECT COUNT(*) FROM pagos WHERE id_prestamo = %s", (id_prestamo,))
        pagos_existentes = cursor.fetchone()[0]
        
        if pagos_existentes == 0:
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
    cursor = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        
        # Obtener datos del préstamo y cliente
        cursor.execute("""
            SELECT pr.*, c.email, c.nombre, c.apellido_paterno,
                   cfg.tasa_interes
            FROM prestamos pr
            JOIN clientes c ON pr.id_cliente = c.id_cliente
            CROSS JOIN configuracion_sistema cfg
            WHERE pr.id_prestamo = %s
        """, (request.id_prestamo,))
        
        prestamo = cursor.fetchone()
        
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        
        nombre_completo = f"{prestamo['nombre']} {prestamo['apellido_paterno']}"
        
        if request.aprobado:
            cursor.execute("UPDATE prestamos SET estado='ACTIVO' WHERE id_prestamo=%s", 
                          (request.id_prestamo,))
            
            # Calcular cuota mensual
            monto = float(prestamo['monto_total'])
            plazo = int(prestamo['plazo_meses'])
            tasa_mensual = float(prestamo['tasa_interes']) / 12
            
            if tasa_mensual == 0:
                cuota = monto / plazo
            else:
                factor = (1 + tasa_mensual) ** plazo
                cuota = monto * (tasa_mensual * factor) / (factor - 1)
            
            # ✅ ENVIAR EMAIL DE APROBACIÓN
            try:
                email_prestamo_aprobado(
                    prestamo['email'],
                    nombre_completo,
                    monto,
                    plazo,
                    cuota,
                    request.id_prestamo
                )
                print(f"✅ Email aprobación → {prestamo['email']}")
            except Exception as e:
                print(f"⚠️ Error email aprobación: {e}")
            
            mensaje = "Préstamo aprobado y cliente notificado"
        else:
            cursor.execute("DELETE FROM pagos WHERE id_prestamo=%s", (request.id_prestamo,))
            cursor.execute("UPDATE prestamos SET estado='RECHAZADO' WHERE id_prestamo=%s", 
                          (request.id_prestamo,))
            
            # ✅ ENVIAR EMAIL DE RECHAZO
            try:
                email_prestamo_rechazado(
                    prestamo['email'],
                    nombre_completo,
                    float(prestamo['monto_total'])
                )
                print(f"✅ Email rechazo → {prestamo['email']}")
            except Exception as e:
                print(f"⚠️ Error email rechazo: {e}")
            
            mensaje = "Préstamo rechazado y cliente notificado"
        
        db.commit()
        return {"status": "success", "message": mensaje}
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


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

# ==================== NUEVOS ENDPOINTS - FASE 1 ====================

# 12. CREAR EMPLEADO (ADMIN)
@app.post("/admin/crear_empleado")
def crear_empleado(request: CrearEmpleadoRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        # Validar que el rol sea válido
        if request.rol.upper() not in ['ADMIN', 'EMPLEADO']:
            raise HTTPException(status_code=400, detail="Rol inválido. Use ADMIN o EMPLEADO")
        
        # Verificar que el username no exista
        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (request.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El usuario ya existe")
        
        cursor.execute("""
            INSERT INTO usuarios (username, password, nombre_completo, rol, estado)
            VALUES (%s, %s, %s, %s, 'Activo')
        """, (request.username, request.password, request.nombre_completo, request.rol.upper()))
        
        db.commit()
        return {"status": "success", "message": f"{request.rol} creado correctamente", "id_usuario": cursor.lastrowid}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 13. REGISTRAR PAGO Y GENERAR TICKET (EMPLEADO)
@app.post("/empleado/registrar_pago")
def registrar_pago(request: RegistrarPagoRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        
        # Verificar que el pago existe y está pendiente
        cursor.execute("""
            SELECT p.*, pr.id_cliente, pr.saldo_pendiente
            FROM pagos p
            JOIN prestamos pr ON p.id_prestamo = pr.id_prestamo
            WHERE p.id_pago = %s
        """, (request.id_pago,))
        pago = cursor.fetchone()
        
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        
        if pago['estado'] == 'PAGADO':
            raise HTTPException(status_code=400, detail="Este pago ya fue registrado")
        
        monto_pago = float(pago['monto'])
        
        # Generar folio y firma
        folio = generar_folio()
        firma = generar_firma_digital(folio, request.id_pago, monto_pago)
        
        # Insertar ticket
        cursor.execute("""
            INSERT INTO tickets_pagos 
            (folio, id_pago, id_empleado, metodo_pago, monto_pagado, firma_digital)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (folio, request.id_pago, request.id_empleado, request.metodo_pago, monto_pago, firma))
        
        id_ticket = cursor.lastrowid
        
        # Actualizar estado del pago
        cursor.execute("""
            UPDATE pagos 
            SET estado = 'PAGADO', fecha_pago = NOW(), cobrado_por = %s
            WHERE id_pago = %s
        """, (request.id_empleado, request.id_pago))
        
        # Actualizar saldo pendiente del préstamo
        nuevo_saldo = float(pago['saldo_pendiente']) - monto_pago
        cursor.execute("""
            UPDATE prestamos 
            SET saldo_pendiente = %s
            WHERE id_prestamo = %s
        """, (nuevo_saldo, pago['id_prestamo']))
        
        # Si saldo es 0, marcar como liquidado
        if nuevo_saldo <= 0.01:
            cursor.execute("""
                UPDATE prestamos 
                SET estado = 'LIQUIDADO'
                WHERE id_prestamo = %s
            """, (pago['id_prestamo'],))
        
        db.commit()
        
        # ✅ Email de ticket
        try:
            cursor.execute("""
                SELECT c.email, c.nombre, c.apellido_paterno, pr.plazo_meses
                FROM clientes c
                JOIN prestamos pr ON c.id_cliente = pr.id_cliente
                WHERE pr.id_prestamo = %s
            """, (pago['id_prestamo'],))
            
            cliente = cursor.fetchone()
            
            if cliente:
                nombre_completo = f"{cliente['nombre']} {cliente['apellido_paterno']}"
                email_ticket_pago(
                    destinatario=cliente['email'],
                    folio=folio,
                    monto=monto_pago,
                    numero_pago=pago['numero_pago'],
                    total_pagos=cliente['plazo_meses'],
                    cliente=nombre_completo
                )
                print(f"✅ Email ticket → {cliente['email']}")
        except Exception as e:
            print(f"⚠️ Error email ticket: {e}")
        
        return {
            "status": "success",
            "message": "Pago registrado correctamente",
            "folio": folio,
            "id_ticket": id_ticket,
            "monto_pagado": monto_pago,
            "nuevo_saldo": nuevo_saldo
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# 14. PAGOS PENDIENTES DEL DÍA (EMPLEADO)
@app.get("/empleado/pagos_pendientes")
def obtener_pagos_pendientes_dia():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                p.id_pago,
                p.numero_pago,
                p.monto,
                p.fecha_vencimiento,
                pr.id_prestamo,
                pr.monto_total,
                pr.saldo_pendiente,
                CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) as nombre_cliente,
                c.telefono
            FROM pagos p
            JOIN prestamos pr ON p.id_prestamo = pr.id_prestamo
            JOIN clientes c ON pr.id_cliente = c.id_cliente
            WHERE p.estado = 'PENDIENTE'
            AND pr.estado IN ('ACTIVO', 'MORA')
            ORDER BY p.fecha_vencimiento ASC
            LIMIT 100
        """)
        pagos = cursor.fetchall()
        for p in pagos:
            p['monto'] = float(p['monto'])
            p['monto_total'] = float(p['monto_total'])
            p['saldo_pendiente'] = float(p['saldo_pendiente'])
            if p['fecha_vencimiento']:
                p['fecha_vencimiento'] = p['fecha_vencimiento'].strftime('%Y-%m-%d')
        return pagos
    finally:
        db.close()

# 15. CORTE DE CAJA (EMPLEADO)
@app.get("/empleado/corte_caja")
def obtener_corte_caja(id_empleado: int = Query(...), fecha: Optional[str] = None):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        if not fecha:
            fecha = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT 
                t.folio,
                t.metodo_pago,
                t.monto_pagado,
                t.fecha_generacion,
                p.numero_pago,
                pr.id_prestamo,
                CONCAT(c.nombre, ' ', c.apellido_paterno) as cliente
            FROM tickets_pagos t
            JOIN pagos p ON t.id_pago = p.id_pago
            JOIN prestamos pr ON p.id_prestamo = pr.id_prestamo
            JOIN clientes c ON pr.id_cliente = c.id_cliente
            WHERE t.id_empleado = %s
            AND DATE(t.fecha_generacion) = %s
            AND t.estado = 'ACTIVO'
            ORDER BY t.fecha_generacion DESC
        """, (id_empleado, fecha))
        
        tickets = cursor.fetchall()
        
        total_efectivo = 0
        total_transferencia = 0
        total_tarjeta = 0
        
        for t in tickets:
            monto = float(t['monto_pagado'])
            t['monto_pagado'] = monto
            t['fecha_generacion'] = t['fecha_generacion'].strftime('%Y-%m-%d %H:%M:%S')
            
            if t['metodo_pago'] == 'EFECTIVO':
                total_efectivo += monto
            elif t['metodo_pago'] == 'TRANSFERENCIA':
                total_transferencia += monto
            elif t['metodo_pago'] == 'TARJETA':
                total_tarjeta += monto
        
        return {
            "fecha": fecha,
            "total_tickets": len(tickets),
            "total_efectivo": total_efectivo,
            "total_transferencia": total_transferencia,
            "total_tarjeta": total_tarjeta,
            "total_general": total_efectivo + total_transferencia + total_tarjeta,
            "tickets": tickets
        }
    finally:
        db.close()

# 16. BUSCAR TICKET POR FOLIO
@app.get("/tickets/{folio}")
def buscar_ticket(folio: str):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                t.*,
                p.numero_pago,
                p.monto as monto_cuota,
                pr.id_prestamo,
                pr.monto_total,
                pr.saldo_pendiente,
                CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) as cliente,
                c.curp,
                u.nombre_completo as empleado
            FROM tickets_pagos t
            JOIN pagos p ON t.id_pago = p.id_pago
            JOIN prestamos pr ON p.id_prestamo = pr.id_prestamo
            JOIN clientes c ON pr.id_cliente = c.id_cliente
            JOIN usuarios u ON t.id_empleado = u.id_usuario
            WHERE t.folio = %s
        """, (folio,))
        
        ticket = cursor.fetchone()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        ticket['monto_pagado'] = float(ticket['monto_pagado'])
        ticket['monto_cuota'] = float(ticket['monto_cuota'])
        ticket['monto_total'] = float(ticket['monto_total'])
        ticket['saldo_pendiente'] = float(ticket['saldo_pendiente'])
        ticket['fecha_generacion'] = ticket['fecha_generacion'].strftime('%Y-%m-%d %H:%M:%S')
        
        return ticket
    finally:
        db.close()

# 17. SOLICITAR CÓDIGO DE RECUPERACIÓN
@app.post("/solicitar_codigo")
def solicitar_codigo(email: str = Query(...)):
    db = conectar()
    cursor = db.cursor()
    try:
        # Verificar que el email existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE username = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="El correo no está registrado")
        
        # Generar código de 6 dígitos
        import random
        codigo = str(random.randint(100000, 999999))
        
        # Guardar código en BD
        cursor.execute("""
            UPDATE usuarios 
            SET codigo_recuperacion = %s, fecha_codigo = NOW()
            WHERE username = %s
        """, (codigo, email))
        
        db.commit()
        
        # TODO: Aquí iría el envío real del email
        # Por ahora solo retornamos éxito
        
        return {
            "status": "success",
            "message": f"Código enviado a {email}",
            "codigo_debug": codigo  # ELIMINAR EN PRODUCCIÓN
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# 18. VERIFICAR CÓDIGO Y CAMBIAR CONTRASEÑA
@app.post("/verificar_codigo")
def verificar_codigo(request: VerificarCodigoRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar código
        cursor.execute("""
            SELECT id_usuario, codigo_recuperacion, fecha_codigo
            FROM usuarios
            WHERE username = %s
        """, (request.email,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if not usuario['codigo_recuperacion']:
            raise HTTPException(status_code=400, detail="No hay código pendiente")
        
        if usuario['codigo_recuperacion'] != request.codigo:
            raise HTTPException(status_code=401, detail="Código incorrecto")
        
        # Verificar que el código no haya expirado (15 minutos)
        if usuario['fecha_codigo']:
            tiempo_transcurrido = datetime.now() - usuario['fecha_codigo']
            if tiempo_transcurrido.total_seconds() > 900:  # 15 minutos
                raise HTTPException(status_code=410, detail="El código ha expirado")
        
        # Actualizar contraseña
        cursor.execute("""
            UPDATE usuarios
            SET password = %s, codigo_recuperacion = NULL, fecha_codigo = NULL
            WHERE username = %s
        """, (request.nueva_password, request.email))
        
        db.commit()
        
        return {"status": "success", "message": "Contraseña actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ==================== ENDPOINTS NUEVOS - LIQUIDACIÓN ====================

@app.post("/empleado/liquidar_prestamo")
def liquidar_prestamo_completo(request: LiquidarPrestamoRequest):
    """Pagar todo el préstamo de una vez con descuento opcional"""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        db.start_transaction()
        
        cursor.execute("""
            SELECT pr.saldo_pendiente, pr.monto_total, pr.plazo_meses,
                   CONCAT(c.nombre, ' ', c.apellido_paterno) as nombre_cliente
            FROM prestamos pr
            JOIN clientes c ON pr.id_cliente = c.id_cliente
            WHERE pr.id_prestamo = %s
        """, (request.id_prestamo,))
        
        prestamo = cursor.fetchone()
        
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        
        saldo = float(prestamo['saldo_pendiente'])
        
        if saldo <= 0:
            raise HTTPException(status_code=400, detail="El préstamo ya está liquidado")
        
        # Descuento 3%
        descuento = saldo * 0.03
        total_a_pagar = saldo - descuento
        
        folio = generar_folio()
        firma = generar_firma_digital(folio, request.id_prestamo, total_a_pagar)
        
        cursor.execute("""
            INSERT INTO tickets_pagos 
            (folio, id_pago, id_empleado, metodo_pago, monto_pagado, firma_digital, tipo)
            VALUES (%s, NULL, %s, %s, %s, %s, 'LIQUIDACION')
        """, (folio, request.id_empleado, request.metodo_pago, total_a_pagar, firma))
        
        id_ticket = cursor.lastrowid
        
        cursor.execute("""
            UPDATE pagos
            SET estado = 'PAGADO', fecha_pago = NOW(), cobrado_por = %s
            WHERE id_prestamo = %s AND estado IN ('PENDIENTE', 'ATRASADO')
        """, (request.id_empleado, request.id_prestamo))
        
        pagos_liquidados = cursor.rowcount
        
        cursor.execute("""
            UPDATE prestamos
            SET saldo_pendiente = 0, 
                estado = 'LIQUIDADO', 
                fecha_liquidacion = NOW()
            WHERE id_prestamo = %s
        """, (request.id_prestamo,))
        
        db.commit()
        
        # ✅ Email de liquidación
        try:
            cursor.execute("""
                SELECT c.email, c.nombre, c.apellido_paterno
                FROM clientes c
                JOIN prestamos pr ON c.id_cliente = pr.id_cliente
                WHERE pr.id_prestamo = %s
            """, (request.id_prestamo,))
            
            cliente = cursor.fetchone()
            
            if cliente:
                nombre_completo = f"{cliente['nombre']} {cliente['apellido_paterno']}"
                email_prestamo_liquidado(
                    destinatario=cliente['email'],
                    nombre=nombre_completo,
                    monto_original=saldo + descuento,
                    descuento=descuento,
                    total_pagado=total_a_pagar,
                    folio=folio
                )
                print(f"✅ Email liquidación → {cliente['email']}")
        except Exception as e:
            print(f"⚠️ Error email liquidación: {e}")
        
        return {
            "status": "success",
            "message": f"Préstamo liquidado para {prestamo['nombre_cliente']}",
            "folio": folio,
            "id_ticket": id_ticket,
            "saldo_anterior": saldo,
            "descuento": descuento,
            "total_pagado": total_a_pagar,
            "pagos_liquidados": pagos_liquidados
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# ==================== ENDPOINT: CALCULAR MORA ====================

@app.post("/sistema/calcular_mora")
def calcular_mora_automatica():
    """Ejecutar diariamente para actualizar estados de mora"""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        try:
            cursor.callproc('calcular_mora_diaria')
            for result in cursor.stored_results():
                data = result.fetchone()
                return {
                    "status": "success",
                    "message": "Mora calculada con procedimiento",
                    "pagos_actualizados": data.get('pagos_actualizados', 0),
                    "prestamos_actualizados": data.get('prestamos_actualizados', 0)
                }
        except:
            pass
        
        cursor.execute("""
            UPDATE pagos p
            JOIN prestamos pr ON p.id_prestamo = pr.id_prestamo
            SET p.estado = 'ATRASADO'
            WHERE p.estado = 'PENDIENTE'
            AND p.fecha_vencimiento < CURDATE()
            AND pr.estado IN ('ACTIVO', 'MORA')
        """)
        
        pagos_actualizados = cursor.rowcount
        
        cursor.execute("""
            UPDATE prestamos pr
            SET pr.estado = 'MORA'
            WHERE pr.estado = 'ACTIVO'
            AND EXISTS (
                SELECT 1 FROM pagos p 
                WHERE p.id_prestamo = pr.id_prestamo 
                AND p.estado = 'ATRASADO'
            )
        """)
        
        prestamos_actualizados = cursor.rowcount
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Mora calculada correctamente",
            "pagos_actualizados": pagos_actualizados,
            "prestamos_actualizados": prestamos_actualizados,
            "ejecutado_en": datetime.now().isoformat()
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# ==================== ENDPOINT: DASHBOARD ADMIN ====================

@app.get("/admin/dashboard_data")
def obtener_dashboard_data():
    """Datos completos para dashboard con gráficos"""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        try:
            cursor.execute("SELECT * FROM vista_dashboard")
            kpis = cursor.fetchone()
        except:
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM clientes) as total_clientes,
                    (SELECT COUNT(*) FROM prestamos WHERE estado = 'ACTIVO') as prestamos_activos,
                    (SELECT COUNT(*) FROM prestamos WHERE estado = 'MORA') as prestamos_mora,
                    (SELECT COALESCE(SUM(monto_total), 0) FROM prestamos WHERE estado IN ('ACTIVO', 'MORA')) as capital_activo,
                    (SELECT COALESCE(SUM(monto_total - saldo_pendiente), 0) FROM prestamos) as monto_recuperado,
                    (SELECT COALESCE(SUM(saldo_pendiente), 0) FROM prestamos WHERE estado IN ('ACTIVO', 'MORA')) as saldo_pendiente
            """)
            kpis = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(fecha_creacion, '%%Y-%%m') as mes,
                SUM(monto_total) as colocacion
            FROM prestamos
            WHERE fecha_creacion >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(fecha_creacion, '%%Y-%%m')
            ORDER BY mes
        """)
        colocacion = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(fecha_pago, '%%Y-%%m') as mes,
                SUM(monto) as cobranza
            FROM pagos
            WHERE estado = 'PAGADO'
            AND fecha_pago >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(fecha_pago, '%%Y-%%m')
            ORDER BY mes
        """)
        cobranza = cursor.fetchall()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN estado = 'ACTIVO' THEN 1 ELSE 0 END) as activos,
                SUM(CASE WHEN estado = 'MORA' THEN 1 ELSE 0 END) as morosos
            FROM prestamos
            WHERE estado IN ('ACTIVO', 'MORA')
        """)
        cartera = cursor.fetchone()
        
        return {
            "status": "success",
            "kpis": {
                "capital_activo": float(kpis['capital_activo']) if kpis['capital_activo'] else 0,
                "monto_recuperado": float(kpis['monto_recuperado']) if kpis['monto_recuperado'] else 0,
                "total_clientes": int(kpis['total_clientes']),
                "prestamos_activos": int(kpis['prestamos_activos']),
                "prestamos_mora": int(kpis['prestamos_mora'])
            },
            "flujo_fondos": {
                "meses": [c['mes'] for c in colocacion],
                "colocacion": [float(c['colocacion']) for c in colocacion],
                "cobranza": [float(c['cobranza']) if c['cobranza'] else 0 for c in cobranza]
            },
            "estado_cartera": {
                "activos": int(cartera['activos']) if cartera['activos'] else 0,
                "morosos": int(cartera['morosos']) if cartera['morosos'] else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# ==================== ENDPOINT: CLIENTES EN RIESGO ====================

@app.get("/admin/clientes_riesgo")
def obtener_clientes_riesgo(limit: int = 5):
    """Top N clientes morosos"""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) as nombre_completo,
                c.curp,
                c.telefono,
                pr.saldo_pendiente,
                MAX(pg.fecha_pago) as ultimo_pago,
                DATEDIFF(NOW(), MAX(pg.fecha_vencimiento)) as dias_atraso
            FROM prestamos pr
            JOIN clientes c ON pr.id_cliente = c.id_cliente
            LEFT JOIN pagos pg ON pr.id_prestamo = pg.id_prestamo AND pg.estado = 'ATRASADO'
            WHERE pr.estado = 'MORA'
            AND pr.saldo_pendiente > 0
            GROUP BY pr.id_prestamo, c.id_cliente
            ORDER BY pr.saldo_pendiente DESC, dias_atraso DESC
            LIMIT %s
        """, (limit,))
        
        clientes = cursor.fetchall()
        
        for cliente in clientes:
            cliente['saldo_pendiente'] = float(cliente['saldo_pendiente'])
        
        return {
            "status": "success",
            "clientes_riesgo": clientes
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

# ==================== ENDPOINT: ACTUALIZAR PERFIL ====================

@app.put("/cliente/perfil")
def actualizar_perfil_cliente(request: ActualizarPerfilRequest):
    """Actualizar datos del perfil del cliente"""
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE clientes
            SET nombre = %s,
                apellido_paterno = %s,
                apellido_materno = %s,
                telefono = %s,
                email = %s,
                direccion = %s
            WHERE id_cliente = %s
        """, (request.nombre, request.apellido_paterno, request.apellido_materno,
              request.telefono, request.email, request.direccion, request.id_cliente))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Perfil actualizado correctamente"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()
