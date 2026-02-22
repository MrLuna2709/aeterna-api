"""
SISTEMA DE NOTIFICACIONES Y EMAILS - COMPLETO
Monte de Piedad - Versión Final
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
try:
    from win10toast import ToastNotifier
    TOAST_DISPONIBLE = True
except ImportError:
    TOAST_DISPONIBLE = False
    print("⚠️ win10toast no instalado. Notificaciones Desktop deshabilitadas.")

# ==================== CONFIGURACIÓN GMAIL ====================

# ==================== IMPORTAR CONFIGURACIÓN EXTERNA ====================
try:
    from CONFIG_EMAIL import (
        GMAIL_USER,
        GMAIL_APP_PASSWORD,
        SMTP_SERVER,
        SMTP_PORT,
        SENDER_NAME,
        EMAIL_CONFIGURED
    )
    if not EMAIL_CONFIGURED:
        print("⚠️  Sistema de notificaciones NO configurado")
        print("    Edita CONFIG_EMAIL.py con tus credenciales de Gmail")
        print("    Ver: GUIA_CONFIGURAR_EMAILS.md")
except ImportError:
    print("❌ Error: No se encontró CONFIG_EMAIL.py")
    print("   Crea el archivo CONFIG_EMAIL.py con tus credenciales")
    GMAIL_USER = "noreply@example.com"
    GMAIL_APP_PASSWORD = "xxxx"
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_NAME = "Monte de Piedad"
    EMAIL_CONFIGURED = False

# ==================== SISTEMA DE EMAILS ====================

def enviar_email(destinatario, asunto, cuerpo_html):
    """
    Envía un email usando Gmail SMTP.
    
    Args:
        destinatario (str): Email del receptor
        asunto (str): Asunto del email
        cuerpo_html (str): Contenido en HTML
        
    Returns:
        bool: True si se envió correctamente, False si hubo error
    """
    # Verificar que esté configurado
    if not EMAIL_CONFIGURED:
        print(f"⚠️  Email NO enviado a {destinatario} (sistema no configurado)")
        return False
    
    try:
        mensaje = MIMEMultipart('alternative')
        mensaje['From'] = f"Monte de Piedad <{GMAIL_USER}>"
        mensaje['To'] = destinatario
        mensaje['Subject'] = asunto
        
        parte_html = MIMEText(cuerpo_html, 'html', 'utf-8')
        mensaje.attach(parte_html)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(mensaje)
        server.quit()
        
        print(f"✅ Email enviado a {destinatario}")
        return True
        
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
        return False


def email_codigo_recuperacion(destinatario, codigo, nombre="Usuario"):
    """Envía email con código de recuperación de contraseña"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #A6032F 0%, #800020 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 16px;
                color: #334155;
                margin-bottom: 20px;
            }}
            .code-container {{
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin: 30px 0;
            }}
            .code {{
                font-size: 36px;
                font-weight: 700;
                color: #A6032F;
                letter-spacing: 8px;
                font-family: 'Courier New', monospace;
            }}
            .code-label {{
                font-size: 12px;
                color: #64748b;
                margin-top: 10px;
                text-transform: uppercase;
            }}
            .warning {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .warning-text {{
                font-size: 14px;
                color: #92400e;
                margin: 0;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 RECUPERACIÓN DE CONTRASEÑA</h1>
            </div>
            <div class="content">
                <p class="greeting">Hola <strong>{nombre}</strong>,</p>
                <p style="color: #475569; line-height: 1.6;">
                    Recibimos una solicitud para restablecer la contraseña de tu cuenta en 
                    <strong>Monte de Piedad</strong>.
                </p>
                <p style="color: #475569; line-height: 1.6;">
                    Usa el siguiente código de verificación de 6 dígitos:
                </p>
                
                <div class="code-container">
                    <div class="code">{codigo}</div>
                    <div class="code-label">Código de verificación</div>
                </div>
                
                <div class="warning">
                    <p class="warning-text">
                        ⏰ <strong>Este código expira en 15 minutos.</strong><br>
                        🔒 Si no solicitaste este cambio, ignora este mensaje.
                    </p>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 30px;">
                    Por tu seguridad, nunca compartas este código con nadie. 
                    El personal de Monte de Piedad jamás te solicitará este código.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = f"🔐 Código de Recuperación: {codigo}"
    return enviar_email(destinatario, asunto, html)


def email_bienvenida(destinatario, nombre):
    """Envía email de bienvenida a nuevos clientes"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #A6032F 0%, #800020 100%);
                padding: 50px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0 0 10px 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .header p {{
                color: rgba(255,255,255,0.9);
                margin: 0;
                font-size: 16px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .welcome-box {{
                background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                padding: 25px;
                border-radius: 12px;
                margin: 20px 0;
                text-align: center;
            }}
            .welcome-text {{
                font-size: 18px;
                color: #1e293b;
                font-weight: 600;
                margin: 0;
            }}
            .features {{
                margin: 30px 0;
            }}
            .feature {{
                display: flex;
                align-items: start;
                margin: 15px 0;
                padding: 15px;
                border-left: 3px solid #A6032F;
                background-color: #f8fafc;
                border-radius: 8px;
            }}
            .feature-icon {{
                font-size: 24px;
                margin-right: 15px;
            }}
            .feature-text {{
                flex: 1;
            }}
            .feature-title {{
                font-weight: 600;
                color: #1e293b;
                margin: 0 0 5px 0;
            }}
            .feature-desc {{
                color: #64748b;
                margin: 0;
                font-size: 14px;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>¡Bienvenido a Monte de Piedad! 🎉</h1>
                <p>Tu cuenta ha sido creada exitosamente</p>
            </div>
            <div class="content">
                <div class="welcome-box">
                    <p class="welcome-text">Hola {nombre}, ¡Es un placer tenerte con nosotros!</p>
                </div>
                
                <p style="color: #475569; line-height: 1.8; margin: 25px 0;">
                    Tu cuenta en Monte de Piedad está lista. Ahora puedes acceder a todos nuestros servicios 
                    financieros diseñados para ayudarte a alcanzar tus metas.
                </p>
                
                <div class="features">
                    <h3 style="color: #1e293b; margin-bottom: 20px;">¿Qué puedes hacer ahora?</h3>
                    
                    <div class="feature">
                        <div class="feature-icon">💰</div>
                        <div class="feature-text">
                            <p class="feature-title">Solicitar Préstamos</p>
                            <p class="feature-desc">Accede a préstamos con tasas competitivas y plazos flexibles hasta 48 meses.</p>
                        </div>
                    </div>
                    
                    <div class="feature">
                        <div class="feature-icon">📊</div>
                        <div class="feature-text">
                            <p class="feature-title">Consultar tu Cartera</p>
                            <p class="feature-desc">Revisa el estado de tus préstamos activos en tiempo real.</p>
                        </div>
                    </div>
                    
                    <div class="feature">
                        <div class="feature-icon">📅</div>
                        <div class="feature-text">
                            <p class="feature-title">Ver Calendario de Pagos</p>
                            <p class="feature-desc">Mantente al día con tus fechas de vencimiento y montos.</p>
                        </div>
                    </div>
                    
                    <div class="feature">
                        <div class="feature-icon">🔔</div>
                        <div class="feature-text">
                            <p class="feature-title">Recibir Notificaciones</p>
                            <p class="feature-desc">Te avisaremos antes de cada vencimiento para que nunca te atrases.</p>
                        </div>
                    </div>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 30px;">
                    Si tienes alguna duda o necesitas ayuda, nuestro equipo está disponible para asistirte.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = f"🎉 ¡Bienvenido a Monte de Piedad, {nombre}!"
    return enviar_email(destinatario, asunto, html)


def email_ticket_pago(destinatario, folio, monto, numero_pago, total_pagos, cliente):
    """Envía email con comprobante de pago (ticket)"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .success-icon {{
                font-size: 64px;
                margin-bottom: 10px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .ticket {{
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 25px;
                margin: 20px 0;
                background-color: #f8fafc;
            }}
            .ticket-row {{
                display: flex;
                justify-content: space-between;
                padding: 12px 0;
                border-bottom: 1px solid #e2e8f0;
            }}
            .ticket-row:last-child {{
                border-bottom: none;
            }}
            .ticket-label {{
                color: #64748b;
                font-size: 14px;
            }}
            .ticket-value {{
                color: #1e293b;
                font-weight: 600;
                font-size: 14px;
            }}
            .amount-box {{
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                border: 2px solid #10b981;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }}
            .amount-label {{
                color: #065f46;
                font-size: 12px;
                margin-bottom: 5px;
            }}
            .amount-value {{
                color: #059669;
                font-size: 32px;
                font-weight: 700;
            }}
            .folio-box {{
                background-color: #1e293b;
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                letter-spacing: 2px;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="success-icon">✅</div>
                <h1>PAGO RECIBIDO EXITOSAMENTE</h1>
            </div>
            <div class="content">
                <p style="color: #475569; line-height: 1.6; text-align: center;">
                    Tu pago ha sido procesado correctamente. 
                    Guarda este comprobante para tus registros.
                </p>
                
                <div class="amount-box">
                    <div class="amount-label">MONTO PAGADO</div>
                    <div class="amount-value">${monto:,.2f}</div>
                </div>
                
                <div class="folio-box">
                    FOLIO: {folio}
                </div>
                
                <div class="ticket">
                    <h3 style="margin: 0 0 20px 0; color: #1e293b;">Detalles del Pago</h3>
                    
                    <div class="ticket-row">
                        <span class="ticket-label">Cliente</span>
                        <span class="ticket-value">{cliente}</span>
                    </div>
                    
                    <div class="ticket-row">
                        <span class="ticket-label">Mensualidad</span>
                        <span class="ticket-value">{numero_pago} de {total_pagos}</span>
                    </div>
                    
                    <div class="ticket-row">
                        <span class="ticket-label">Fecha y Hora</span>
                        <span class="ticket-value">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</span>
                    </div>
                    
                    <div class="ticket-row">
                        <span class="ticket-label">Folio</span>
                        <span class="ticket-value">{folio}</span>
                    </div>
                </div>
                
                <p style="color: #64748b; font-size: 13px; line-height: 1.6; margin-top: 25px; padding: 15px; background-color: #f1f5f9; border-radius: 8px;">
                    💡 <strong>Importante:</strong> Conserva este comprobante. 
                    Puedes consultarlo en cualquier momento presentando el folio en sucursal 
                    o desde tu cuenta en la aplicación.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Comprobante Oficial</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = f"✅ Pago Recibido - Folio {folio}"
    return enviar_email(destinatario, asunto, html)


def email_prestamo_aprobado(destinatario, nombre, monto, plazo_meses, cuota_mensual, id_prestamo):
    """Envía email cuando un préstamo es aprobado"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                padding: 50px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .success-icon {{
                font-size: 72px;
                margin-bottom: 15px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .congratulations {{
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                border: 2px solid #10b981;
            }}
            .congrats-text {{
                font-size: 20px;
                color: #065f46;
                font-weight: 600;
                margin: 0;
            }}
            .details-box {{
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 25px;
                margin: 25px 0;
                background-color: #f8fafc;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 12px 0;
                border-bottom: 1px solid #e2e8f0;
            }}
            .detail-row:last-child {{
                border-bottom: none;
                padding-top: 15px;
                margin-top: 10px;
                border-top: 2px solid #cbd5e1;
            }}
            .detail-label {{
                color: #64748b;
                font-size: 14px;
            }}
            .detail-value {{
                color: #1e293b;
                font-weight: 600;
                font-size: 14px;
            }}
            .highlight-value {{
                color: #A6032F;
                font-size: 20px;
                font-weight: 700;
            }}
            .info-box {{
                background-color: #eff6ff;
                border-left: 4px solid #3b82f6;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .info-text {{
                color: #1e40af;
                margin: 0;
                font-size: 14px;
                line-height: 1.6;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="success-icon">🎉</div>
                <h1>¡PRÉSTAMO APROBADO!</h1>
            </div>
            <div class="content">
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{nombre}</strong>,
                </p>
                
                <div class="congratulations">
                    <p class="congrats-text">¡Excelentes noticias! Tu solicitud ha sido aprobada</p>
                </div>
                
                <p style="color: #475569; line-height: 1.6; margin: 25px 0;">
                    Nos complace informarte que tu préstamo ha sido <strong style="color: #059669;">APROBADO</strong> 
                    y está listo para ser utilizado.
                </p>
                
                <div class="details-box">
                    <h3 style="margin: 0 0 20px 0; color: #1e293b;">Detalles de tu Préstamo</h3>
                    
                    <div class="detail-row">
                        <span class="detail-label">Número de Préstamo</span>
                        <span class="detail-value">#{id_prestamo:05d}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Monto Aprobado</span>
                        <span class="detail-value">${monto:,.2f}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Plazo</span>
                        <span class="detail-value">{plazo_meses} meses</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="detail-label">Cuota Mensual</span>
                        <span class="highlight-value">${cuota_mensual:,.2f}</span>
                    </div>
                </div>
                
                <div class="info-box">
                    <p class="info-text">
                        📅 <strong>Primer pago:</strong> 30 días a partir de hoy<br>
                        💳 <strong>Forma de pago:</strong> Efectivo en sucursal o con empleado de cobranza
                    </p>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 25px;">
                    Puedes consultar tu calendario de pagos completo en tu portal de cliente. 
                    ¡Gracias por confiar en nosotros!
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = f"🎉 ¡Préstamo Aprobado! - ${monto:,.0f}"
    return enviar_email(destinatario, asunto, html)


def email_prestamo_rechazado(destinatario, nombre, monto):
    """Envía email cuando un préstamo es rechazado"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #64748b 0%, #475569 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .message-box {{
                background-color: #fef2f2;
                border-left: 4px solid #ef4444;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .message-text {{
                color: #7f1d1d;
                margin: 0;
                font-size: 14px;
                line-height: 1.6;
            }}
            .info-box {{
                background-color: #f8fafc;
                padding: 20px;
                border-radius: 12px;
                margin: 25px 0;
                border: 2px solid #e2e8f0;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Actualización de tu Solicitud</h1>
            </div>
            <div class="content">
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{nombre}</strong>,
                </p>
                
                <p style="color: #475569; line-height: 1.6; margin: 25px 0;">
                    Lamentamos informarte que en esta ocasión tu solicitud de préstamo 
                    por <strong>${monto:,.2f}</strong> no pudo ser aprobada.
                </p>
                
                <div class="message-box">
                    <p class="message-text">
                        <strong>Importante:</strong> Esta decisión no afecta tu historial crediticio 
                        y puedes volver a solicitar en el futuro.
                    </p>
                </div>
                
                <div class="info-box">
                    <h3 style="margin: 0 0 15px 0; color: #1e293b;">¿Qué puedes hacer?</h3>
                    <ul style="color: #475569; line-height: 1.8; margin: 0; padding-left: 20px;">
                        <li>Contacta a uno de nuestros asesores para más información</li>
                        <li>Revisa y actualiza tus datos personales</li>
                        <li>Puedes volver a solicitar en cualquier momento</li>
                    </ul>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 25px;">
                    Si tienes dudas o necesitas asistencia, nuestro equipo está disponible para ayudarte.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Sistema Seguro</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = "Actualización de tu Solicitud - Monte de Piedad"
    return enviar_email(destinatario, asunto, html)


def email_recordatorio_pago(destinatario, nombre, numero_pago, monto, fecha_vencimiento, dias_restantes):
    """Envía recordatorio de pago próximo (3 días antes)"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .bell-icon {{
                font-size: 64px;
                margin-bottom: 10px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .payment-card {{
                background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
                border: 2px solid #f59e0b;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin: 25px 0;
            }}
            .payment-label {{
                color: #92400e;
                font-size: 12px;
                margin-bottom: 5px;
                text-transform: uppercase;
            }}
            .payment-number {{
                color: #78350f;
                font-size: 16px;
                margin: 10px 0;
            }}
            .payment-amount {{
                color: #A6032F;
                font-size: 36px;
                font-weight: 700;
                margin: 15px 0;
            }}
            .payment-date {{
                color: #475569;
                font-size: 16px;
                margin: 10px 0;
            }}
            .countdown {{
                background-color: #f59e0b;
                color: white;
                padding: 12px 25px;
                border-radius: 25px;
                display: inline-block;
                font-size: 18px;
                font-weight: 700;
                margin-top: 15px;
            }}
            .tip-box {{
                background-color: #eff6ff;
                border-left: 4px solid #3b82f6;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .tip-text {{
                color: #1e40af;
                margin: 0;
                font-size: 14px;
                line-height: 1.6;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="bell-icon">🔔</div>
                <h1>RECORDATORIO DE PAGO</h1>
            </div>
            <div class="content">
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{nombre}</strong>,
                </p>
                
                <p style="color: #475569; line-height: 1.6; margin: 25px 0;">
                    Te recordamos que tienes una mensualidad próxima a vencer.
                </p>
                
                <div class="payment-card">
                    <div class="payment-label">Mensualidad</div>
                    <div class="payment-number">#{numero_pago}</div>
                    <div class="payment-amount">${monto:,.2f}</div>
                    <div class="payment-date">📅 Vence el: <strong>{fecha_vencimiento}</strong></div>
                    <div class="countdown">⏰ {dias_restantes} días restantes</div>
                </div>
                
                <div class="tip-box">
                    <p class="tip-text">
                        💡 <strong>Tip:</strong> Realiza tu pago con anticipación para evitar recargos por mora 
                        y mantener tu historial crediticio limpio.
                    </p>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 25px;">
                    Puedes realizar tu pago en cualquiera de nuestras sucursales 
                    o con tu empleado de cobranza asignado.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Sistema de Recordatorios</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = f"🔔 Recordatorio: Pago vence en {dias_restantes} días"
    return enviar_email(destinatario, asunto, html)


def email_pago_vencido(destinatario, nombre, numero_pago, monto, dias_atraso):
    """Envía alerta de pago vencido"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .warning-icon {{
                font-size: 64px;
                margin-bottom: 10px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .alert-card {{
                background-color: #fee2e2;
                border: 3px solid #ef4444;
                border-radius: 12px;
                padding: 30px;
                text-align: center;
                margin: 25px 0;
            }}
            .alert-label {{
                color: #991b1b;
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 10px;
                text-transform: uppercase;
            }}
            .payment-info {{
                color: #1e293b;
                font-size: 16px;
                margin: 10px 0;
            }}
            .amount-overdue {{
                color: #dc2626;
                font-size: 36px;
                font-weight: 700;
                margin: 15px 0;
            }}
            .days-overdue {{
                background-color: #dc2626;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                display: inline-block;
                font-size: 16px;
                font-weight: 700;
                margin-top: 10px;
            }}
            .urgent-box {{
                background-color: #fef2f2;
                border-left: 4px solid #dc2626;
                padding: 20px;
                border-radius: 8px;
                margin: 25px 0;
            }}
            .urgent-text {{
                color: #7f1d1d;
                margin: 0;
                font-size: 14px;
                line-height: 1.8;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="warning-icon">⚠️</div>
                <h1>PAGO VENCIDO - ACCIÓN REQUERIDA</h1>
            </div>
            <div class="content">
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{nombre}</strong>,
                </p>
                
                <p style="color: #475569; line-height: 1.6; margin: 25px 0;">
                    Te informamos que tienes una mensualidad <strong style="color: #dc2626;">vencida</strong> 
                    que requiere tu atención inmediata.
                </p>
                
                <div class="alert-card">
                    <div class="alert-label">⚠️ PAGO VENCIDO</div>
                    <div class="payment-info">Mensualidad #{numero_pago}</div>
                    <div class="amount-overdue">${monto:,.2f}</div>
                    <div class="days-overdue">{dias_atraso} {'día' if dias_atraso == 1 else 'días'} de atraso</div>
                </div>
                
                <div class="urgent-box">
                    <p class="urgent-text">
                        <strong>⚡ Importante:</strong><br>
                        • Los pagos atrasados generan intereses moratorios adicionales<br>
                        • El atraso afecta tu historial crediticio<br>
                        • Puedes incurrir en penalizaciones<br>
                        • Contacta con nosotros para regularizar tu situación
                    </p>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 25px;">
                    Por favor, ponte al corriente lo antes posible. Puedes realizar tu pago 
                    en sucursal o contactar a tu empleado de cobranza para acordar un plan de pago.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Sistema de Alertas</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = f"⚠️ URGENTE: Pago Vencido - {dias_atraso} {'día' if dias_atraso == 1 else 'días'} de atraso"
    return enviar_email(destinatario, asunto, html)


def email_prestamo_liquidado(destinatario, nombre, monto_original, descuento, total_pagado, folio):
    """Envía felicitación por préstamo liquidado"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f1f5f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                padding: 50px 30px;
                text-align: center;
            }}
            .header h1 {{
                color: white;
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .celebration-icon {{
                font-size: 80px;
                margin-bottom: 15px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .celebration-box {{
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 3px solid #22c55e;
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                margin: 25px 0;
            }}
            .celebration-badge {{
                background-color: #059669;
                color: white;
                padding: 10px 25px;
                border-radius: 25px;
                display: inline-block;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 15px;
            }}
            .celebration-text {{
                color: #065f46;
                font-size: 22px;
                font-weight: 700;
                margin: 0;
            }}
            .summary-box {{
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 25px;
                margin: 25px 0;
            }}
            .summary-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e2e8f0;
            }}
            .summary-row:last-child {{
                border-bottom: none;
                padding-top: 15px;
                margin-top: 10px;
                border-top: 2px solid #cbd5e1;
            }}
            .summary-label {{
                color: #64748b;
                font-size: 14px;
            }}
            .summary-value {{
                color: #1e293b;
                font-weight: 600;
                font-size: 14px;
            }}
            .highlight-value {{
                color: #059669;
                font-size: 18px;
                font-weight: 700;
            }}
            .folio-box {{
                background-color: #1e293b;
                color: white;
                padding: 12px;
                border-radius: 8px;
                text-align: center;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                letter-spacing: 2px;
                margin: 20px 0;
            }}
            .benefits-box {{
                background-color: #dbeafe;
                border-left: 4px solid #3b82f6;
                padding: 20px;
                border-radius: 8px;
                margin: 25px 0;
            }}
            .benefits-text {{
                color: #1e40af;
                margin: 0;
                font-size: 14px;
                line-height: 1.8;
            }}
            .footer {{
                text-align: center;
                padding: 30px;
                font-size: 12px;
                color: #94a3b8;
                border-top: 1px solid #e2e8f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="celebration-icon">🎊</div>
                <h1>¡FELICIDADES!</h1>
            </div>
            <div class="content">
                <p style="color: #475569; font-size: 16px; line-height: 1.6;">
                    Hola <strong>{nombre}</strong>,
                </p>
                
                <div class="celebration-box">
                    <div class="celebration-badge">✓ PRÉSTAMO LIQUIDADO</div>
                    <p class="celebration-text">Has liquidado tu préstamo completamente</p>
                </div>
                
                <p style="color: #475569; line-height: 1.6; margin: 25px 0; text-align: center;">
                    ¡Excelente trabajo! Has completado el pago total de tu préstamo. 
                    Esto demuestra tu compromiso y responsabilidad financiera. 🎉
                </p>
                
                <div class="folio-box">
                    FOLIO DE LIQUIDACIÓN: {folio}
                </div>
                
                <div class="summary-box">
                    <h3 style="margin: 0 0 20px 0; color: #1e293b;">Resumen Final</h3>
                    
                    <div class="summary-row">
                        <span class="summary-label">Monto Original del Préstamo</span>
                        <span class="summary-value">${monto_original:,.2f}</span>
                    </div>
                    
                    <div class="summary-row">
                        <span class="summary-label">Descuento por Liquidación (3%)</span>
                        <span class="summary-value" style="color: #059669;">-${descuento:,.2f}</span>
                    </div>
                    
                    <div class="summary-row">
                        <span class="summary-label">Total Pagado</span>
                        <span class="highlight-value">${total_pagado:,.2f}</span>
                    </div>
                </div>
                
                <div class="benefits-box">
                    <p class="benefits-text">
                        <strong>💡 Beneficios de haber liquidado:</strong><br>
                        ✓ Ya puedes solicitar un nuevo préstamo cuando lo necesites<br>
                        ✓ Tu historial crediticio ha mejorado<br>
                        ✓ Ahorraste ${descuento:,.2f} en intereses<br>
                        ✓ Tienes capacidad de crédito disponible
                    </p>
                </div>
                
                <p style="color: #64748b; font-size: 14px; line-height: 1.6; margin-top: 25px; text-align: center;">
                    Gracias por tu confianza. Estamos aquí para apoyarte cuando lo necesites nuevamente.
                </p>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} Monte de Piedad | Comprobante de Liquidación</p>
                <p style="margin-top: 5px;">Este es un correo automático, no respondas a esta dirección.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    asunto = "🎊 ¡Felicidades! Préstamo Liquidado - Monte de Piedad"
    return enviar_email(destinatario, asunto, html)


# ==================== NOTIFICACIONES DESKTOP ====================

def notificar_desktop(titulo, mensaje, duracion=5, icono_path=None):
    """
    Muestra notificación nativa de Windows 10/11
    """
    if not TOAST_DISPONIBLE:
        print(f"📢 [DESKTOP] {titulo}: {mensaje}")
        return False
    
    try:
        toaster = ToastNotifier()
        toaster.show_toast(
            titulo,
            mensaje,
            icon_path=icono_path if icono_path else None,
            duration=duracion,
            threaded=True
        )
        return True
    except Exception as e:
        print(f"❌ Error en notificación Desktop: {e}")
        return False


def notif_pago_registrado(folio, monto):
    """Notificación cuando se registra un pago"""
    return notificar_desktop(
        "💰 Pago Registrado",
        f"Folio: {folio}\nMonto: ${monto:,.2f}",
        duracion=7,
        icono_path="monte.ico"
    )


def notif_prestamo_aprobado(cliente, monto):
    """Notificación cuando se aprueba un préstamo"""
    return notificar_desktop(
        "✅ Préstamo Aprobado",
        f"Cliente: {cliente}\nMonto: ${monto:,.2f}",
        duracion=7,
        icono_path="monte.ico"
    )


def notif_vencimiento_proximo(cliente, dias):
    """Notificación de vencimiento próximo"""
    return notificar_desktop(
        "⚠️ Vencimiento Próximo",
        f"Cliente: {cliente}\nVence en {dias} días",
        duracion=10,
        icono_path="monte.ico"
    )


def notif_corte_caja(total_tickets, total_monto):
    """Notificación al hacer corte de caja"""
    return notificar_desktop(
        "📊 Corte de Caja",
        f"Total tickets: {total_tickets}\nTotal: ${total_monto:,.2f}",
        duracion=7,
        icono_path="monte.ico"
    )


# ==================== TESTING ====================

if __name__ == "__main__":
    print("=== SISTEMA DE NOTIFICACIONES COMPLETO ===\n")
    print("8 tipos de emails disponibles:")
    print("1. Código de recuperación")
    print("2. Bienvenida")
    print("3. Ticket de pago")
    print("4. Préstamo aprobado")
    print("5. Préstamo rechazado")
    print("6. Recordatorio de pago")
    print("7. Pago vencido")
    print("8. Préstamo liquidado")
    print("\n4 tipos de notificaciones desktop")
    print("\n✅ Sistema listo para usar")
