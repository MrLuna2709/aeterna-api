# 📧 GUÍA DE CONFIGURACIÓN - SISTEMA DE NOTIFICACIONES POR EMAIL

## Para usuarios que instalen Monte SIN Piedad en su PC

---

## ⚠️ IMPORTANTE

Para que el sistema de notificaciones funcione, necesitas configurar TU PROPIO email de Gmail.

**NO uses las credenciales que vienen por defecto** - no funcionarán.

---

## 📋 REQUISITOS

- ✅ Cuenta de Gmail
- ✅ Verificación en 2 pasos activada
- ✅ 10 minutos de tu tiempo

---

## 🚀 PASOS PARA CONFIGURAR

### PASO 1: Activar Verificación en 2 Pasos

1. Ve a: https://myaccount.google.com/security
2. Busca "Verificación en 2 pasos"
3. Click en "Comenzar" y sigue los pasos
4. Confirma con tu teléfono

✅ **Ya tienes 2FA activado**

---

### PASO 2: Generar Contraseña de Aplicación

1. Ve a: https://myaccount.google.com/apppasswords
2. Inicia sesión con tu cuenta de Gmail
3. En "Seleccionar app" → Elige **"Correo"**
4. En "Seleccionar dispositivo" → Elige **"Otro (nombre personalizado)"**
5. Escribe: **"Monte de Piedad"**
6. Click **"Generar"**

Google te mostrará una contraseña de 16 caracteres:
```
abcd efgh ijkl mnop
```

✅ **Copia esta contraseña** (la necesitarás en el siguiente paso)

---

### PASO 3: Configurar CONFIG_EMAIL.py

1. Abre la carpeta del proyecto:
```
C:\SpaceWork\Code\PyMonte\
```

2. Abre el archivo: **`CONFIG_EMAIL.py`**

3. **Edita estas líneas:**

**ANTES:**
```python
GMAIL_USER = "tu_email@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
```

**DESPUÉS:**
```python
GMAIL_USER = "miemailreal@gmail.com"  # ← Tu email
GMAIL_APP_PASSWORD = "abcd efgh ijkl mnop"  # ← Tu contraseña de app
```

4. **Guarda el archivo** (Ctrl+S)

---

### PASO 4: Verificar que Funciona

Ejecuta el test de emails:

```powershell
cd C:\SpaceWork\Code\PyMonte
python test_emails.py
```

Sigue el menú y prueba enviar un email de prueba.

**Si llega el email** → ✅ Configuración correcta

**Si NO llega** → Revisa los pasos anteriores

---

## ❓ PREGUNTAS FRECUENTES

### ¿Por qué necesito una "Contraseña de Aplicación"?

Gmail requiere contraseñas especiales para aplicaciones que se conectan por SMTP. Tu contraseña normal NO funciona.

---

### ¿Es seguro?

Sí. La "Contraseña de Aplicación" solo permite enviar emails. No da acceso a:
- ❌ Leer tus emails
- ❌ Modificar tu cuenta
- ❌ Acceder a otros servicios de Google

Puedes revocarla en cualquier momento desde:
https://myaccount.google.com/apppasswords

---

### ¿Puedo usar otro email que no sea Gmail?

**NO recomendado**. El sistema está optimizado para Gmail SMTP.

Si DEBES usar otro:
- Outlook: `smtp.office365.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- Otros: Busca "SMTP settings" de tu proveedor

Pero tendrás que modificar `CONFIG_EMAIL.py` manualmente.

---

### ¿Qué pasa si no configuro el email?

La aplicación **funcionará normal**, pero:
- ✅ Préstamos se aprueban/rechazan
- ✅ Pagos se registran
- ❌ NO se envían emails a clientes

Los clientes NO recibirán notificaciones automáticas.

---

### Los emails llegan a SPAM

**Normal la primera vez.**

Solución:
1. Busca en la carpeta SPAM
2. Marca como "No es spam"
3. Los siguientes llegarán a Inbox

---

### Error: "Authentication failed"

**Verifica:**

1. ¿Copiaste la contraseña correctamente?
   - Debe tener 16 caracteres
   - Con espacios: `abcd efgh ijkl mnop`

2. ¿Activaste la verificación en 2 pasos?
   - Requerido para generar App Passwords

3. ¿Usaste tu contraseña normal en lugar de la App Password?
   - ❌ NO uses tu contraseña de Gmail normal
   - ✅ Usa la contraseña de 16 caracteres que generaste

---

## 🔒 SEGURIDAD

### ✅ HACER:
- Genera tu propia App Password
- Guarda CONFIG_EMAIL.py de forma segura
- Revoca App Passwords que ya no uses

### ❌ NO HACER:
- NO compartas tu CONFIG_EMAIL.py con nadie
- NO subas CONFIG_EMAIL.py a GitHub público
- NO uses la contraseña de ejemplo que viene por defecto

---

## 🎯 VERIFICACIÓN FINAL

Checklist para confirmar que todo está bien:

- [ ] Verificación en 2 pasos activada en Gmail
- [ ] App Password generada (16 caracteres)
- [ ] CONFIG_EMAIL.py editado con TU email
- [ ] CONFIG_EMAIL.py editado con TU app password
- [ ] test_emails.py ejecutado exitosamente
- [ ] Email de prueba recibido

**Si todo está ✅ = Sistema listo para usar** 🎉

---

## 💡 TIPS

### Para Desarrollo:
- Usa un email de prueba (no tu email personal)
- Crea una cuenta Gmail específica para el sistema

### Para Producción:
- Usa un email profesional: `noreply@tuempresa.com`
- Considera usar servicios como SendGrid o AWS SES para mayor volumen

---

## 📞 SOPORTE

Si tienes problemas:

1. Revisa esta guía completa
2. Verifica los logs en consola
3. Prueba con el script `test_emails.py`
4. Revisa que Gmail SMTP esté activo en tu red

---

**¡Listo! Ahora el sistema está configurado y funcionando.** 🎊
