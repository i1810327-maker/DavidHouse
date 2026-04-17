# 🎓 ColegioSys - Sistema de Gestión Escolar

**Sistema integral de gestión educativa con control de acceso basado en roles (RBAC)**

---

## 📊 Estructura de Base de Datos (MySQL)

### Script SQL para crear la BD

```sql
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS colegio_sys;
USE colegio_sys;

-- Tabla de Grados
CREATE TABLE grados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200),
    nivel ENUM('inicial', 'primaria') NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla de Usuarios
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(20) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(80) NOT NULL,
    apellido_materno VARCHAR(80) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    rol ENUM('directora', 'docente', 'alumno') NOT NULL,
    profesion VARCHAR(100),
    tiene_especialidad BOOLEAN DEFAULT FALSE,
    descripcion_especialidad TEXT,
    grado_id INT,
    seccion_id INT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (grado_id) REFERENCES grados(id)
);

-- Tabla de Secciones
CREATE TABLE secciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    grado_id INT NOT NULL,
    docente_id INT,
    capacidad INT DEFAULT 30,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (grado_id) REFERENCES grados(id),
    FOREIGN KEY (docente_id) REFERENCES usuarios(id)
);

-- Agregar foreign key de usuarios a secciones después de crear secciones
ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_seccion FOREIGN KEY (seccion_id) REFERENCES secciones(id);

-- Tabla de Cursos
CREATE TABLE cursos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    descripcion TEXT,
    docente_id INT NOT NULL,
    grado_id INT NOT NULL,
    seccion_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (docente_id) REFERENCES usuarios(id),
    FOREIGN KEY (grado_id) REFERENCES grados(id),
    FOREIGN KEY (seccion_id) REFERENCES secciones(id)
);

-- Tabla de Inscripciones (Alumnos en Cursos)
CREATE TABLE inscripciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alumno_id INT NOT NULL,
    curso_id INT NOT NULL,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    calificacion DECIMAL(5,2),
    asistencias INT DEFAULT 0,
    UNIQUE KEY unique_inscripcion (alumno_id, curso_id),
    FOREIGN KEY (alumno_id) REFERENCES usuarios(id),
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

-- Tabla de Logs (Auditoría)
CREATE TABLE logs_acceso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    accion VARCHAR(255),
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

---

## 🚀 Instalación Rápida

### 1. Crear la BD en phpMyAdmin
```sql
-- Copia y ejecuta el script SQL anterior en phpMyAdmin
```

### 2. Instalar dependencias
```bash
cd C:\Users\imano\OneDrive\Desktop\colegio_sys
.\venv\Scripts\Activate.ps1
pip install flask flask-sqlalchemy flask-bcrypt mysql-connector-python
```

### 3. Ejecutar
```bash
python app.py
```

**Accede a**: http://localhost:5000

---

## 👥 Roles y Funcionalidades

### 👩‍💼 **DIRECTORA**
- ✅ Panel de administración
- ✅ Registrar alumnos (DNI, Nombres, Apellidos, Correo, Clave, Sección, Grado)
- ✅ Registrar docentes (DNI, Nombres, Apellidos, Correo, Clave, Profesión, ±Especialidad)
- ✅ Ver listado de usuarios
- ✅ Crear grados y secciones
- ✅ Crear cursos
- ✅ Cambiar contraseña

### 👨‍🏫 **DOCENTE**
- ✅ Ver cursos asignados
- ✅ Ver sección y grado
- ✅ Ver lista de alumnos
- ✅ Calificar alumnos
- ✅ Cambiar contraseña

### 👨‍🎓 **ALUMNO**
- ✅ Ver mis cursos
- ✅ Ver calificaciones
- ✅ Ver sección y grado
- ✅ Cambiar contraseña

---

## 📁 Estructura del Proyecto

```
colegio_sys/
├── app.py              # Aplicación principal (decoradores)
├── db.py               # Configuración BD
├── models.py           # Modelos (Usuario, Grado, Sección, Curso)
├── static/
│   └── css/
│       └── styles.css  # Estilos (Azul David House)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard_directora.html
│   ├── dashboard_docente.html
│   ├── dashboard_alumno.html
│   ├── usuarios_form.html
│   ├── docentes_form.html
│   └── cambiar_clave.html
├── README.md           # Este archivo
└── venv/               # Entorno virtual
```

---

## 🔐 Seguridad

✅ Contraseñas encriptadas con **bcrypt**
✅ Control de acceso basado en roles
✅ Sesiones seguras
✅ Validación de formularios

---

© 2026 **ColegioSys** - Todos los derechos reservados.
