"""
═══════════════════════════════════════════════════════════════════════════════
API FINAL - MONTE SIN PIEDAD
Con Resend, tabla unificada, y variables de entorno para Railway
═══════════════════════════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from datetime import datetime, timedelta
import random
import os

# ==================== RESEND (reemplaza smtplib) ====================
import resend

# Configurar API key de Resend desde variable de entorno
resend.api_key = os.environ.get("RESEND_API_KEY", "")

# ==================== CONFIGURACIÓN BD (VARIABLES DE ENTORNO) ====================
DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', 'junction.proxy.rlwy.net'),
    'port': int(os.environ.get('MYSQLPORT', '16661')),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD', 'rOhOhfujlMBVGnrTtIYJQLAtxcMlsBOP'),
    'database': os.environ.get('MYSQLDATABASE', 'railway')
}

# ==================== FASTAPI APP ====================
app = FastAPI()

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

class VerificarEmailRequest(BaseModel):
    email: str
    codigo: str

class RecuperacionRequest(BaseModel):
    email: str
    codigo: str
    nueva_password: str

# ==================== FUNCIONES DE EMAIL (RESEND) ====================

def enviar_email_resend(destinatario: str, asunto: str, html: str):
    try:
        resend.Emails.send({
            "from": "Monte de Piedad <onboarding@resend.dev>",
            "to": [destinatario],
            "subject": asunto,
            "html": html
        })
        print(f"✅ Email enviado a {destinatario}")
        return True
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
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
def registrar_cliente(request: RegistroClienteRequest):
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
             curp, telefono, direccion, no_identificacion, activo, 
             email_verificado, codigo_verificacion, fecha_codigo_verificacion)
            VALUES (%s, %s, %s, %s, %s, 'Cliente', %s, %s, %s, %s, TRUE, FALSE, %s, NOW())
        """, (
            request.nombre, request.apellido_paterno, request.apellido_materno,
            request.email, request.password, request.curp, request.telefono,
            request.direccion, request.no_identificacion, codigo_verificacion
        ))

        db.commit()
        id_cliente = cursor.lastrowid

        try:
            email_verificacion_cuenta(request.email, codigo_verificacion, request.nombre)
        except Exception as e:
            cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_cliente,))
            db.commit()
            raise HTTPException(status_code=500, detail=f"No se pudo enviar email de verificación: {str(e)}")

        return {
            "status": "success",
            "message": "Registro exitoso. Revisa tu email para verificar tu cuenta.",
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
def solicitar_codigo_recuperacion(email: str = Query(...)):
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

        try:
            email_codigo_recuperacion(email, codigo, usuario['nombre'])
        except Exception as mail_error:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Código generado pero no se pudo enviar el correo: {str(mail_error)}")

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

# ==================== ENDPOINTS CLIENTE (APP ANDROID) ====================

class SolicitudCreditoRequest(BaseModel):
    id_cliente: int
    monto: float
    plazo_meses: int

class ActualizarPerfilRequest(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

@app.get("/cliente/{id_cliente}/prestamos")
def obtener_prestamos_cliente(id_cliente: int):
    """Devuelve todos los préstamos del cliente con su estado."""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                p.id_prestamo,
                CONCAT('MSP-', p.id_prestamo) AS folio,
                p.monto_total,
                p.saldo_pendiente,
                p.tasa_interes,
                p.plazo_meses,
                p.estado,
                p.fecha_creacion,
                p.fecha_aprobacion,
                (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo AND g.estado = 'pagado') AS pagos_realizados,
                (SELECT COUNT(*) FROM pagos g WHERE g.id_prestamo = p.id_prestamo) AS total_pagos
            FROM prestamos p
            WHERE p.id_cliente = %s
            ORDER BY p.fecha_creacion DESC
        """, (id_cliente,))

        prestamos = cursor.fetchall()

        # Serializar fechas
        for p in prestamos:
            for campo in ['fecha_creacion', 'fecha_aprobacion']:
                if p.get(campo) and hasattr(p[campo], 'isoformat'):
                    p[campo] = p[campo].isoformat()
            p['monto_total']      = float(p['monto_total'] or 0)
            p['saldo_pendiente']  = float(p['saldo_pendiente'] or 0)
            p['tasa_interes']     = float(p['tasa_interes'] or 0)

        return {
            "status": "success",
            "total": len(prestamos),
            "prestamos": prestamos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/cliente/{id_cliente}/prestamos/{id_prestamo}/pagos")
def obtener_calendario_pagos(id_cliente: int, id_prestamo: int):
    """Devuelve el calendario de pagos de un préstamo del cliente."""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar que el préstamo pertenece al cliente
        cursor.execute("""
            SELECT id_prestamo FROM prestamos
            WHERE id_prestamo = %s AND id_cliente = %s
        """, (id_prestamo, id_cliente))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Préstamo no encontrado")

        cursor.execute("""
            SELECT id_pago, numero_pago, fecha_vencimiento, monto, estado, fecha_pago
            FROM pagos
            WHERE id_prestamo = %s
            ORDER BY numero_pago
        """, (id_prestamo,))

        pagos = cursor.fetchall()

        for p in pagos:
            for campo in ['fecha_vencimiento', 'fecha_pago']:
                if p.get(campo) and hasattr(p[campo], 'isoformat'):
                    p[campo] = p[campo].isoformat()
            p['monto'] = float(p['monto'] or 0)

        return {
            "status": "success",
            "id_prestamo": id_prestamo,
            "total_pagos": len(pagos),
            "pagos": pagos
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.post("/cliente/solicitar_credito")
def solicitar_credito(request: SolicitudCreditoRequest):
    """El cliente solicita un nuevo crédito. Queda en estado PENDIENTE."""
    TASA_MENSUAL = 0.05

    if request.monto < 1000 or request.monto > 50000:
        raise HTTPException(status_code=400, detail="El monto debe estar entre $1,000 y $50,000")
    if request.plazo_meses not in [6, 12, 24, 36, 48]:
        raise HTTPException(status_code=400, detail="Plazo inválido. Opciones: 6, 12, 24, 36, 48 meses")

    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Verificar que el cliente existe y es Cliente
        cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE id_usuario = %s", (request.id_cliente,))
        usuario = cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        if usuario['rol'] != 'Cliente':
            raise HTTPException(status_code=403, detail="Solo los clientes pueden solicitar créditos")

        # Verificar que no tenga otro crédito PENDIENTE activo
        cursor.execute("""
            SELECT id_prestamo FROM prestamos
            WHERE id_cliente = %s AND estado = 'PENDIENTE'
        """, (request.id_cliente,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya tienes una solicitud pendiente de revisión")

        # Calcular cuota mensual (amortización francesa)
        tasa  = TASA_MENSUAL
        plazo = request.plazo_meses
        cuota = request.monto * (tasa * (1 + tasa)**plazo) / ((1 + tasa)**plazo - 1)
        saldo_total = round(cuota * plazo, 2)

        cursor.execute("""
            INSERT INTO prestamos
                (id_cliente, monto_total, saldo_pendiente, tasa_interes, plazo_meses, estado, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, 'PENDIENTE', NOW())
        """, (request.id_cliente, request.monto, saldo_total, tasa, plazo))

        db.commit()
        id_prestamo = cursor.lastrowid

        return {
            "status": "success",
            "message": "Solicitud enviada. Un empleado la revisará pronto.",
            "id_prestamo": id_prestamo,
            "cuota_mensual": round(cuota, 2),
            "plazo_meses": plazo,
            "monto": request.monto
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/cliente/{id_cliente}/perfil")
def obtener_perfil(id_cliente: int):
    """Devuelve el perfil completo del cliente."""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno,
                   email, telefono, curp, direccion, no_identificacion,
                   fecha_registro, email_verificado
            FROM usuarios
            WHERE id_usuario = %s AND rol = 'Cliente'
        """, (id_cliente,))

        usuario = cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        usuario['email_verificado'] = bool(usuario.get('email_verificado', False))
        if usuario.get('fecha_registro') and hasattr(usuario['fecha_registro'], 'isoformat'):
            usuario['fecha_registro'] = usuario['fecha_registro'].isoformat()

        return {"status": "success", "perfil": usuario}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.put("/cliente/{id_cliente}/perfil")
def actualizar_perfil(id_cliente: int, request: ActualizarPerfilRequest):
    """Actualiza los datos del perfil del cliente."""
    db = conectar()
    cursor = db.cursor(dictionary=True)
    try:
        # Solo actualizar campos que vienen en el request
        campos = {}
        if request.nombre           is not None: campos['nombre']           = request.nombre
        if request.apellido_paterno is not None: campos['apellido_paterno'] = request.apellido_paterno
        if request.apellido_materno is not None: campos['apellido_materno'] = request.apellido_materno
        if request.telefono         is not None: campos['telefono']         = request.telefono
        if request.direccion        is not None: campos['direccion']        = request.direccion

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        set_clause = ", ".join(f"{k} = %s" for k in campos)
        valores    = list(campos.values()) + [id_cliente]

        cursor.execute(
            f"UPDATE usuarios SET {set_clause} WHERE id_usuario = %s AND rol = 'Cliente'",
            valores
        )
        db.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return {"status": "success", "message": "Perfil actualizado correctamente"}
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
