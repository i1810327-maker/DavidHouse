# 🚀 GUÍA DE INSTALACIÓN Y EJECUCIÓN - ColegioSys

## 📋 Paso 1: Preparar MySQL (phpMyAdmin)

### Crear la Base de Datos:
1. Accede a **phpMyAdmin**: http://localhost/phpmyadmin
2. Haz clic en **Nueva** (o New Database)
3. Nombre de BD: `colegio_sys`
4. Haz clic en **Crear** (Create)

Si lo prefieres, ejecuta directamente en phpMyAdmin:
```sql
CREATE DATABASE IF NOT EXISTS colegio_sys;
```

**✅ Listo.** La BD está creada (aún vacía).

---

## 🛠️ Paso 2: Instalar Dependencias Python

En **PowerShell** (Windows):

```bash
# Navega a la carpeta del proyecto
cd C:\Users\imano\OneDrive\Desktop\colegio_sys

# Activa el entorno virtual
.\venv\Scripts\Activate.ps1

# Instala las dependencias
pip install -r requirements.txt
```

**Esperado:**
```
Successfully installed flask flask-sqlalchemy flask-bcrypt mysql-connector-python...
```

---

## 🗄️ Paso 3: Inicializar la Base de Datos

Con el entorno virtual activado:

```bash
python init_db.py
```

**Esperado:**
```
🔧 Creando tablas...
✅ Tables created correctly

📖 Creating grades...
✅ Grados created

📚 Creating sections...
✅ Secciones created

👩‍💼 Creating user Director...
✅ Directora created
   📧 Correo: admin@colegio.edu.pe
   🔑 Contraseña: Admin2026

👨‍🏫 Creating user Teacher...
✅ Docente created
   📧 Correo: docente@colegio.edu.pe
   🔑 Contraseña: Docente2026

👨‍🎓 Creating user Student...
✅ Alumno created
   📧 Correo: alumno@colegio.edu.pe
   🔑 Contraseña: Alumno2026

🎉 ¡Base de datos inicializada correctamente!
```

**✅ Listo.** Las tablas y datos de prueba están creados.

---

## ▶️ Paso 4: Ejecutar la Aplicación

```bash
python app.py
```

**Esperado:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

## 🌐 Paso 5: Acceder a la Aplicación

1. Abre tu navegador
2. Ve a: **http://localhost:5000**
3. Deberías ver la página de **Login**

---

## 🔑 Credenciales de Prueba

### 1️⃣ Directora (Administrador)
- **Correo:** admin@colegio.edu.pe
- **Contraseña:** Admin2026
- **Funciones:** Registrar alumnos, docentes, crear cursos, etc.

### 2️⃣ Docente
- **Correo:** docente@colegio.edu.pe
- **Contraseña:** Docente2026
- **Funciones:** Ver cursos, alumnos, cambiar contraseña

### 3️⃣ Alumno
- **Correo:** alumno@colegio.edu.pe
- **Contraseña:** Alumno2026
- **Funciones:** Ver cursos, calificaciones, cambiar contraseña

---

## 📝 Pruebas Recomendadas

### ✅ Como Directora:
1. Inicia sesión en dashboard
2. Ve a "Registrar Alumno"
3. Completa el formulario y registra uno nuevo
4. Ve a "Registrar Docente"
5. Completa el formulario y registra uno nuevo

### ✅ Como Docente:
1. Inicia sesión
2. Ve a "Dashboard"
3. Verás los cursos asignados
4. Ve a "Cambiar Contraseña"
5. Cambia tu contraseña

### ✅ Como Alumno:
1. Inicia sesión
2. Ve a "Dashboard"
3. Verás tus cursos inscritos y calificaciones
4. Ve a "Cambiar Contraseña"
5. Cambia tu contraseña

---

## ⚠️ Solución de Problemas

### Error: "No module named 'flask'"
**Solución:**
```bash
# Asegúrate de tener el entorno virtual ACTIVADO
.\venv\Scripts\Activate.ps1
pip install flask flask-sqlalchemy flask-bcrypt mysql-connector-python
```

### Error: "Can't connect to MySQL server"
**Solución:**
1. Verifica que MySQL está corriendo:
   - En Windows: Busca "Services" → "MySQL80" → Inicia si no está
2. Asegúrate de que la BD `colegio_sys` existe en phpMyAdmin

### Error: "Port 5000 already in use"
**Solución:**
```bash
# Cambia el puerto en app.py (última línea)
# De: app.run(debug=True)
# A: app.run(debug=True, port=5001)
```

### Error: "Table 'colegio_sys.usuarios' doesn't exist"
**Solución:**
```bash
# Ejecuta el script de inicialización
python init_db.py
```

---

## 📁 Estructura de Archivos

```
colegio_sys/
├── app.py                    # Aplicación principal
├── db.py                     # Configuración BD
├── models.py                 # Modelos (Usuario, Grado, etc)
├── init_db.py               # Script inicializar BD
├── requirements.txt         # Dependencias Python
├── .env.example             # Configuración de ejemplo
├── README.md                # Documentación completa
├── SETUP.md                 # Este archivo
├── static/
│   └── css/
│       └── styles.css       # Estilos CSS
├── templates/
│   ├── login.html
│   ├── base.html
│   ├── dashboard_directora.html
│   ├── dashboard_docente.html
│   ├── dashboard_alumno.html
│   ├── usuarios_form.html
│   ├── docentes_form.html
│   ├── cambiar_clave.html
│   └── error.html
└── venv/                    # Entorno virtual

---

## 🔒 Seguridad

- ✅ Contraseñas encriptadas con bcrypt
- ✅ Control de acceso por roles (RBAC)
- ✅ Sesiones seguras
- ✅ Validación de formularios
- ✅ Logout disponible

---

⚠️ **IMPORTANTE:** En producción:
1. Cambiar `app.secret_key` a una clave aleatoria
2. Poner `debug=False` en `app.run()`
3. Usar HTTPS
4. Cambiar contraseñas de usuarios de prueba

---

## 📞 Soporte

¿Preguntas? Contacta a: admin@colegio.edu.pe

---

© 2026 **ColegioSys** - Sistema de Gestión Educativa
