# ==================== CONFIG_EMAIL.py ====================
# Archivo de configuración de emails
# Los usuarios deben editar este archivo con sus propias credenciales

"""
📧 INSTRUCCIONES PARA CONFIGURAR EMAILS:

1. Ve a tu cuenta de Gmail: https://myaccount.google.com/security
2. Activa la "Verificación en 2 pasos"
3. Ve a: https://myaccount.google.com/apppasswords
4. Crea una "Contraseña de aplicación" para "Correo"
5. Copia los 16 caracteres (con espacios)
6. Pega abajo en GMAIL_APP_PASSWORD

⚠️  IMPORTANTE: 
- NO uses tu contraseña normal de Gmail
- Usa la "Contraseña de aplicación" de 16 caracteres
- Ver guía completa en: GUIA_CONFIGURAR_EMAILS.md
"""

# ==================== CONFIGURACIÓN ====================

# Email desde el cual se enviarán las notificaciones
GMAIL_USER = "tu_email@gmail.com"  # ← CAMBIAR POR TU EMAIL

# Contraseña de aplicación (16 caracteres generada en Gmail)
# NO es tu contraseña normal de Gmail
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # ← CAMBIAR POR TU APP PASSWORD

# Servidor SMTP de Gmail (NO cambiar)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Nombre del remitente
SENDER_NAME = "Monte de Piedad"

# ==================== FIN DE CONFIGURACIÓN ====================

# Validación automática
if GMAIL_USER == "tu_email@gmail.com":
    print("⚠️  ADVERTENCIA: Debes configurar CONFIG_EMAIL.py")
    print("    1. Abre CONFIG_EMAIL.py")
    print("    2. Cambia GMAIL_USER por tu email")
    print("    3. Cambia GMAIL_APP_PASSWORD por tu app password")
    print("    4. Ver guía: GUIA_CONFIGURAR_EMAILS.md")
    EMAIL_CONFIGURED = False
else:
    EMAIL_CONFIGURED = True
    print(f"✅ Email configurado: {GMAIL_USER}")
