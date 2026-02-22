# 🏛 Monte SIN Piedad - Sistema de Gestión de Préstamos

Sistema completo de gestión de préstamos con notificaciones por email, módulos Desktop (CustomTkinter), API REST (FastAPI) y sincronización en tiempo real.

---

## 🚀 INSTALACIÓN RÁPIDA

### Requisitos
- Python 3.8+
- MySQL 8.0+ (o Railway)
- Gmail (para notificaciones)

### Pasos

```bash
# 1. Clonar
git clone https://github.com/TU_USUARIO/PyMonte.git
cd PyMonte

# 2. Entorno virtual
python -m venv fastapi-env
.\fastapi-env\Scripts\activate  # Windows
# source fastapi-env/bin/activate  # Linux/Mac

# 3. Dependencias
pip install -r requirements.txt

# 4. Configurar email (OPCIONAL)
# Edita CONFIG_EMAIL.py con tu Gmail
# Ver: GUIA_CONFIGURAR_EMAILS.md

# 5. Ejecutar
uvicorn app_api:app --reload --port 8000  # API
python Lg_Monte.py                         # Desktop
```

---

## ✨ CARACTERÍSTICAS

### 📧 Notificaciones Email
- Bienvenida, Aprobación, Rechazo
- Tickets de pago, Recordatorios
- Alertas de mora, Liquidación

### 🖥️ Módulos Desktop
- Admin con dashboard y gráficos
- Empleado con cobranza
- Cliente con cartera
- Auto-refresh en tiempo real

### 🔗 API REST
- 16 endpoints completos
- Validaciones de negocio
- Sistema de mora automático
- Liquidación con descuento

---

## 📚 DOCUMENTACIÓN

- **Configurar Emails:** `GUIA_CONFIGURAR_EMAILS.md`
- **API:** http://localhost:8000/docs
- **Pruebas:** `python test_emails.py`

---

**✨ Sistema 100% funcional y listo para usar ✨**
