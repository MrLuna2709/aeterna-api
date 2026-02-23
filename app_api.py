"""
═══════════════════════════════════════════════════════════════════════════════
API ACTUALIZADA - MONTE SIN PIEDAD
Con Resend para emails y tabla usuarios unificada
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

# Configurar API key de Resend
resend.api_key = os.environ.get("RESEND_API_KEY", "")

# ==================== CONFIGURACIÓN ====================
app = FastAPI()

DB_CONFIG = {
    'host': 'junction.proxy.rlwy.net',
    'port': 16661,
    'user': 'root',
    'password': 'rOhOhfujlMBVGnrTtIYJQLAtxcMlsBOP',
    'database': 'railway'
}

def conectar():
    """Conecta a la base de datos"""
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

class RecuperacionRequest(BaseModel):
    email: str
    codigo: str
    nueva_password: str

# ==================== FUNCIONES DE EMAIL (RESEND) ====================

def enviar_email_resend(destinatario: str, asunto: str, html: str):
    """
    Envía email usando Resend (HTTPS, no SMTP)
    Funciona en Railway sin problemas
    """
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
    """Envía código de recuperación de contraseña"""
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
          <p style="color:#475569;line-height:1.6;">
            Recibimos una solicitud para restablecer tu contraseña en <strong>Monte de Piedad</strong>.
          </p>
          <p style="color:#475569;line-height:1.6;">Usa el siguiente código de verificación:</p>
          
          <div style="background:#f8fafc;border:2px solid #e2e8f0;border-radius:12px;padding:30px;text-align:center;margin:30px 0;">
            <div style="font-size:40px;font-weight:900;color:#A6032F;letter-spacing:12px;font-family:'Courier New',monospace;">
              {codigo}
            </div>
            <div style="font-size:12px;color:#64748b;margin-top:10px;text-transform:uppercase;">
              Código de verificación
            </div>
          </div>
          
          <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:15px;border-radius:8px;margin:20px 0;">
            <p style="font-size:14px;color:#92400e;margin:0;">
              ⏰ <strong>Este código expira en 15 minutos.</strong><br>
              🔒 Si no solicitaste este cambio, ignora este mensaje.
            </p>
          </div>
          
          <p style="color:#64748b;font-size:14px;line-height:1.6;margin-top:30px;">
            Por tu seguridad, nunca compartas este código con nadie.
          </p>
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

def email_bienvenida(destinatario: str, nombre: str):
    """Envía email de bienvenida a nuevos clientes"""
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
            <p style="font-size:18px;color:#1e293b;font-weight:600;margin:0;">
              Hola {nombre}, ¡Es un placer tenerte con nosotros!
            </p>
          </div>
          
          <p style="color:#475569;line-height:1.8;margin:25px 0;">
            Tu cuenta está lista. Ahora puedes acceder a todos nuestros servicios financieros.
          </p>
          
          <p style="color:#64748b;font-size:14px;line-height:1.6;margin-top:30px;">
            Si tienes alguna duda, nuestro equipo está disponible para asistirte.
          </p>
        </div>
        <div style="text-align:center;padding:30px;font-size:12px;color:#94a3b8;border-top:1px solid #e2e8f0;">
          <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
        </div>
      </div>
    </body>
    </html>
    """
    
    return enviar_email_resend(destinatario, f"🎉 ¡Bienvenido a Monte de Piedad, {nombre}!", html)

# ==================== ENDPOINTS UNIFICADOS ====================

@app.post("/login")
def login_unificado(request: LoginRequest):
    """
    Login unificado para TODOS los usuarios
    Retorna el usuario con su rol (Admin, Empleado, o Cliente)
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Buscar usuario por email en la tabla unificada
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno, 
                   email, rol, activo, curp, telefono
            FROM usuarios
            WHERE email = %s AND password = %s
        """, (request.email, request.password))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        if not usuario.get('activo', True):
            raise HTTPException(status_code=403, detail="Cuenta desactivada")
        
        # Retornar usuario con su rol
        return {
            "status": "success",
            "message": "Login exitoso",
            "usuario": {
                "id_usuario": usuario['id_usuario'],
                "nombre": usuario['nombre'],
                "apellido_paterno": usuario.get('apellido_paterno', ''),
                "apellido_materno": usuario.get('apellido_materno', ''),
                "email": usuario['email'],
                "rol": usuario['rol'],  # 'Admin', 'Empleado', o 'Cliente'
                "curp": usuario.get('curp'),
                "telefono": usuario.get('telefono')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/registrar_cliente")
def registrar_cliente(request: RegistroClienteRequest):
    """
    Registra un nuevo cliente en la tabla usuarios con rol='Cliente'
    """
    db = conectar()
    cursor = db.cursor()
    
    try:
        # Verificar si el email ya existe
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (request.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Verificar si el CURP ya existe (si se proporciona)
        if request.curp:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE curp = %s", (request.curp,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="El CURP ya está registrado")
        
        # Insertar nuevo cliente en tabla usuarios
        query = """
        INSERT INTO usuarios 
        (nombre, apellido_paterno, apellido_materno, email, password, rol, 
         curp, telefono, direccion, no_identificacion, activo)
        VALUES (%s, %s, %s, %s, %s, 'Cliente', %s, %s, %s, %s, TRUE)
        """
        
        cursor.execute(query, (
            request.nombre,
            request.apellido_paterno,
            request.apellido_materno,
            request.email,
            request.password,
            request.curp,
            request.telefono,
            request.direccion,
            request.no_identificacion
        ))
        
        db.commit()
        id_cliente = cursor.lastrowid
        
        # Enviar email de bienvenida
        try:
            email_bienvenida(request.email, request.nombre)
        except Exception as e:
            print(f"⚠️  Cliente registrado pero email no enviado: {e}")
        
        return {
            "status": "success",
            "message": "Cliente registrado exitosamente",
            "id_cliente": id_cliente
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/solicitar_codigo")
def solicitar_codigo_recuperacion(email: str = Query(...)):
    """
    Genera código de recuperación y lo envía por email usando Resend
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Buscar usuario por email (sin importar el rol)
        cursor.execute("""
            SELECT id_usuario, nombre, email 
            FROM usuarios 
            WHERE email = %s
        """, (email,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="El correo no está registrado")
        
        # Generar código de 6 dígitos
        codigo = str(random.randint(100000, 999999))
        
        # Guardar código en la base de datos
        cursor.execute("""
            UPDATE usuarios
            SET codigo_recuperacion = %s, fecha_codigo = NOW()
            WHERE email = %s
        """, (codigo, email))
        
        db.commit()
        
        # Enviar email con código usando Resend
        try:
            email_codigo_recuperacion(email, codigo, usuario['nombre'])
        except Exception as mail_error:
            # Si falla el envío, revertir cambios
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Código generado pero no se pudo enviar el correo: {str(mail_error)}"
            )
        
        return {
            "status": "success",
            "message": f"Código enviado a {email}"
            # NO incluir codigo_debug en producción
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/verificar_codigo")
def verificar_codigo(request: RecuperacionRequest):
    """
    Verifica el código de recuperación y actualiza la contraseña
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)
    
    try:
        # Buscar usuario con el código
        cursor.execute("""
            SELECT id_usuario, codigo_recuperacion, fecha_codigo
            FROM usuarios
            WHERE email = %s
        """, (request.email,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        if not usuario['codigo_recuperacion']:
            raise HTTPException(status_code=400, detail="No hay código de recuperación pendiente")
        
        if usuario['codigo_recuperacion'] != request.codigo:
            raise HTTPException(status_code=401, detail="Código incorrecto")
        
        # Verificar que el código no haya expirado (15 minutos)
        if usuario['fecha_codigo']:
            tiempo_transcurrido = datetime.now() - usuario['fecha_codigo']
            if tiempo_transcurrido.total_seconds() > 900:  # 15 minutos
                raise HTTPException(status_code=410, detail="El código ha expirado. Solicita uno nuevo.")
        
        # Actualizar contraseña y limpiar código
        cursor.execute("""
            UPDATE usuarios
            SET password = %s, 
                codigo_recuperacion = NULL, 
                fecha_codigo = NULL
            WHERE email = %s
        """, (request.nueva_password, request.email))
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Contraseña actualizada correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ==================== ENDPOINTS DE CONSULTA ====================

@app.get("/usuarios")
def obtener_usuarios(rol: Optional[str] = None):
    """
    Obtiene lista de usuarios
    Si se especifica rol, filtra por ese rol
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)
    
    try:
        if rol:
            cursor.execute("""
                SELECT id_usuario, nombre, apellido_paterno, apellido_materno, 
                       email, rol, activo, fecha_registro
                FROM usuarios
                WHERE rol = %s
                ORDER BY fecha_registro DESC
            """, (rol,))
        else:
            cursor.execute("""
                SELECT id_usuario, nombre, apellido_paterno, apellido_materno, 
                       email, rol, activo, fecha_registro
                FROM usuarios
                ORDER BY fecha_registro DESC
            """)
        
        usuarios = cursor.fetchall()
        
        return {
            "status": "success",
            "total": len(usuarios),
            "usuarios": usuarios
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/empleados")
def obtener_empleados():
    """
    Obtiene solo empleados y administradores
    """
    return obtener_usuarios(rol="Empleado")

@app.get("/clientes")
def obtener_clientes():
    """
    Obtiene solo clientes
    """
    return obtener_usuarios(rol="Cliente")

@app.get("/usuario/{id_usuario}")
def obtener_usuario(id_usuario: int):
    """
    Obtiene datos de un usuario específico
    """
    db = conectar()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id_usuario, nombre, apellido_paterno, apellido_materno,
                   email, rol, curp, telefono, direccion, no_identificacion,
                   activo, fecha_registro
            FROM usuarios
            WHERE id_usuario = %s
        """, (id_usuario,))
        
        usuario = cursor.fetchone()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "status": "success",
            "usuario": usuario
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ==================== ENDPOINTS DE ADMINISTRACIÓN ====================

@app.post("/admin/crear_empleado")
def crear_empleado(request: dict):
    """
    Crea un nuevo empleado o administrador
    """
    db = conectar()
    cursor = db.cursor()
    
    try:
        # Verificar que el rol sea válido
        rol = request.get('rol', 'Empleado')
        if rol not in ['Admin', 'Empleado']:
            raise HTTPException(status_code=400, detail="Rol inválido para empleado")
        
        # Verificar email único
        cursor.execute("SELECT id_usuario FROM usuarios WHERE email = %s", (request['email'],))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        
        # Insertar empleado
        query = """
        INSERT INTO usuarios 
        (nombre, apellido_paterno, apellido_materno, email, password, rol, activo)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """
        
        cursor.execute(query, (
            request['nombre'],
            request.get('apellido_paterno', ''),
            request.get('apellido_materno', ''),
            request['email'],
            request['password'],
            rol
        ))
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"{rol} creado exitosamente",
            "id_usuario": cursor.lastrowid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.put("/usuario/{id_usuario}")
def actualizar_usuario(id_usuario: int, request: dict):
    """
    Actualiza datos de un usuario
    """
    db = conectar()
    cursor = db.cursor()
    
    try:
        # Construir query dinámicamente según campos proporcionados
        campos_actualizar = []
        valores = []
        
        campos_permitidos = ['nombre', 'apellido_paterno', 'apellido_materno', 
                            'email', 'telefono', 'direccion', 'curp']
        
        for campo in campos_permitidos:
            if campo in request:
                campos_actualizar.append(f"{campo} = %s")
                valores.append(request[campo])
        
        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        valores.append(id_usuario)
        
        query = f"UPDATE usuarios SET {', '.join(campos_actualizar)} WHERE id_usuario = %s"
        cursor.execute(query, valores)
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "status": "success",
            "message": "Usuario actualizado correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/usuario/{id_usuario}")
def desactivar_usuario(id_usuario: int):
    """
    Desactiva un usuario (no lo elimina)
    """
    db = conectar()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET activo = FALSE 
            WHERE id_usuario = %s
        """, (id_usuario,))
        
        db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "status": "success",
            "message": "Usuario desactivado correctamente"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ==================== ENDPOINT RAÍZ ====================

@app.get("/")
def root():
    return {
        "app": "Monte SIN Piedad API",
        "version": "2.0",
        "features": [
            "Login unificado",
            "Tabla usuarios única",
            "Emails con Resend (HTTPS)",
            "Recuperación de contraseña",
            "CRUD completo de usuarios"
        ],
        "status": "✅ Operativo"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
