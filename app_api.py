"""
═══════════════════════════════════════════════════════════════════════════════
API FINAL - MONTE SIN PIEDAD
Con Resend, tabla unificada, y variables de entorno para Railway
═══════════════════════════════════════════════════════════════════════════════
"""

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from datetime import datetime, timedelta
import random
import os

# ==================== BREVO API ====================
import requests

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")

# ==================== CONFIGURACIÓN BD (VARIABLES DE ENTORNO) ====================
DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', 'junction.proxy.rlwy.net'),
    'port': int(os.environ.get('MYSQLPORT', '16661')),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD', 'rOhOhfujlMBVGnrTtIYJQLAtxcMlsBOP'),
    'database': os.environ.get('MYSQLDATABASE', 'railway')
}

# ==================== FASTAPI APP ====================
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def conectar():
    return mysql.connector.connect(**DB_CONFIG)

# ==================== MODELOS ====================

class LoginRequest(BaseModel):
    email: str
    password: str

class RegistroClienteRequest(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    email: str
    password: str
    curp: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    no_identificacion: Optional[str] = None
    fecha_nacimiento: Optional[str] = None

class VerificarEmailRequest(BaseModel):
    email: str
    codigo: str

class RecuperacionRequest(BaseModel):
    email: str
    codigo: str
    nueva_password: str

class ActualizarPerfilClienteRequest(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

# ==================== FUNCIONES DE EMAIL (RESEND) ====================

def enviar_email_resend(destinatario: str, asunto: str, html: str):
    """Envía email via API HTTP de Brevo (puerto 443). Nombre legacy mantenido para compatibilidad."""
    if not BREVO_API_KEY:
        raise Exception("BREVO_API_KEY no configurada en las variables de entorno de Railway")

    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": "Monte de Piedad", "email": "hangelica957@gmail.com"},
        "to": [{"email": destinatario}],
        "subject": asunto,
        "htmlContent": html,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            msg_id = response.json().get("messageId", "n/a")
            print(f"✅ Email enviado a {destinatario} — messageId: {msg_id}")
            return True

        error_detail = response.json().get("message", response.text)
        raise Exception(f"Brevo API error {response.status_code}: {error_detail}")
    except requests.exceptions.Timeout:
        raise Exception("Timeout al conectar con Brevo API")
    except Exception as e:
        print(f"❌ Error Brevo API: {e}")
        raise Exception(f"No se pudo enviar el correo: {str(e)}")

def email_codigo_recuperacion(destinatario: str, codigo: str, nombre: str = "Usuario"):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#A6032F,#800020);padding:40px;text-align:center;">
          <h1 style="color:white;margin:0;font-size:24px;font-weight:700;">🔐 RECUPERACIÓN DE CONTRASEÑA</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="color:#475569;line-height:1.6;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#475569;line-height:1.6;">Recibimos una solicitud para restablecer tu contraseña en <strong>Monte de Piedad</strong>.</p>
          <p style="color:#475569;line-height:1.6;">Usa el siguiente código de verificación:</p>
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:30px;text-align:center;margin:30px 0;">
            <div style="font-size:40px;font-weight:900;color:#A6032F;letter-spacing:12px;font-family:'Courier New',monospace;">{codigo}</div>
            <div style="font-size:12px;color:#64748b;margin-top:10px;text-transform:uppercase;">Código de verificación</div>
          </div>
          <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:15px;border-radius:8px;margin:20px 0;">
            <p style="font-size:14px;color:#92400e;margin:0;">⏰ <strong>Este código expira en 15 minutos.</strong><br>🔒 Si no solicitaste este cambio, ignora este mensaje.</p>
          </div>
          <p style="color:#64748b;font-size:14px;line-height:1.6;margin-top:30px;">Por tu seguridad, nunca compartas este código con nadie.</p>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
          <p style="margin-top:5px;">Este es un correo automático, no respondas a esta dirección.</p>
        </div>
      </div>
    </body>
    </html>
    """
    return enviar_email_resend(destinatario, f"🔐 Código de Recuperación: {codigo}", html)

def email_verificacion_cuenta(destinatario: str, codigo: str, nombre: str):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#10b981,#059669);padding:40px;text-align:center;">
          <h1 style="color:white;margin:0;font-size:24px;">✅ VERIFICA TU EMAIL</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="color:#475569;line-height:1.6;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#475569;line-height:1.6;">¡Bienvenido a <strong>Monte de Piedad</strong>! Para completar tu registro, verifica tu email con el siguiente código:</p>
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:30px;text-align:center;margin:30px 0;">
            <div style="font-size:40px;font-weight:900;color:#10b981;letter-spacing:12px;font-family:'Courier New',monospace;">{codigo}</div>
            <div style="font-size:12px;color:#64748b;margin-top:10px;">Código de verificación</div>
          </div>
          <div style="background:#dbeafe;border-left:4px solid #3b82f6;padding:15px;border-radius:8px;">
            <p style="font-size:14px;color:#1e40af;margin:0;">ℹ️ <strong>Este código expira en 15 minutos.</strong><br>Si no solicitaste esta cuenta, ignora este mensaje.</p>
          </div>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte de Piedad</p>
        </div>
      </div>
    </body>
    </html>
    """
    return enviar_email_resend(destinatario, "✅ Verifica tu cuenta - Monte de Piedad", html)

def email_bienvenida(destinatario: str, nombre: str):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#A6032F,#800020);padding:50px 30px;text-align:center;">
          <h1 style="color:white;margin:0 0 10px 0;font-size:28px;">¡Bienvenido a Monte de Piedad! 🎉</h1>
          <p style="color:rgba(255,255,255,0.9);margin:0;">Tu cuenta ha sido creada exitosamente</p>
        </div>
        <div style="padding:40px 30px;">
          <div style="background:linear-gradient(135deg,#f1f5f9,#e2e8f0);padding:25px;border-radius:12px;margin:20px 0;text-align:center;">
            <p style="font-size:18px;color:#1e293b;font-weight:600;margin:0;">Hola {nombre}, ¡Es un placer tenerte con nosotros!</p>
          </div>
          <p style="color:#475569;line-height:1.8;margin:25px 0;">Tu cuenta está lista. Ahora puedes acceder a todos nuestros servicios financieros.</p>
          <p style="color:#64748b;font-size:14px;line-height:1.6;margin-top:30px;">Si tienes alguna duda, nuestro equipo está disponible para asistirte.</p>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
        </div>
      </div>
    </body>
    </html>
    """
    return enviar_email_resend(destinatario, f"🎉 ¡Bienvenido a Monte de Piedad, {nombre}!", html)


def enviar_email_bienvenida_background(destinatario: str, nombre: str):
    """Wrapper para ejecución en segundo plano sin romper la respuesta del endpoint."""
    try:
        email_bienvenida(destinatario, nombre)
    except Exception as e:
        print(f"⚠️ Email de bienvenida no enviado: {e}")


def enviar_email_verificacion_background(destinatario: str, codigo: str, nombre: str):
    """Wrapper para ejecución en segundo plano sin romper la respuesta del endpoint."""
    try:
        email_verificacion_cuenta(destinatario, codigo, nombre)
    except Exception as e:
        print(f"⚠️ Email de verificación no enviado: {e}")


def enviar_email_codigo_recuperacion_background(destinatario: str, codigo: str, nombre: str):
    """Wrapper para ejecución en segundo plano sin romper la respuesta del endpoint."""
    try:
        email_codigo_recuperacion(destinatario, codigo, nombre)
    except Exception as e:
        print(f"⚠️ Email de recuperación no enviado: {e}")

# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    return {
        "app": "Monte SIN Piedad API",
        "version": "2.0",
        "status": "✅ Operativo"
    }

@app.post("/login")
def login_unificado(request: LoginRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno, 
                   email, rol, activo, email_verificado, curp, telefono
            FROM usuarios
            WHERE email = %s AND password = %s
        """, (request.email, request.password))

        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if not usuario.get('activo', True):
            raise HTTPException(status_code=403, detail="Cuenta desactivada")

        if not usuario.get('email_verificado', False):
            raise HTTPException(status_code=403, detail="Email no verificado. Revisa tu correo.")

        return {
            "status": "success",
            "message": "Login exitoso",
            "usuario": {
                "id_usuario":        usuario['id_usuario'],
                "nombre":            usuario['nombre'],
                "apellido_paterno":  usuario.get('apellido_paterno', ''),
                "apellido_materno":  usuario.get('apellido_materno', ''),
                "email":             usuario['email'],
                "rol":               usuario['rol'],
                "curp":              usuario.get('curp'),
                "telefono":          usuario.get('telefono'),
                # ✅ FIX: bool() convierte TINYINT(1) de MySQL a true/false JSON
                # MySQL devuelve 1/0, Android espera true/false → JsonSyntaxException sin esto
                "email_verificado":  bool(usuario.get('email_verificado', False))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.post("/registrar_cliente")
def registrar_cliente(request: RegistroClienteRequest, background_tasks: BackgroundTasks):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (request.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        if request.curp:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE curp = %s", (request.curp,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="El CURP ya está registrado")

        codigo_verificacion = str(random.randint(100000, 999999))

        cursor.execute("""
            INSERT INTO usuarios 
            (nombre, apellido_paterno, apellido_materno, email, password, rol,
             curp, telefono, direccion, no_identificacion, fecha_nacimiento, activo,
             email_verificado, codigo_verificacion, fecha_codigo_verificacion)
            VALUES (%s, %s, %s, %s, %s, 'Cliente', %s, %s, %s, %s, %s, TRUE, FALSE, %s, NOW())
        """, (
            request.nombre, request.apellido_paterno, request.apellido_materno,
            request.email, request.password, request.curp, request.telefono,
            request.direccion, request.no_identificacion, request.fecha_nacimiento,
            codigo_verificacion
        ))

        db.commit()
        id_cliente = cursor.lastrowid

        # Enviar email en background para evitar timeouts en cliente Android
        background_tasks.add_task(
            enviar_email_verificacion_background,
            request.email,
            codigo_verificacion,
            request.nombre
        )

        return {
            "status": "success",
            "message": "Registro exitoso. Verifica tu email para activar tu cuenta.",
            "requiere_verificacion": True,
            "id_cliente": id_cliente
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.post("/verificar_email")
def verificar_email(request: VerificarEmailRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, codigo_verificacion, fecha_codigo_verificacion, email_verificado
            FROM usuarios WHERE email = %s
        """, (request.email,))

        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if usuario['email_verificado']:
            return {"status": "success", "message": "El email ya estaba verificado"}

        if usuario['codigo_verificacion'] != request.codigo:
            raise HTTPException(status_code=401, detail="Código incorrecto")

        if usuario['fecha_codigo_verificacion']:
            tiempo = datetime.now() - usuario['fecha_codigo_verificacion']
            if tiempo.total_seconds() > 900:
                raise HTTPException(status_code=410, detail="Código expirado. Solicita uno nuevo.")

        cursor.execute("""
            UPDATE usuarios
            SET email_verificado = TRUE, codigo_verificacion = NULL, fecha_codigo_verificacion = NULL
            WHERE email = %s
        """, (request.email,))
        db.commit()

        return {"status": "success", "message": "Email verificado correctamente. Ya puedes iniciar sesión."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.post("/reenviar_codigo_verificacion")
def reenviar_codigo(email: str = Query(...)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, nombre, email_verificado FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if usuario['email_verificado']:
            raise HTTPException(status_code=400, detail="El email ya está verificado")

        codigo = str(random.randint(100000, 999999))
        cursor.execute("""
            UPDATE usuarios SET codigo_verificacion = %s, fecha_codigo_verificacion = NOW()
            WHERE email = %s
        """, (codigo, email))
        db.commit()

        email_verificacion_cuenta(email, codigo, usuario['nombre'])

        return {"status": "success", "message": "Nuevo código enviado a tu email"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.post("/solicitar_codigo")
@app.post("/solicitor_codigo")
def solicitar_codigo_recuperacion(background_tasks: BackgroundTasks, email: str = Query(...)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, nombre, email FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="El correo no está registrado")

        codigo = str(random.randint(100000, 999999))
        cursor.execute("""
            UPDATE usuarios SET codigo_recuperacion = %s, fecha_codigo = NOW() WHERE email = %s
        """, (codigo, email))
        db.commit()

        # Enviar email en background para evitar timeouts en cliente Android
        background_tasks.add_task(enviar_email_codigo_recuperacion_background, email, codigo, usuario['nombre'])

        return {"status": "success", "message": f"Código enviado a {email}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.post("/verificar_codigo")
def verificar_codigo(request: RecuperacionRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, codigo_recuperacion, fecha_codigo FROM usuarios WHERE email = %s
        """, (request.email,))
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if not usuario['codigo_recuperacion']:
            raise HTTPException(status_code=400, detail="No hay código de recuperación pendiente")
        if usuario['codigo_recuperacion'] != request.codigo:
            raise HTTPException(status_code=401, detail="Código incorrecto")

        if usuario['fecha_codigo']:
            tiempo = datetime.now() - usuario['fecha_codigo']
            if tiempo.total_seconds() > 900:
                raise HTTPException(status_code=410, detail="El código ha expirado. Solicita uno nuevo.")

        cursor.execute("""
            UPDATE usuarios
            SET password = %s, codigo_recuperacion = NULL, fecha_codigo = NULL
            WHERE email = %s
        """, (request.nueva_password, request.email))
        db.commit()

        return {"status": "success", "message": "Contraseña actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

# ==================== ENDPOINTS DE CONSULTA ====================

@app.get("/usuarios")
def obtener_usuarios(rol: Optional[str] = None):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        if rol:
            cursor.execute("""
                SELECT id_usuario, nombre, apellido_paterno, apellido_materno, 
                       email, rol, activo, email_verificado, fecha_registro
                FROM usuarios WHERE rol = %s ORDER BY fecha_registro DESC
            """, (rol,))
        else:
            cursor.execute("""
                SELECT id_usuario, nombre, apellido_paterno, apellido_materno, 
                       email, rol, activo, email_verificado, fecha_registro
                FROM usuarios ORDER BY fecha_registro DESC
            """)

        usuarios = cursor.fetchall()
        # ✅ FIX: convertir todos los booleanos de MySQL a bool Python
        for u in usuarios:
            u['activo']           = bool(u.get('activo', False))
            u['email_verificado'] = bool(u.get('email_verificado', False))

        return {"status": "success", "total": len(usuarios), "usuarios": usuarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.get("/usuario/{id_usuario}")
def obtener_usuario(id_usuario: int):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno,
                   email, rol, curp, telefono, direccion, no_identificacion,
                   activo, email_verificado, fecha_registro
            FROM usuarios WHERE id_usuario = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # ✅ FIX: convertir booleanos
        usuario['activo']           = bool(usuario.get('activo', False))
        usuario['email_verificado'] = bool(usuario.get('email_verificado', False))

        return {"status": "success", "usuario": usuario}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/cliente/{id_cliente}/perfil")
def obtener_perfil_cliente(id_cliente: int):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno, email,
                   curp, telefono, direccion, no_identificacion, fecha_nacimiento
            FROM usuarios
            WHERE id_usuario = %s AND rol = 'Cliente'
        """, (id_cliente,))
        perfil = cursor.fetchone()
        if not perfil:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if perfil.get('fecha_nacimiento') and hasattr(perfil['fecha_nacimiento'], 'isoformat'):
            perfil['fecha_nacimiento'] = perfil['fecha_nacimiento'].isoformat()
        return {"status": "success", "perfil": perfil}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.put("/cliente/{id_cliente}/perfil")
def actualizar_perfil_cliente(id_cliente: int, request: ActualizarPerfilClienteRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE usuarios
            SET nombre=%s, apellido_paterno=%s, apellido_materno=%s, telefono=%s, direccion=%s
            WHERE id_usuario=%s AND rol='Cliente'
        """, (
            request.nombre,
            request.apellido_paterno,
            request.apellido_materno,
            request.telefono,
            request.direccion,
            id_cliente
        ))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return {"status": "success", "message": "Perfil actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== MODELOS ADICIONALES ====================

class PrestamoRequest(BaseModel):
    id_cliente: int
    monto: float
    plazo_meses: int

class AprobarPrestamoRequest(BaseModel):
    id_prestamo: int
    accion: str  # "aprobar" o "rechazar"
    id_empleado: int

class CrearEmpleadoRequest(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    email: str
    password: str
    telefono: Optional[str] = None
    rol: str = "Empleado"

class RegistrarPagoRequest(BaseModel):
    id_pago: int
    id_empleado: int

class ConfiguracionRequest(BaseModel):
    tasa_interes: Optional[float] = None
    plazo_maximo: Optional[int] = None
    monto_minimo: Optional[float] = None
    monto_maximo: Optional[float] = None

# ==================== ENDPOINTS CLIENTE ====================

# 5. SOLICITAR PRÉSTAMO
@app.post("/cliente/prestamo")
@app.post("/cliente/solicitar_credito")
def solicitar_prestamo(request: PrestamoRequest):
    TASA = 0.05
    if request.monto < 1000 or request.monto > 50000:
        raise HTTPException(status_code=400, detail="Monto debe estar entre $1,000 y $50,000")
    if request.plazo_meses not in [6, 12, 24, 36, 48]:
        raise HTTPException(status_code=400, detail="Plazo inválido. Opciones: 6, 12, 24, 36, 48 meses")

    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE id_usuario = %s", (request.id_cliente,))
        u = cursor.fetchone()
        if not u:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        cursor.execute("SELECT id_prestamo FROM prestamos WHERE id_cliente = %s AND estado = 'PENDIENTE'", (request.id_cliente,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya tienes una solicitud pendiente")

        plazo = request.plazo_meses
        cuota = request.monto * (TASA * (1 + TASA)**plazo) / ((1 + TASA)**plazo - 1)
        saldo = round(cuota * plazo, 2)

        cursor.execute("""
            INSERT INTO prestamos (id_cliente, monto_total, saldo_pendiente, tasa_interes, plazo_meses, estado, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, 'PENDIENTE', NOW())
        """, (request.id_cliente, request.monto, saldo, TASA, plazo))
        db.commit()

        return {"status": "success", "message": "Solicitud enviada. Un empleado la revisará pronto."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 6. MIS PRÉSTAMOS
@app.get("/cliente/mis_prestamos")
@app.get("/cliente/{id_cliente_path}/prestamos")
def obtener_mis_prestamos(id_cliente: Optional[int] = Query(None), id_cliente_path: Optional[int] = None):
    if id_cliente is None and id_cliente_path is not None:
        id_cliente = id_cliente_path
    if id_cliente is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Se requiere id_cliente")
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.id_prestamo,
                   CONCAT('MSP-', p.id_prestamo) AS folio,
                   p.monto_total, p.saldo_pendiente, p.tasa_interes,
                   p.plazo_meses, p.estado,
                   p.fecha_creacion, p.fecha_aprobacion,
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo AND g.estado = 'pagado') AS pagos_realizados,
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo) AS total_pagos
            FROM prestamos p
            WHERE p.id_cliente = %s
            ORDER BY p.fecha_creacion DESC
        """, (id_cliente,))
        prestamos = cursor.fetchall()
        for p in prestamos:
            for c in ['fecha_creacion', 'fecha_aprobacion']:
                if p.get(c) and hasattr(p[c], 'isoformat'):
                    p[c] = p[c].isoformat()
            p['monto_total']     = float(p['monto_total'] or 0)
            p['saldo_pendiente'] = float(p['saldo_pendiente'] or 0)
            p['tasa_interes']    = float(p['tasa_interes'] or 0)
        return prestamos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 7. CARTERA (resumen financiero del cliente)
@app.get("/cliente/cartera")
@app.get("/cliente/{id_cliente_path}/cartera")
def obtener_cartera(id_cliente: Optional[int] = Query(None), id_cliente_path: Optional[int] = None):
    if id_cliente is None and id_cliente_path is not None:
        id_cliente = id_cliente_path
    if id_cliente is None:
        raise HTTPException(status_code=400, detail="Se requiere id_cliente")
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(monto_total), 0)     AS capital_otorgado,
                COALESCE(SUM(saldo_pendiente), 0) AS saldo_pendiente,
                COUNT(*)                           AS total_prestamos,
                SUM(CASE WHEN estado = 'ACTIVO'    THEN 1 ELSE 0 END) AS activos,
                SUM(CASE WHEN estado = 'MOROSO'    THEN 1 ELSE 0 END) AS morosos,
                SUM(CASE WHEN estado = 'LIQUIDADO' THEN 1 ELSE 0 END) AS liquidados,
                SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) AS pendientes
            FROM prestamos WHERE id_cliente = %s
        """, (id_cliente,))
        row = cursor.fetchone()

        cursor.execute("""
            SELECT COALESCE(SUM(g.monto), 0) AS total_pagado
            FROM pagos g
            JOIN prestamos p ON g.id_prestamo = p.id_prestamo
            WHERE p.id_cliente = %s AND g.estado = 'pagado'
        """, (id_cliente,))
        pagos = cursor.fetchone()

        # Próximo pago
        cursor.execute("""
            SELECT g.fecha_vencimiento, g.monto, g.numero_pago,
                   CONCAT('MSP-', p.id_prestamo) AS folio
            FROM pagos g
            JOIN prestamos p ON g.id_prestamo = p.id_prestamo
            WHERE p.id_cliente = %s AND g.estado = 'pendiente' AND p.estado = 'ACTIVO'
            ORDER BY g.fecha_vencimiento ASC
            LIMIT 1
        """, (id_cliente,))
        proximo = cursor.fetchone()
        if proximo and proximo.get('fecha_vencimiento') and hasattr(proximo['fecha_vencimiento'], 'isoformat'):
            proximo['fecha_vencimiento'] = proximo['fecha_vencimiento'].isoformat()
            proximo['monto'] = float(proximo['monto'] or 0)

        return {
            "status": "success",
            "capital_otorgado":  float(row['capital_otorgado'] or 0),
            "saldo_pendiente":   float(row['saldo_pendiente'] or 0),
            "total_pagado":      float(pagos['total_pagado'] or 0),
            "total_prestamos":   row['total_prestamos'],
            "activos":           row['activos'],
            "morosos":           row['morosos'],
            "liquidados":        row['liquidados'],
            "pendientes":        row['pendientes'],
            "proximo_pago":      proximo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 8. CALENDARIO DE PAGOS
@app.get("/cliente/pagos/{id_prestamo}")
@app.get("/cliente/{id_cliente_path}/prestamos/{id_prestamo}/pagos")
def obtener_pagos(id_prestamo: int, id_cliente_path: Optional[int] = None):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_pago, numero_pago, fecha_vencimiento, monto, estado, fecha_pago
            FROM pagos WHERE id_prestamo = %s ORDER BY numero_pago
        """, (id_prestamo,))
        pagos = cursor.fetchall()
        for p in pagos:
            for c in ['fecha_vencimiento', 'fecha_pago']:
                if p.get(c) and hasattr(p[c], 'isoformat'):
                    p[c] = p[c].isoformat()
            p['monto'] = float(p['monto'] or 0)
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 9. CONFIGURACIÓN (GET)
@app.get("/configuracion_sistema")
def obtener_configuracion():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM configuracion_sistema ORDER BY id_config ASC")
        config = cursor.fetchall()
        for row in config:
            row['tasa_interes'] = float(row.get('tasa_interes', 0) or 0)
            row['monto_minimo'] = float(row.get('monto_minimo', 0) or 0)
            row['monto_maximo'] = float(row.get('monto_maximo', 0) or 0)
            row['plazo_maximo'] = int(row.get('plazo_maximo', 0) or 0)
            if row.get('fecha_actualizacion') and hasattr(row['fecha_actualizacion'], 'isoformat'):
                row['fecha_actualizacion'] = row['fecha_actualizacion'].isoformat()
        return {"status": "success", "configuracion": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 10. CONFIGURACIÓN (PUT)
@app.put("/configuracion_sistema/{id_config}")
def actualizar_configuracion(id_config: int, request: ConfiguracionRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        campos = []
        valores = []

        if request.tasa_interes is not None:
            campos.append("tasa_interes = %s")
            valores.append(str(float(request.tasa_interes)))
        if request.plazo_maximo is not None:
            campos.append("plazo_maximo = %s")
            valores.append(int(request.plazo_maximo))
        if request.monto_minimo is not None:
            campos.append("monto_minimo = %s")
            valores.append(str(float(request.monto_minimo)))
        if request.monto_maximo is not None:
            campos.append("monto_maximo = %s")
            valores.append(str(float(request.monto_maximo)))

        if not campos:
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

        campos.append("fecha_actualizacion = NOW()")
        query = f"UPDATE configuracion_sistema SET {', '.join(campos)} WHERE id_config = %s"
        valores.append(id_config)

        cursor.execute(query, tuple(valores))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        return {"status": "success", "message": "Configuración actualizada"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== ENDPOINTS ADMIN ====================

# 11. PRÉSTAMOS PENDIENTES
@app.get("/admin/prestamos_pendientes")
def obtener_prestamos_pendientes():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT p.id_prestamo, CONCAT('MSP-', p.id_prestamo) AS folio,
                   p.monto_total, p.saldo_pendiente, p.tasa_interes, p.plazo_meses,
                   p.estado, p.fecha_creacion,
                   u.nombre, u.apellido_paterno, u.curp, u.telefono, u.email
            FROM prestamos p
            JOIN usuarios u ON p.id_cliente = u.id_usuario
            WHERE p.estado = 'PENDIENTE'
            ORDER BY p.fecha_creacion ASC
        """)
        prestamos = cursor.fetchall()
        for p in prestamos:
            if p.get('fecha_creacion') and hasattr(p['fecha_creacion'], 'isoformat'):
                p['fecha_creacion'] = p['fecha_creacion'].isoformat()
            p['monto_total']     = float(p['monto_total'] or 0)
            p['saldo_pendiente'] = float(p['saldo_pendiente'] or 0)
            p['tasa_interes']    = float(p['tasa_interes'] or 0)
        return prestamos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 12. APROBAR / RECHAZAR PRÉSTAMO
@app.post("/admin/aprobar_prestamo")
def procesar_prestamo(request: AprobarPrestamoRequest):
    from datetime import date, timedelta

    if request.accion not in ["aprobar", "rechazar"]:
        raise HTTPException(status_code=400, detail="Acción inválida. Usa 'aprobar' o 'rechazar'")

    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM prestamos WHERE id_prestamo = %s", (request.id_prestamo,))
        prestamo = cursor.fetchone()
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        if prestamo['estado'] != 'PENDIENTE':
            raise HTTPException(status_code=400, detail="El préstamo no está en estado PENDIENTE")

        if request.accion == "aprobar":
            capital = float(prestamo['monto_total'])
            plazo   = int(prestamo['plazo_meses'])
            tasa    = float(prestamo['tasa_interes'])
            cuota   = capital * (tasa * (1 + tasa)**plazo) / ((1 + tasa)**plazo - 1)
            saldo   = round(cuota * plazo, 2)
            hoy     = date.today()

            cursor.execute("""
                UPDATE prestamos SET estado='ACTIVO', saldo_pendiente=%s,
                fecha_aprobacion=NOW(), id_aprobador=%s WHERE id_prestamo=%s
            """, (saldo, request.id_empleado, request.id_prestamo))

            for i in range(1, plazo + 1):
                fecha_venc = hoy + timedelta(days=30 * i)
                cursor.execute("""
                    INSERT INTO pagos (id_prestamo, numero_pago, fecha_vencimiento, monto, estado)
                    VALUES (%s, %s, %s, %s, 'pendiente')
                """, (request.id_prestamo, i, fecha_venc, round(cuota, 2)))

            db.commit()
            return {"status": "success", "message": f"Préstamo aprobado. Se generaron {plazo} pagos."}
        else:
            cursor.execute(
                "UPDATE prestamos SET estado='RECHAZADO', id_aprobador=%s WHERE id_prestamo=%s",
                (request.id_empleado, request.id_prestamo)
            )
            db.commit()
            return {"status": "success", "message": "Préstamo rechazado."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 13. ESTADÍSTICAS
@app.get("/admin/estadisticas")
def obtener_estadisticas():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vista_dashboard LIMIT 1")
        row = cursor.fetchone() or {}

        return {
            "total_clientes": int(row.get('total_clientes', 0) or 0),
            "prestamos_activos": int(row.get('prestamos_activos', 0) or 0),
            "capital_otorgado": float(row.get('capital_colocado', 0) or 0),
            "saldo_pendiente": float(row.get('saldo_pendiente_total', 0) or 0),
            "monto_recuperado": float(row.get('recaudacion_total', 0) or 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 14. CREAR EMPLEADO
@app.post("/admin/crear_empleado")
def crear_empleado(request: CrearEmpleadoRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (request.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        rol = (request.rol or "Empleado").strip().title()
        if rol not in ["Empleado", "Admin"]:
            raise HTTPException(status_code=400, detail="Rol inválido. Usa 'Empleado' o 'Admin'")

        cursor.execute("""
            INSERT INTO usuarios (nombre, apellido_paterno, apellido_materno, email, password,
                                  rol, telefono, activo, email_verificado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)
        """, (request.nombre, request.apellido_paterno, request.apellido_materno,
              request.email, request.password, rol, request.telefono))
        db.commit()
        id_empleado = cursor.lastrowid

        return {"status": "success", "message": f"{rol} creado exitosamente", "id_empleado": id_empleado}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== ENDPOINTS EMPLEADO ====================

# 15. REGISTRAR PAGO
@app.post("/empleado/registrar_pago")
def registrar_pago(request: RegistrarPagoRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pagos WHERE id_pago = %s", (request.id_pago,))
        pago = cursor.fetchone()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        if pago['estado'] == 'pagado':
            raise HTTPException(status_code=400, detail="Este pago ya fue registrado")

        monto       = float(pago['monto'])
        id_prestamo = pago['id_prestamo']

        cursor.execute("UPDATE pagos SET estado='pagado', fecha_pago=NOW() WHERE id_pago=%s", (request.id_pago,))
        cursor.execute("""
            UPDATE prestamos SET saldo_pendiente = GREATEST(0, saldo_pendiente - %s)
            WHERE id_prestamo = %s
        """, (monto, id_prestamo))

        # Verificar si se liquidó
        cursor.execute("SELECT saldo_pendiente FROM prestamos WHERE id_prestamo = %s", (id_prestamo,))
        row = cursor.fetchone()
        if row and float(row['saldo_pendiente']) == 0:
            cursor.execute("UPDATE prestamos SET estado='LIQUIDADO' WHERE id_prestamo=%s", (id_prestamo,))

        # Guardar en tickets_pagos con columnas reales
        import hashlib, time
        folio = f"T-{request.id_pago}-{int(time.time())}"
        firma = hashlib.sha256(f"{request.id_pago}{monto}{time.time()}".encode()).hexdigest()[:64]
        liquidado = float(row['saldo_pendiente']) == 0 if row else False
        cursor.execute("""
            INSERT INTO tickets_pagos 
                (folio, id_pago, id_empleado, metodo_pago, monto_pagado, fecha_generacion, firma_digital, estado, tipo)
            VALUES (%s, %s, %s, 'EFECTIVO', %s, NOW(), %s, 'ACTIVO', %s)
        """, (folio, request.id_pago, request.id_empleado, monto, firma,
              'LIQUIDACION' if liquidado else 'PAGO'))

        db.commit()
        return {
            "status":      "success",
            "message":     f"Pago #{pago['numero_pago']} registrado exitosamente",
            "monto":       monto,
            "id_prestamo": id_prestamo
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 16. PAGOS PENDIENTES
@app.get("/empleado/pagos_pendientes")
def obtener_pagos_pendientes():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT g.id_pago, g.id_prestamo, g.numero_pago,
                   g.fecha_vencimiento, g.monto, g.estado,
                   p.monto_total,
                   CONCAT('MSP-', p.id_prestamo) AS folio,
                   CONCAT(u.nombre, ' ', u.apellido_paterno, ' ', COALESCE(u.apellido_materno, '')) AS nombre_cliente,
                   u.nombre, u.apellido_paterno, u.telefono
            FROM pagos g
            JOIN prestamos p ON g.id_prestamo = p.id_prestamo
            JOIN usuarios u ON p.id_cliente = u.id_usuario
            WHERE g.estado = 'pendiente' AND p.estado IN ('ACTIVO', 'MOROSO')
            ORDER BY g.fecha_vencimiento ASC
        """)
        pagos = cursor.fetchall()
        for p in pagos:
            if p.get('fecha_vencimiento') and hasattr(p['fecha_vencimiento'], 'isoformat'):
                p['fecha_vencimiento'] = p['fecha_vencimiento'].isoformat()
            p['monto'] = float(p['monto'] or 0)
            p['monto_total'] = float(p['monto_total'] or 0)
            p['nombre_cliente'] = (p.get('nombre_cliente') or '').strip() or None
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 17. CORTE DE CAJA
@app.get("/empleado/corte_caja")
def obtener_corte_caja(id_empleado: int = Query(...), fecha: Optional[str] = Query(None)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        fecha_filtro = fecha if fecha else datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT COUNT(*) AS total_pagos,
                   COALESCE(SUM(monto_pagado), 0) AS total_cobrado
            FROM tickets_pagos
            WHERE DATE(fecha_generacion) = %s AND estado = 'ACTIVO'
        """, (fecha_filtro,))
        corte = cursor.fetchone()

        cursor.execute("""
            SELECT t.id_ticket, t.folio, t.monto_pagado, t.fecha_generacion,
                   t.metodo_pago, t.tipo,
                   CONCAT('MSP-', p.id_prestamo) AS folio_prestamo,
                   u.nombre, u.apellido_paterno
            FROM tickets_pagos t
            JOIN pagos g ON t.id_pago = g.id_pago
            JOIN prestamos p ON g.id_prestamo = p.id_prestamo
            JOIN usuarios u ON p.id_cliente = u.id_usuario
            WHERE DATE(t.fecha_generacion) = %s AND t.estado = 'ACTIVO'
            ORDER BY t.fecha_generacion DESC
        """, (fecha_filtro,))
        movimientos = cursor.fetchall()
        for m in movimientos:
            if m.get('fecha_generacion') and hasattr(m['fecha_generacion'], 'isoformat'):
                m['fecha_generacion'] = m['fecha_generacion'].isoformat()
            m['monto_pagado'] = float(m['monto_pagado'] or 0)

        return {
            "status":        "success",
            "fecha":         fecha_filtro,
            "total_pagos":   corte['total_pagos'],
            "total_cobrado": float(corte['total_cobrado'] or 0),
            "movimientos":   movimientos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# 18. BUSCAR TICKET POR FOLIO
@app.get("/tickets/{folio}")
def buscar_ticket(folio: str):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Extraer id_prestamo del folio (MSP-34 → 34)
        id_prestamo = int(folio.replace("MSP-", "").strip())

        cursor.execute("""
            SELECT p.id_prestamo, CONCAT('MSP-', p.id_prestamo) AS folio,
                   p.monto_total, p.saldo_pendiente, p.tasa_interes,
                   p.plazo_meses, p.estado, p.fecha_creacion, p.fecha_aprobacion,
                   u.nombre, u.apellido_paterno, u.apellido_materno,
                   u.curp, u.telefono, u.email,
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo AND g.estado = 'pagado') AS pagos_realizados,
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo) AS total_pagos
            FROM prestamos p
            JOIN usuarios u ON p.id_cliente = u.id_usuario
            WHERE p.id_prestamo = %s
        """, (id_prestamo,))

        prestamo = cursor.fetchone()
        if not prestamo:
            raise HTTPException(status_code=404, detail=f"Ticket {folio} no encontrado")

        for c in ['fecha_creacion', 'fecha_aprobacion']:
            if prestamo.get(c) and hasattr(prestamo[c], 'isoformat'):
                prestamo[c] = prestamo[c].isoformat()
        prestamo['monto_total']     = float(prestamo['monto_total'] or 0)
        prestamo['saldo_pendiente'] = float(prestamo['saldo_pendiente'] or 0)
        prestamo['tasa_interes']    = float(prestamo['tasa_interes'] or 0)

        # Pagos del ticket
        cursor.execute("""
            SELECT id_pago, numero_pago, fecha_vencimiento, monto, estado, fecha_pago
            FROM pagos WHERE id_prestamo = %s ORDER BY numero_pago
        """, (id_prestamo,))
        pagos = cursor.fetchall()
        for p in pagos:
            for c in ['fecha_vencimiento', 'fecha_pago']:
                if p.get(c) and hasattr(p[c], 'isoformat'):
                    p[c] = p[c].isoformat()
            p['monto'] = float(p['monto'] or 0)

        prestamo['pagos'] = pagos
        return {"status": "success", "ticket": prestamo}
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de folio inválido. Usa MSP-{número}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
