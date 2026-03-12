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
import json

# ==================== BREVO API ====================
import requests

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")

# ==================== CONFIGURACIÓN BD (VARIABLES DE ENTORNO) ====================
DB_CONFIG = {
    'host':     os.environ.get('MYSQLHOST',           'junction.proxy.rlwy.net'),
    'port':     int(os.environ.get('MYSQLPORT',       '16661')),
    'user':     os.environ.get('MYSQLUSER',            'root'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD',  'rOhOhfujlMBVGnrTtIYJQLAtxcMlsBOP'),
    'database': os.environ.get('MYSQLDATABASE',        'railway')
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

# ==================== FUNCIONES DE EMAIL (BREVO) ====================

def enviar_email_resend(destinatario: str, asunto: str, html: str):
    if not BREVO_API_KEY:
        raise Exception("BREVO_API_KEY no configurada en las variables de entorno de Railway")

    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": "Monte sin Piedad", "email": "hangelica957@gmail.com"},
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
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        <div style="background:linear-gradient(135deg,#A6032F,#800020);padding:40px;text-align:center;">
          <h1 style="color:white;margin:0;font-size:24px;font-weight:700;">🔐 RECUPERACIÓN DE CONTRASEÑA</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="color:#475569;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#475569;">Usa el siguiente código:</p>
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:30px;text-align:center;margin:30px 0;">
            <div style="font-size:40px;font-weight:900;color:#A6032F;letter-spacing:12px;font-family:'Courier New',monospace;">{codigo}</div>
          </div>
          <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:15px;border-radius:8px;">
            <p style="font-size:14px;color:#92400e;margin:0;">⏰ <strong>Expira en 15 minutos.</strong></p>
          </div>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte sin Piedad</p>
        </div>
      </div>
    </body></html>"""
    return enviar_email_resend(destinatario, f"🔐 Código de Recuperación: {codigo}", html)


def email_verificacion_cuenta(destinatario: str, codigo: str, nombre: str):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#10b981,#059669);padding:40px;text-align:center;">
          <h1 style="color:white;margin:0;">✅ VERIFICA TU EMAIL</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="color:#475569;">Hola <strong>{nombre}</strong>, verifica tu email:</p>
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:30px;text-align:center;margin:30px 0;">
            <div style="font-size:40px;font-weight:900;color:#10b981;letter-spacing:12px;font-family:'Courier New',monospace;">{codigo}</div>
          </div>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte sin Piedad</p>
        </div>
      </div>
    </body></html>"""
    return enviar_email_resend(destinatario, "✅ Verifica tu cuenta - Monte sin Piedad", html)


def email_bienvenida(destinatario: str, nombre: str):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:500px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#A6032F,#800020);padding:50px 30px;text-align:center;">
          <h1 style="color:white;margin:0;">¡Bienvenido a Monte sin Piedad! 🎉</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="font-size:18px;color:#1e293b;">Hola {nombre}, ¡Es un placer tenerte con nosotros!</p>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte sin Piedad</p>
        </div>
      </div>
    </body></html>"""
    return enviar_email_resend(destinatario, f"🎉 ¡Bienvenido a Monte sin Piedad, {nombre}!", html)


# ── Emails de notificaciones de préstamo ──────────────────────────────────────

def email_credito_aprobado(destinatario: str, nombre: str, folio: str,
                            monto: float, plazo: int, cuota: float):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:560px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,.1);">
        <div style="background:linear-gradient(135deg,#10b981,#059669);padding:40px;text-align:center;">
          <div style="font-size:60px;">✅</div>
          <h1 style="color:white;margin:8px 0 0;">¡CRÉDITO APROBADO!</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="color:#475569;font-size:16px;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#475569;">Tu solicitud de crédito ha sido aprobada. Aquí están los detalles:</p>
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:25px;margin:25px 0;">
            <table width="100%" style="border-collapse:collapse;">
              <tr>
                <td style="color:#64748b;font-size:14px;padding:10px 0;border-bottom:1px solid #e2e8f0;">Folio</td>
                <td style="color:#1e293b;font-weight:600;text-align:right;padding:10px 0;border-bottom:1px solid #e2e8f0;">{folio}</td>
              </tr>
              <tr>
                <td style="color:#64748b;font-size:14px;padding:10px 0;border-bottom:1px solid #e2e8f0;">Monto aprobado</td>
                <td style="color:#10b981;font-weight:700;font-size:18px;text-align:right;padding:10px 0;border-bottom:1px solid #e2e8f0;">${monto:,.2f}</td>
              </tr>
              <tr>
                <td style="color:#64748b;font-size:14px;padding:10px 0;border-bottom:1px solid #e2e8f0;">Plazo</td>
                <td style="color:#1e293b;font-weight:600;text-align:right;padding:10px 0;border-bottom:1px solid #e2e8f0;">{plazo} meses</td>
              </tr>
              <tr>
                <td style="color:#64748b;font-size:14px;padding:10px 0;">Cuota mensual</td>
                <td style="color:#A6032F;font-weight:700;font-size:18px;text-align:right;padding:10px 0;">${cuota:,.2f}</td>
              </tr>
            </table>
          </div>
          <div style="background:#ecfdf5;border-left:4px solid #10b981;padding:15px;border-radius:8px;">
            <p style="color:#065f46;margin:0;font-size:14px;">
              💡 Puedes ver tu calendario de pagos desde la aplicación.
            </p>
          </div>
        </div>
        <div style="text-align:center;padding:20px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte de Piedad — correo automático</p>
        </div>
      </div>
    </body></html>"""
    try:
        enviar_email_resend(destinatario, f"✅ Crédito Aprobado — {folio}", html)
    except Exception as e:
        print(f"⚠️ Email crédito aprobado no enviado: {e}")


def email_credito_rechazado(destinatario: str, nombre: str, folio: str, monto: float):
    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f1f5f9;margin:0;padding:20px;">
      <div style="max-width:560px;margin:auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,.1);">
        <div style="background:linear-gradient(135deg,#ef4444,#dc2626);padding:40px;text-align:center;">
          <div style="font-size:60px;">❌</div>
          <h1 style="color:white;margin:8px 0 0;">SOLICITUD NO APROBADA</h1>
        </div>
        <div style="padding:40px 30px;">
          <p style="color:#475569;font-size:16px;">Hola <strong>{nombre}</strong>,</p>
          <p style="color:#475569;">Lamentamos informarte que tu solicitud de crédito no pudo ser aprobada en esta ocasión.</p>
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:25px;margin:25px 0;text-align:center;">
            <div style="color:#64748b;font-size:14px;">Folio de solicitud</div>
            <div style="color:#1e293b;font-weight:700;font-size:20px;margin:8px 0;">{folio}</div>
            <div style="color:#64748b;font-size:14px;">Monto solicitado: <strong>${monto:,.2f}</strong></div>
          </div>
          <div style="background:#fef2f2;border-left:4px solid #ef4444;padding:15px;border-radius:8px;">
            <p style="color:#991b1b;margin:0;font-size:14px;">
              Puedes volver a solicitar un crédito en cualquier momento desde la aplicación.
            </p>
          </div>
        </div>
        <div style="text-align:center;padding:20px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte de Piedad — correo automático</p>
        </div>
      </div>
    </body></html>"""
    try:
        enviar_email_resend(destinatario, f"Resultado de tu solicitud — {folio}", html)
    except Exception as e:
        print(f"⚠️ Email crédito rechazado no enviado: {e}")


# ── Helpers de notificaciones ─────────────────────────────────────────────────

def _guardar_notificacion(cursor, id_usuario: int, tipo: str,
                           titulo: str, mensaje: str, datos_extra: dict = None):
    """Inserta una notificación en la tabla notificaciones."""
    extra_json = json.dumps(datos_extra or {}, ensure_ascii=False)
    cursor.execute("""
        INSERT INTO notificaciones
            (id_usuario, tipo, titulo, mensaje, leida, datos_extra)
        VALUES (%s, %s, %s, %s, 0, %s)
    """, (id_usuario, tipo, titulo, mensaje, extra_json))


# ── Funciones background ──────────────────────────────────────────────────────

def enviar_email_bienvenida_background(destinatario: str, nombre: str):
    try:
        email_bienvenida(destinatario, nombre)
    except Exception as e:
        print(f"⚠️ Email de bienvenida no enviado: {e}")


def enviar_email_verificacion_background(destinatario: str, codigo: str, nombre: str):
    try:
        email_verificacion_cuenta(destinatario, codigo, nombre)
    except Exception as e:
        print(f"⚠️ Email de verificación no enviado: {e}")


def enviar_email_codigo_recuperacion_background(destinatario: str, codigo: str, nombre: str):
    try:
        email_codigo_recuperacion(destinatario, codigo, nombre)
    except Exception as e:
        print(f"⚠️ Email de recuperación no enviado: {e}")


def _bg_email_aprobado(destinatario, nombre, folio, monto, plazo, cuota):
    try:
        email_credito_aprobado(destinatario, nombre, folio, monto, plazo, cuota)
    except Exception as e:
        print(f"⚠️ Email aprobado no enviado: {e}")


def _bg_email_rechazado(destinatario, nombre, folio, monto):
    try:
        email_credito_rechazado(destinatario, nombre, folio, monto)
    except Exception as e:
        print(f"⚠️ Email rechazado no enviado: {e}")


# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    return {"app": "Monte SIN Piedad API", "version": "2.0", "status": "✅ Operativo"}


@app.post("/login")
def login_unificado(request: LoginRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno,
                   email, rol, activo, email_verificado, curp, telefono
            FROM usuarios WHERE email = %s AND password = %s
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
                "id_usuario":       usuario['id_usuario'],
                "nombre":           usuario['nombre'],
                "apellido_paterno": usuario.get('apellido_paterno', ''),
                "apellido_materno": usuario.get('apellido_materno', ''),
                "email":            usuario['email'],
                "rol":              usuario['rol'],
                "curp":             usuario.get('curp'),
                "telefono":         usuario.get('telefono'),
                "email_verificado": bool(usuario.get('email_verificado', False))
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
        background_tasks.add_task(
            enviar_email_verificacion_background, request.email, codigo_verificacion, request.nombre
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
            UPDATE usuarios SET password = %s, codigo_recuperacion = NULL, fecha_codigo = NULL
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
                       email, rol, activo, email_verificado, fecha_registro,
                       curp, telefono, no_identificacion
                FROM usuarios WHERE rol = %s ORDER BY fecha_registro DESC
            """, (rol,))
        else:
            cursor.execute("""
                SELECT id_usuario, nombre, apellido_paterno, apellido_materno,
                       email, rol, activo, email_verificado, fecha_registro,
                       curp, telefono, no_identificacion
                FROM usuarios ORDER BY fecha_registro DESC
            """)
        usuarios = cursor.fetchall()
        for u in usuarios:
            u['activo']           = bool(u.get('activo', False))
            u['email_verificado'] = bool(u.get('email_verificado', False))
            if u.get('fecha_registro') and hasattr(u['fecha_registro'], 'isoformat'):
                u['fecha_registro'] = u['fecha_registro'].isoformat()
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
            FROM usuarios WHERE id_usuario = %s AND rol = 'Cliente'
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
        """, (request.nombre, request.apellido_paterno, request.apellido_materno,
              request.telefono, request.direccion, id_cliente))
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
    accion: str
    id_empleado: int

class CrearEmpleadoRequest(BaseModel):
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    email: str
    password: str
    telefono: Optional[str] = None
    rol: str = "Empleado"

class EditarUsuarioAdminRequest(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    curp: Optional[str] = None
    no_identificacion: Optional[str] = None

class RegistrarPagoRequest(BaseModel):
    id_pago:     int
    id_empleado: Optional[int] = None
    metodo_pago: Optional[str] = "EFECTIVO"

class RegistrarPagoClienteRequest(BaseModel):
    id_pago: int
    id_cliente: int
    metodo_pago: Optional[str] = "EFECTIVO"

class ConfiguracionRequest(BaseModel):
    tasa_interes: Optional[float] = None
    plazo_maximo: Optional[int] = None
    monto_minimo: Optional[float] = None
    monto_maximo: Optional[float] = None


# ==================== ENDPOINTS CLIENTE ====================

@app.post("/cliente/prestamo")
@app.post("/cliente/solicitar_credito")
def solicitar_prestamo(request: PrestamoRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT tasa_interes, plazo_maximo, monto_minimo, monto_maximo
            FROM configuracion_sistema ORDER BY id ASC LIMIT 1
        """)
        cfg = cursor.fetchone()
        if not cfg:
            raise HTTPException(status_code=500, detail="No hay configuración del sistema")

        tasa      = float(cfg['tasa_interes'])
        plazo_max = int(cfg['plazo_maximo'])
        monto_min = float(cfg['monto_minimo'])
        monto_max = float(cfg['monto_maximo'])

        if request.monto < monto_min or request.monto > monto_max:
            raise HTTPException(status_code=400,
                detail=f"Monto debe estar entre ${monto_min:,.0f} y ${monto_max:,.0f}")

        plazos_validos = [p for p in [6, 12, 24, 36, 48] if p <= plazo_max]
        if request.plazo_meses not in plazos_validos:
            raise HTTPException(status_code=400,
                detail=f"Plazo inválido. Opciones disponibles: {plazos_validos}")

        cursor.execute("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (request.id_cliente,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        cursor.execute(
            "SELECT id_prestamo FROM prestamos WHERE id_cliente = %s AND estado = 'PENDIENTE'",
            (request.id_cliente,)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya tienes una solicitud pendiente")

        cursor.execute("""
            SELECT COUNT(*) AS activos FROM prestamos
            WHERE id_cliente = %s AND estado IN ('ACTIVO', 'MOROSO', 'PENDIENTE')
        """, (request.id_cliente,))
        if int(cursor.fetchone().get('activos', 0) or 0) >= 4:
            raise HTTPException(status_code=403,
                detail="Tienes 4 créditos activos. Liquida alguno para solicitar uno nuevo.")

        cursor.execute("""
            SELECT p.plazo_meses, COUNT(g.id_pago) AS pagados
            FROM prestamos p
            LEFT JOIN pagos g ON g.id_prestamo = p.id_prestamo AND g.estado = 'pagado'
            WHERE p.id_cliente = %s AND p.estado IN ('ACTIVO', 'MOROSO')
            GROUP BY p.id_prestamo, p.plazo_meses
            ORDER BY p.fecha_aprobacion DESC LIMIT 1
        """, (request.id_cliente,))
        rec = cursor.fetchone()
        if rec:
            pagados = int(rec['pagados'] or 0)
            plazo   = int(rec['plazo_meses'] or 1)
            if pagados < plazo / 2:
                raise HTTPException(status_code=403,
                    detail=f"Debes pagar al menos el 50% de tu préstamo activo "
                           f"({pagados}/{plazo} pagos realizados) para solicitar uno nuevo.")

        capital = request.monto
        plazo   = request.plazo_meses
        cuota   = capital * (tasa * (1 + tasa)**plazo) / ((1 + tasa)**plazo - 1)
        cuota_redondeada = round(cuota, 2)
        saldo_total      = round(cuota * plazo, 2)

        cursor.execute("""
            INSERT INTO prestamos
                (id_cliente, monto_total, saldo_pendiente, tasa_interes, plazo_meses, estado, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, 'PENDIENTE', NOW())
        """, (request.id_cliente, capital, saldo_total, tasa, plazo))

        db.commit()
        return {
            "status":        "success",
            "message":       "Solicitud enviada. Un empleado la revisará pronto.",
            "cuota_mensual": cuota_redondeada,
            "total_a_pagar": saldo_total,
            "tasa_mensual":  tasa
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/cliente/mis_prestamos")
@app.get("/cliente/{id_cliente_path}/prestamos")
def obtener_mis_prestamos(id_cliente: Optional[int] = Query(None), id_cliente_path: Optional[int] = None):
    if id_cliente is None and id_cliente_path is not None:
        id_cliente = id_cliente_path
    if id_cliente is None:
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
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo)                         AS total_pagos
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
        cursor.execute("""
            SELECT g.fecha_vencimiento, g.monto, g.numero_pago,
                   CONCAT('MSP-', p.id_prestamo) AS folio
            FROM pagos g
            JOIN prestamos p ON g.id_prestamo = p.id_prestamo
            WHERE p.id_cliente = %s AND g.estado = 'pendiente' AND p.estado = 'ACTIVO'
            ORDER BY g.fecha_vencimiento ASC LIMIT 1
        """, (id_cliente,))
        proximo = cursor.fetchone()
        if proximo and proximo.get('fecha_vencimiento') and hasattr(proximo['fecha_vencimiento'], 'isoformat'):
            proximo['fecha_vencimiento'] = proximo['fecha_vencimiento'].isoformat()
            proximo['monto'] = float(proximo['monto'] or 0)
        return {
            "status":           "success",
            "capital_otorgado": float(row['capital_otorgado'] or 0),
            "saldo_pendiente":  float(row['saldo_pendiente'] or 0),
            "total_pagado":     float(pagos['total_pagado'] or 0),
            "total_prestamos":  row['total_prestamos'],
            "activos":          row['activos'],
            "morosos":          row['morosos'],
            "liquidados":       row['liquidados'],
            "pendientes":       row['pendientes'],
            "proximo_pago":     proximo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


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


@app.post("/cliente/registrar_pago")
def registrar_pago_cliente(request: RegistrarPagoClienteRequest):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pagos WHERE id_pago = %s", (request.id_pago,))
        pago = cursor.fetchone()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        id_prestamo = pago['id_prestamo']
        cursor.execute("SELECT id_cliente FROM prestamos WHERE id_prestamo = %s", (id_prestamo,))
        prestamo = cursor.fetchone()
        if not prestamo or prestamo['id_cliente'] != request.id_cliente:
            raise HTTPException(status_code=403, detail="No tienes permiso para pagar este préstamo")

        if pago['estado'] == 'pagado':
            raise HTTPException(status_code=400, detail="Este pago ya fue registrado")

        cursor.execute("""
            SELECT COUNT(*) AS bloqueantes FROM pagos
            WHERE id_prestamo = %s AND numero_pago < %s AND estado != 'pagado'
        """, (id_prestamo, pago['numero_pago']))
        if int(cursor.fetchone().get('bloqueantes', 0) or 0) > 0:
            raise HTTPException(status_code=403,
                detail="Debes pagar las mensualidades anteriores primero.")

        monto = float(pago['monto'])
        cursor.execute(
            "UPDATE pagos SET estado='pagado', fecha_pago=NOW() WHERE id_pago = %s",
            (request.id_pago,)
        )
        cursor.execute(
            "UPDATE prestamos SET saldo_pendiente = GREATEST(0, saldo_pendiente - %s) WHERE id_prestamo = %s",
            (monto, id_prestamo)
        )
        cursor.execute(
            "SELECT COUNT(*) AS pendientes FROM pagos WHERE id_prestamo = %s AND estado = 'pendiente'",
            (id_prestamo,)
        )
        liquidado = int(cursor.fetchone().get('pendientes', 0) or 0) == 0
        if liquidado:
            cursor.execute(
                "UPDATE prestamos SET estado='LIQUIDADO', saldo_pendiente=0 WHERE id_prestamo = %s",
                (id_prestamo,)
            )

        import hashlib, time
        folio = f"TC-{request.id_pago}-{int(time.time())}"
        firma = hashlib.sha256(f"{request.id_pago}{monto}{time.time()}".encode()).hexdigest()[:64]
        metodo = (request.metodo_pago or "EFECTIVO").upper()
        cursor.execute("""
            INSERT INTO tickets_pagos
                (folio, id_pago, metodo_pago, monto_pagado,
                 fecha_generacion, firma_digital, estado, tipo)
            VALUES (%s, %s, %s, %s, NOW(), %s, 'ACTIVO', %s)
        """, (folio, request.id_pago, metodo, monto, firma,
              'LIQUIDACION' if liquidado else 'PAGO'))

        # ── Notificación en BD ────────────────────────────────────────────────
        folio_prestamo = f"MSP-{id_prestamo}"
        if liquidado:
            _guardar_notificacion(
                cursor, request.id_cliente,
                "CREDITO_LIQUIDADO",
                "¡Crédito liquidado! 🎉",
                f"Has liquidado tu crédito {folio_prestamo}. ¡Felicidades!",
                {"folio": folio_prestamo, "monto": monto}
            )
        else:
            _guardar_notificacion(
                cursor, request.id_cliente,
                "PAGO_REGISTRADO",
                "Pago registrado ✅",
                f"Tu pago #{pago['numero_pago']} del crédito {folio_prestamo} "
                f"por ${monto:,.2f} fue registrado correctamente.",
                {"folio": folio_prestamo, "numero_pago": pago['numero_pago'], "monto": monto}
            )

        db.commit()
        return {
            "status":      "success",
            "message":     f"Pago #{pago['numero_pago']} registrado exitosamente",
            "monto":       monto,
            "id_prestamo": id_prestamo,
            "liquidado":   liquidado
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== CONFIGURACIÓN ====================

@app.get("/configuracion_sistema")
def obtener_configuracion():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM configuracion_sistema ORDER BY id ASC")
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


@app.put("/configuracion_sistema/{id_config}")
def actualizar_configuracion(id_config: int, request: ConfiguracionRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        campos  = []
        valores = []
        if request.tasa_interes is not None:
            campos.append("tasa_interes = %s"); valores.append(float(request.tasa_interes))
        if request.plazo_maximo is not None:
            campos.append("plazo_maximo = %s"); valores.append(int(request.plazo_maximo))
        if request.monto_minimo is not None:
            campos.append("monto_minimo = %s"); valores.append(float(request.monto_minimo))
        if request.monto_maximo is not None:
            campos.append("monto_maximo = %s"); valores.append(float(request.monto_maximo))
        if not campos:
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
        campos.append("fecha_actualizacion = NOW()")
        query = f"UPDATE configuracion_sistema SET {', '.join(campos)} WHERE id = %s"
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


@app.post("/admin/aprobar_prestamo")
def procesar_prestamo(request: AprobarPrestamoRequest, background_tasks: BackgroundTasks):
    from datetime import date
    if request.accion not in ["aprobar", "rechazar"]:
        raise HTTPException(status_code=400, detail="Acción inválida. Usa 'aprobar' o 'rechazar'")
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # ── Obtener préstamo + datos del cliente ──────────────────────────────
        cursor.execute("""
            SELECT p.*,
                   u.nombre, u.apellido_paterno, u.email AS email_cliente,
                   u.id_usuario AS id_cliente
            FROM prestamos p
            JOIN usuarios u ON p.id_cliente = u.id_usuario
            WHERE p.id_prestamo = %s
        """, (request.id_prestamo,))
        prestamo = cursor.fetchone()
        if not prestamo:
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")
        if prestamo['estado'] != 'PENDIENTE':
            raise HTTPException(status_code=400, detail="El préstamo no está en estado PENDIENTE")

        id_cliente     = prestamo['id_cliente']
        email_cliente  = prestamo['email_cliente']
        nombre_cliente = f"{prestamo['nombre']} {prestamo.get('apellido_paterno', '')}".strip()
        folio          = f"MSP-{request.id_prestamo}"

        if request.accion == "aprobar":
            capital = float(prestamo['monto_total'])
            plazo   = int(prestamo['plazo_meses'])
            tasa    = float(prestamo['tasa_interes'])

            cuota        = capital * (tasa * (1 + tasa)**plazo) / ((1 + tasa)**plazo - 1)
            cuota_normal = round(cuota, 2)
            saldo_total  = round(cuota * plazo, 2)
            ultimo_pago  = round(saldo_total - cuota_normal * (plazo - 1), 2)
            hoy          = date.today()

            cursor.execute("""
                UPDATE prestamos
                SET estado='ACTIVO', monto_total=%s, saldo_pendiente=%s,
                    fecha_aprobacion=NOW(), id_aprobador=%s
                WHERE id_prestamo=%s
            """, (saldo_total, saldo_total, request.id_empleado, request.id_prestamo))

            for i in range(1, plazo + 1):
                fecha_venc = hoy + timedelta(days=30 * i)
                monto_pago = ultimo_pago if i == plazo else cuota_normal
                cursor.execute("""
                    INSERT INTO pagos (id_prestamo, numero_pago, fecha_vencimiento, monto, estado)
                    VALUES (%s, %s, %s, %s, 'pendiente')
                """, (request.id_prestamo, i, fecha_venc, monto_pago))

            # ── Notificación en tabla ─────────────────────────────────────────
            _guardar_notificacion(
                cursor, id_cliente,
                "CREDITO_APROBADO",
                "¡Crédito aprobado! ✅",
                f"Tu crédito {folio} por ${capital:,.2f} fue aprobado. "
                f"Cuota mensual: ${cuota_normal:,.2f} por {plazo} meses.",
                {"folio": folio, "monto": capital,
                 "plazo": plazo, "cuota": cuota_normal,
                 "id_prestamo": request.id_prestamo}
            )

            db.commit()

            # ── Email en background (no bloquea la respuesta) ─────────────────
            background_tasks.add_task(
                _bg_email_aprobado,
                email_cliente, nombre_cliente, folio,
                capital, plazo, cuota_normal
            )

            return {
                "status":        "success",
                "message":       f"Préstamo aprobado. Se generaron {plazo} pagos.",
                "cuota_mensual": cuota_normal,
                "ultimo_pago":   ultimo_pago,
                "total_a_pagar": saldo_total
            }

        else:  # rechazar
            cursor.execute(
                "UPDATE prestamos SET estado='RECHAZADO', id_aprobador=%s WHERE id_prestamo=%s",
                (request.id_empleado, request.id_prestamo)
            )

            # ── Notificación en tabla ─────────────────────────────────────────
            _guardar_notificacion(
                cursor, id_cliente,
                "CREDITO_RECHAZADO",
                "Solicitud rechazada ❌",
                f"Tu solicitud {folio} por ${float(prestamo['monto_total']):,.2f} "
                f"no pudo ser aprobada. Puedes intentarlo nuevamente.",
                {"folio": folio, "monto": float(prestamo['monto_total'])}
            )

            db.commit()

            # ── Email en background ───────────────────────────────────────────
            background_tasks.add_task(
                _bg_email_rechazado,
                email_cliente, nombre_cliente, folio,
                float(prestamo['monto_total'])
            )

            return {"status": "success", "message": "Préstamo rechazado."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/admin/folios")
def obtener_folios_admin(fecha: Optional[str] = Query(None)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        fecha_filtro = fecha if fecha else datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT t.id_ticket, t.folio, t.monto_pagado, t.fecha_generacion,
                   t.metodo_pago, t.tipo,
                   CONCAT('MSP-', p.id_prestamo) AS folio_prestamo,
                   u.nombre, u.apellido_paterno
            FROM tickets_pagos t
            JOIN pagos g         ON t.id_pago       = g.id_pago
            JOIN prestamos p     ON g.id_prestamo   = p.id_prestamo
            JOIN usuarios u      ON p.id_cliente    = u.id_usuario
            WHERE DATE(t.fecha_generacion) = %s AND LOWER(t.estado) = 'activo'
            ORDER BY t.fecha_generacion DESC
        """, (fecha_filtro,))
        movimientos = cursor.fetchall()
        for m in movimientos:
            if m.get("fecha_generacion") and hasattr(m["fecha_generacion"], "isoformat"):
                m["fecha_generacion"] = m["fecha_generacion"].isoformat()
            m["monto_pagado"] = float(m.get("monto_pagado") or 0)
            m["metodo_pago"]  = (m.get("metodo_pago") or "").upper()
            m["tipo"]         = (m.get("tipo") or "pago").upper()
        total = float(sum(m["monto_pagado"] for m in movimientos))
        return {
            "status":        "success",
            "fecha":         fecha_filtro,
            "total_pagos":   len(movimientos),
            "total_cobrado": total,
            "movimientos":   movimientos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/admin/estadisticas")
def obtener_estadisticas():
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM vista_dashboard LIMIT 1")
        row = cursor.fetchone() or {}
        return {
            "total_clientes":    int(row.get('total_clientes', 0) or 0),
            "prestamos_activos": int(row.get('prestamos_activos', 0) or 0),
            "capital_otorgado":  float(row.get('capital_colocado', 0) or 0),
            "saldo_pendiente":   float(row.get('saldo_pendiente_total', 0) or 0),
            "monto_recuperado":  float(row.get('recaudacion_total', 0) or 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


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
        return {"status": "success", "message": f"{rol} creado exitosamente", "id_empleado": cursor.lastrowid}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.put("/admin/usuario/{id_usuario}")
def editar_usuario_admin(id_usuario: int, request: EditarUsuarioAdminRequest):
    db = conectar()
    cursor = db.cursor()
    try:
        campos  = []
        valores = []
        if request.nombre            is not None: campos.append("nombre=%s");             valores.append(request.nombre)
        if request.apellido_paterno  is not None: campos.append("apellido_paterno=%s");   valores.append(request.apellido_paterno)
        if request.apellido_materno  is not None: campos.append("apellido_materno=%s");   valores.append(request.apellido_materno)
        if request.telefono          is not None: campos.append("telefono=%s");           valores.append(request.telefono)
        if request.direccion         is not None: campos.append("direccion=%s");          valores.append(request.direccion)
        if request.curp              is not None: campos.append("curp=%s");               valores.append(request.curp)
        if request.no_identificacion is not None: campos.append("no_identificacion=%s");  valores.append(request.no_identificacion)
        if not campos:
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id_usuario = %s"
        valores.append(id_usuario)
        cursor.execute(query, tuple(valores))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"status": "success", "message": "Usuario actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.put("/admin/usuario/{id_usuario}/estado")
def cambiar_estado_usuario(id_usuario: int, activo: bool = Query(...)):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE usuarios SET activo=%s WHERE id_usuario=%s", (activo, id_usuario))
        db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"status": "success", "message": "Estado actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== ENDPOINTS EMPLEADO ====================

@app.post("/empleado/registrar_pago")
def registrar_pago(request: RegistrarPagoRequest):
    print(f"REGISTRAR PAGO → id_pago={request.id_pago} id_empleado={request.id_empleado} metodo={request.metodo_pago}")
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

        # Obtener id_cliente para la notificación
        cursor.execute("SELECT id_cliente FROM prestamos WHERE id_prestamo = %s", (id_prestamo,))
        p_row      = cursor.fetchone()
        id_cliente = p_row['id_cliente'] if p_row else None

        cursor.execute("UPDATE pagos SET estado='pagado', fecha_pago=NOW() WHERE id_pago=%s", (request.id_pago,))
        cursor.execute("""
            UPDATE prestamos SET saldo_pendiente = GREATEST(0, saldo_pendiente - %s)
            WHERE id_prestamo = %s
        """, (monto, id_prestamo))

        cursor.execute(
            "SELECT COUNT(*) AS pendientes FROM pagos WHERE id_prestamo = %s AND estado = 'pendiente'",
            (id_prestamo,)
        )
        liquidado = int(cursor.fetchone().get('pendientes', 0) or 0) == 0
        if liquidado:
            cursor.execute(
                "UPDATE prestamos SET estado='LIQUIDADO', saldo_pendiente=0 WHERE id_prestamo=%s",
                (id_prestamo,)
            )

        import hashlib, time
        folio = f"T-{request.id_pago}-{int(time.time())}"
        firma = hashlib.sha256(f"{request.id_pago}{monto}{time.time()}".encode()).hexdigest()[:64]
        # DESPUÉS:
        metodo     = (request.metodo_pago or "EFECTIVO").upper()
        id_empleado = request.id_empleado  # puede ser None, la BD lo acepta nullable
        cursor.execute("""
            INSERT INTO tickets_pagos
                (folio, id_pago, id_empleado, metodo_pago, monto_pagado,
                 fecha_generacion, firma_digital, estado, tipo)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s, 'ACTIVO', %s)
        """, (folio, request.id_pago, id_empleado, metodo, monto, firma,
              'LIQUIDACION' if liquidado else 'PAGO'))

        # ── Notificación en BD ────────────────────────────────────────────────
        if id_cliente:
            folio_prestamo = f"MSP-{id_prestamo}"
            if liquidado:
                _guardar_notificacion(
                    cursor, id_cliente,
                    "CREDITO_LIQUIDADO",
                    "¡Crédito liquidado! 🎉",
                    f"Has liquidado tu crédito {folio_prestamo}. ¡Felicidades!",
                    {"folio": folio_prestamo, "monto": monto}
                )
            else:
                _guardar_notificacion(
                    cursor, id_cliente,
                    "PAGO_REGISTRADO",
                    "Pago registrado ✅",
                    f"Tu pago #{pago['numero_pago']} del crédito {folio_prestamo} "
                    f"por ${monto:,.2f} fue registrado.",
                    {"folio": folio_prestamo,
                     "numero_pago": pago['numero_pago'], "monto": monto}
                )

        db.commit()
        return {
            "status":      "success",
            "message":     f"Pago #{pago['numero_pago']} registrado exitosamente",
            "monto":       monto,
            "id_prestamo": id_prestamo,
            "liquidado":   liquidado
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/empleado/pagos_pendientes")
def obtener_pagos_pendientes():
    db     = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT g.id_pago, g.id_prestamo, g.numero_pago,
                   g.fecha_vencimiento, g.monto, g.estado,
                   p.monto_total, p.estado AS estado_prestamo,
                   CONCAT('MSP-', p.id_prestamo) AS folio,
                   CONCAT(u.nombre, ' ', u.apellido_paterno, ' ',
                          COALESCE(u.apellido_materno, '')) AS nombre_cliente,
                   u.nombre, u.apellido_paterno, u.telefono, u.curp
            FROM pagos g
            JOIN prestamos p ON g.id_prestamo = p.id_prestamo
            JOIN usuarios u  ON p.id_cliente  = u.id_usuario
            WHERE g.estado = 'pendiente' AND p.estado IN ('ACTIVO', 'MOROSO')
            ORDER BY g.fecha_vencimiento ASC
        """)
        pagos = cursor.fetchall()
        for p in pagos:
            if p.get('fecha_vencimiento') and hasattr(p['fecha_vencimiento'], 'isoformat'):
                p['fecha_vencimiento'] = p['fecha_vencimiento'].isoformat()
            p['monto']       = float(p['monto'] or 0)
            p['monto_total'] = float(p['monto_total'] or 0)
            p['nombre_cliente'] = (p.get('nombre_cliente') or '').strip() or None
        return pagos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


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
            JOIN pagos g     ON t.id_pago       = g.id_pago
            JOIN prestamos p ON g.id_prestamo   = p.id_prestamo
            JOIN usuarios u  ON p.id_cliente    = u.id_usuario
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


@app.get("/tickets/{folio}")
def buscar_ticket(folio: str):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        id_prestamo = int(folio.replace("MSP-", "").strip())
        cursor.execute("""
            SELECT p.id_prestamo, CONCAT('MSP-', p.id_prestamo) AS folio,
                   p.monto_total, p.saldo_pendiente, p.tasa_interes,
                   p.plazo_meses, p.estado, p.fecha_creacion, p.fecha_aprobacion,
                   u.nombre, u.apellido_paterno, u.apellido_materno,
                   u.curp, u.telefono, u.email,
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo AND g.estado = 'pagado') AS pagos_realizados,
                   (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo)                         AS total_pagos
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


@app.get("/cliente/{id_cliente}/elegibilidad")
def verificar_elegibilidad(id_cliente: int):
    db     = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT COUNT(*) AS activos FROM prestamos
            WHERE id_cliente = %s AND estado IN ('ACTIVO', 'MOROSO', 'PENDIENTE')
        """, (id_cliente,))
        activos = int(cursor.fetchone().get('activos', 0) or 0)

        if activos >= 4:
            return {
                "puede_solicitar": False,
                "motivo": "Tienes 4 créditos activos. Liquida alguno para solicitar uno nuevo.",
                "pagos_realizados": None,
                "plazo_meses": None
            }

        cursor.execute("""
            SELECT p.plazo_meses, COUNT(g.id_pago) AS pagados
            FROM prestamos p
            LEFT JOIN pagos g ON g.id_prestamo = p.id_prestamo AND g.estado = 'pagado'
            WHERE p.id_cliente = %s AND p.estado IN ('ACTIVO', 'MOROSO')
            GROUP BY p.id_prestamo, p.plazo_meses
            ORDER BY p.fecha_aprobacion DESC LIMIT 1
        """, (id_cliente,))
        rec = cursor.fetchone()

        if rec:
            pagados = int(rec['pagados'] or 0)
            plazo   = int(rec['plazo_meses'] or 1)
            if pagados < plazo / 2:
                return {
                    "puede_solicitar": False,
                    "motivo": f"Debes pagar al menos el 50% de tu préstamo activo "
                              f"({pagados} de {plazo} pagos realizados).",
                    "pagos_realizados": pagados,
                    "plazo_meses": plazo
                }

        return {"puede_solicitar": True, "motivo": None,
                "pagos_realizados": None, "plazo_meses": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== ENDPOINTS NOTIFICACIONES ====================

@app.get("/notificaciones/{id_usuario}")
def obtener_notificaciones(id_usuario: int, solo_no_leidas: bool = Query(False), limite: int = Query(50)):
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        where = "WHERE id_usuario = %s"
        params = [id_usuario]
        if solo_no_leidas:
            where += " AND leida = 0"
        cursor.execute(
            f"SELECT * FROM notificaciones {where} ORDER BY fecha_creacion DESC LIMIT %s",
            (*params, limite)
        )
        notifs = cursor.fetchall()
        for n in notifs:
            if n.get('fecha_creacion') and hasattr(n['fecha_creacion'], 'isoformat'):
                n['fecha_creacion'] = n['fecha_creacion'].isoformat()
            n['leida'] = bool(n.get('leida', False))
        return {"status": "success", "total": len(notifs), "notificaciones": notifs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/notificaciones/{id_usuario}/no_leidas")
def contar_no_leidas(id_usuario: int):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM notificaciones WHERE id_usuario = %s AND leida = 0",
            (id_usuario,)
        )
        count = cursor.fetchone()[0]
        return {"status": "success", "no_leidas": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.put("/notificaciones/{id_notificacion}/leida")
def marcar_leida(id_notificacion: int):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE notificaciones SET leida = 1 WHERE id_notificacion = %s",
            (id_notificacion,)
        )
        db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.put("/notificaciones/{id_usuario}/todas_leidas")
def marcar_todas_leidas(id_usuario: int):
    db = conectar()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE notificaciones SET leida = 1 WHERE id_usuario = %s AND leida = 0",
            (id_usuario,)
        )
        db.commit()
        return {"status": "success", "actualizadas": cursor.rowcount}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


# ==================== PAYPAL ====================

import time
import requests as http_requests

PAYPAL_CLIENT_ID  = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET     = os.environ.get("PAYPAL_SECRET", "")
PAYPAL_MODE       = os.environ.get("PAYPAL_MODE", "sandbox")

PAYPAL_BASE = (
    "https://api-m.sandbox.paypal.com"
    if PAYPAL_MODE == "sandbox"
    else "https://api-m.paypal.com"
)

RAILWAY_DOMAIN    = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
PAYPAL_RETURN_URL = f"https://{RAILWAY_DOMAIN}/pagos/paypal/retorno"
PAYPAL_CANCEL_URL = f"https://{RAILWAY_DOMAIN}/pagos/paypal/cancelar"

_paypal_token_cache = {"access_token": None, "expires_at": 0}

def _paypal_access_token() -> str:
    ahora  = time.time()
    margen = 300
    if (
        _paypal_token_cache["access_token"] and
        ahora < _paypal_token_cache["expires_at"] - margen
    ):
        print(f"PAYPAL TOKEN → usando cacheado, expira en {int(_paypal_token_cache['expires_at'] - ahora)}s")
        return _paypal_token_cache["access_token"]

    response = http_requests.post(
        f"{PAYPAL_BASE}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=10
    )
    print(f"PAYPAL AUTH → status={response.status_code}")
    if response.status_code != 200:
        raise HTTPException(status_code=502,
            detail=f"PayPal auth error {response.status_code}: {response.text}")

    data = response.json()
    _paypal_token_cache["access_token"] = data["access_token"]
    _paypal_token_cache["expires_at"]   = ahora + data.get("expires_in", 32400)
    print(f"PAYPAL AUTH → token nuevo generado, válido por {data.get('expires_in', 32400)}s")
    return _paypal_token_cache["access_token"]


from fastapi.responses import RedirectResponse

@app.get("/pagos/paypal/retorno")
def paypal_retorno(token: str = "", PayerID: str = ""):
    deep_link = f"com.moon.casaprestamo://paypalpay?token={token}&PayerID={PayerID}"
    return RedirectResponse(url=deep_link)

@app.get("/pagos/paypal/cancelar")
def paypal_cancelar():
    return RedirectResponse(url="com.moon.casaprestamo://paypalpay/cancel")


class PaypalOrdenRequest(BaseModel):
    id_pago:    int
    id_cliente: int

class PaypalCapturarRequest(BaseModel):
    token:      str
    id_pago:    int
    id_cliente: int


@app.post("/pagos/paypal/crear-orden")
def crear_orden_paypal(request: PaypalOrdenRequest):
    db     = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pagos WHERE id_pago = %s", (request.id_pago,))
        pago = cursor.fetchone()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        cursor.execute(
            "SELECT id_cliente FROM prestamos WHERE id_prestamo = %s",
            (pago["id_prestamo"],)
        )
        prestamo = cursor.fetchone()
        if not prestamo or prestamo["id_cliente"] != request.id_cliente:
            raise HTTPException(status_code=403, detail="No tienes permiso para pagar este préstamo")

        if pago["estado"] == "pagado":
            raise HTTPException(status_code=400, detail="Este pago ya fue registrado")

        cursor.execute("""
            SELECT COUNT(*) AS bloqueantes FROM pagos
            WHERE id_prestamo = %s AND numero_pago < %s AND estado != 'pagado'
        """, (pago["id_prestamo"], pago["numero_pago"]))
        if int(cursor.fetchone().get("bloqueantes", 0) or 0) > 0:
            raise HTTPException(status_code=403,
                detail="Debes pagar las mensualidades anteriores primero.")

        monto        = float(pago["monto"])
        token_acceso = _paypal_access_token()

        orden_response = http_requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": str(request.id_pago),
                    "description":  f"Mensualidad #{pago['numero_pago']} - Monte sin Piedad",
                    "amount": {"currency_code": "MXN", "value": f"{monto:.2f}"}
                }],
                "application_context": {
                    "brand_name":          "Monte sin Piedad",
                    "landing_page":        "BILLING",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action":         "PAY_NOW",
                    "return_url":          PAYPAL_RETURN_URL,
                    "cancel_url":          PAYPAL_CANCEL_URL
                }
            },
            headers={
                "Authorization": f"Bearer {token_acceso}",
                "Content-Type":  "application/json"
            },
            timeout=15
        )
        print(f"PAYPAL ORDEN → status={orden_response.status_code}")
        if orden_response.status_code not in (200, 201):
            raise HTTPException(status_code=502,
                detail=f"PayPal error al crear orden: {orden_response.text}")

        orden        = orden_response.json()
        orden_id     = orden["id"]
        approval_url = next(
            (link["href"] for link in orden.get("links", []) if link["rel"] == "approve"),
            None
        )
        if not approval_url:
            raise HTTPException(status_code=502, detail="PayPal no devolvió approval_url")

        return {
            "status":       "success",
            "orden_id":     orden_id,
            "approval_url": approval_url,
            "monto":        monto,
            "numero_pago":  pago["numero_pago"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.post("/pagos/paypal/capturar")
def capturar_pago_paypal(request: PaypalCapturarRequest):
    db     = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM pagos WHERE id_pago = %s", (request.id_pago,))
        pago = cursor.fetchone()
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")

        cursor.execute(
            "SELECT id_cliente FROM prestamos WHERE id_prestamo = %s",
            (pago["id_prestamo"],)
        )
        prestamo = cursor.fetchone()
        if not prestamo or prestamo["id_cliente"] != request.id_cliente:
            raise HTTPException(status_code=403, detail="No tienes permiso")

        if pago["estado"] == "pagado":
            return {
                "status":      "success",
                "message":     f"Pago #{pago['numero_pago']} ya fue registrado anteriormente",
                "monto":       float(pago["monto"]),
                "id_prestamo": pago["id_prestamo"],
                "liquidado":   False,
                "folio":       "DUPLICADO"
            }

        monto        = float(pago["monto"])
        id_prestamo  = pago["id_prestamo"]
        token_acceso = _paypal_access_token()

        print(f"PAYPAL CAPTURA → intentando capturar orden {request.token}")
        captura_response = http_requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{request.token}/capture",
            headers={
                "Authorization": f"Bearer {token_acceso}",
                "Content-Type":  "application/json"
            },
            json={},
            timeout=15
        )
        print(f"PAYPAL CAPTURA → status={captura_response.status_code}")

        if captura_response.status_code == 422:
            raise HTTPException(status_code=400,
                detail="Este pago ya fue procesado en PayPal. Recarga tu cartera.")
        if captura_response.status_code not in (200, 201):
            raise HTTPException(status_code=502,
                detail=f"PayPal error al capturar: {captura_response.text}")

        estado_final = captura_response.json().get("status", "")
        if estado_final != "COMPLETED":
            raise HTTPException(status_code=400,
                detail=f"El pago no fue completado. Estado PayPal: {estado_final}")

        cursor.execute(
            "UPDATE pagos SET estado='pagado', fecha_pago=NOW() WHERE id_pago = %s",
            (request.id_pago,)
        )
        cursor.execute(
            "UPDATE prestamos SET saldo_pendiente = GREATEST(0, saldo_pendiente - %s) WHERE id_prestamo = %s",
            (monto, id_prestamo)
        )
        cursor.execute(
            "SELECT COUNT(*) AS pendientes FROM pagos WHERE id_prestamo = %s AND estado = 'pendiente'",
            (id_prestamo,)
        )
        liquidado = int(cursor.fetchone().get("pendientes", 0) or 0) == 0
        if liquidado:
            cursor.execute(
                "UPDATE prestamos SET estado='LIQUIDADO', saldo_pendiente=0 WHERE id_prestamo = %s",
                (id_prestamo,)
            )

        import hashlib
        folio = f"TC-{request.id_pago}-{int(time.time())}"
        firma = hashlib.sha256(
            f"{request.id_pago}{monto}{time.time()}".encode()
        ).hexdigest()[:64]
        cursor.execute("""
            INSERT INTO tickets_pagos
                (folio, id_pago, metodo_pago, monto_pagado,
                 fecha_generacion, firma_digital, estado, tipo)
            VALUES (%s, %s, 'PAYPAL', %s, NOW(), %s, 'ACTIVO', %s)
        """, (folio, request.id_pago, monto, firma,
              "LIQUIDACION" if liquidado else "PAGO"))

        # ── Notificación en BD ────────────────────────────────────────────────
        folio_prestamo = f"MSP-{id_prestamo}"
        if liquidado:
            _guardar_notificacion(
                cursor, request.id_cliente,
                "CREDITO_LIQUIDADO",
                "¡Crédito liquidado! 🎉",
                f"Has liquidado tu crédito {folio_prestamo} vía PayPal. ¡Felicidades!",
                {"folio": folio_prestamo, "monto": monto}
            )
        else:
            _guardar_notificacion(
                cursor, request.id_cliente,
                "PAGO_REGISTRADO",
                "Pago registrado ✅",
                f"Tu pago #{pago['numero_pago']} del crédito {folio_prestamo} "
                f"por ${monto:,.2f} fue registrado vía PayPal.",
                {"folio": folio_prestamo,
                 "numero_pago": pago['numero_pago'], "monto": monto}
            )

        db.commit()
        return {
            "status":      "success",
            "message":     f"Pago #{pago['numero_pago']} registrado exitosamente vía PayPal",
            "monto":       monto,
            "id_prestamo": id_prestamo,
            "liquidado":   liquidado,
            "folio":       folio
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
