# ==========================================
# MODELOS DE BASE DE DATOS (ORM)
# ==========================================
# Define las tablas de la base de datos usando SQLAlchemy
# Cada clase representa una tabla y sus columnas

from db import db
from datetime import datetime

# ===== MODELO GRADO =====
# Tabla: grados
# Descripción: Niveles educativos (1º Primaria, 2º Primaria, Inicial 3, etc.)
class Grado(db.Model):
    __tablename__ = 'grados'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único del grado
    nombre = db.Column(db.String(50), nullable=False)      # Nombre: "1º Primaria"
    descripcion = db.Column(db.String(200))                # Descripción opcional
    nivel = db.Column(db.Enum('inicial', 'primaria'), nullable=False)  # Nivel: inicial o primaria
    activo = db.Column(db.Boolean, default=True)           # Si está activo en el sistema
    
    # Relaciones: un grado tiene muchas secciones, usuarios y cursos
    secciones = db.relationship('Seccion', backref='grado', lazy=True, cascade='all, delete-orphan')
    usuarios = db.relationship('Usuario', backref='grado_rel', lazy=True)
    cursos = db.relationship('Curso', backref='grado_rel', lazy=True)
    
    def __repr__(self):
        return f"<Grado {self.nombre}>"

# ===== MODELO SECCION =====
# Tabla: secciones
# Descripción: Divisiones de un grado (A, B, C). Cada sección tiene un docente tutor.
class Seccion(db.Model):
    __tablename__ = 'secciones'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único de la sección
    nombre = db.Column(db.String(50), nullable=False)      # Nombre: "A", "B"
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)  # FK a Grado
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # FK a Usuario (tutor)
    capacidad = db.Column(db.Integer, default=30)          # Cupo máximo de estudiantes
    activo = db.Column(db.Boolean, default=True)           # Si está activa
    
    # Relaciones
    docente = db.relationship('Usuario', backref='secciones_docente', lazy=True, foreign_keys=[docente_id])
    usuarios = db.relationship('Usuario', backref='seccion_rel', lazy=True, foreign_keys='Usuario.seccion_id')
    cursos = db.relationship('Curso', backref='seccion_rel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Seccion {self.nombre} - Grado {self.grado.nombre}>"

# ===== MODELO CURSO =====
# Tabla: cursos
# Descripción: Materias asignadas a un grado/sección y docente (Matemáticas, Comunicación, etc.)
class Curso(db.Model):
    __tablename__ = 'cursos'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único del curso
    nombre = db.Column(db.String(100), nullable=False)     # Nombre: "Matemáticas"
    codigo = db.Column(db.String(20), unique=True, nullable=False)  # Código único: "MAT101"
    descripcion = db.Column(db.Text)                       # Descripción opcional
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # FK a Usuario
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)      # FK a Grado
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'), nullable=False)  # FK a Sección
    activo = db.Column(db.Boolean, default=True)           # Si está activo
    
    # Relaciones
    docente = db.relationship('Usuario', backref='cursos_docente', lazy=True)
    inscripciones = db.relationship('Inscripcion', backref='curso', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Curso {self.nombre}>"

# ===== MODELO INSCRIPCION =====
# Tabla: inscripciones
# Descripción: Relación entre alumno y curso. Guarda calificaciones y asistencia.
class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único de inscripción
    alumno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # FK a Usuario
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)    # FK a Curso
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha de inscripción
    calificacion = db.Column(db.Numeric(5, 2))             # Nota del alumno (ej: 4.50)
    asistencia = db.Column(db.Integer, default=0)          # Cantidad de asistencia
    
    # Relaciones
    alumno = db.relationship('Usuario', backref='inscripciones', lazy=True, foreign_keys=[alumno_id])
    __table_args__ = (db.UniqueConstraint('alumno_id', 'curso_id', name='unique_inscripcion'),)
    
    def __repr__(self):
        return f"<Inscripcion {self.alumno.nombres} - {self.curso.nombre}>"

# ===== MODELO USUARIO =====
# Tabla: usuarios
# Descripción: Personas del sistema: директор (directora), docente, alumno.
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único del usuario
    dni = db.Column(db.String(20), unique=True, nullable=False)  # DNI único
    nombres = db.Column(db.String(100), nullable=False)    # Nombres
    apellido_paterno = db.Column(db.String(80), nullable=False)  # Apellido paterno
    apellido_materno = db.Column(db.String(80), nullable=False)  # Apellido materno
    correo = db.Column(db.String(120), unique=True, nullable=False)  # Correo único
    telefono_principal = db.Column(db.String(20))           # Teléfono principal
    telefono_secundario = db.Column(db.String(20))          # Teléfono secundario
    clave = db.Column(db.String(255), nullable=False)       # Contraseña encriptada
    rol = db.Column(db.Enum('directora', 'docente', 'alumno'), nullable=False)  # Rol en el sistema
    profesion = db.Column(db.String(100))                   # Profesión (solo docentes)
    tiene_especialidad = db.Column(db.Boolean, default=False)  # Si tiene especialidad
    descripcion_especialidad = db.Column(db.Text)           # Descripción de especialidad
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'))  # FK a Grado (solo alumnos)
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'))  # FK a Sección
    activo = db.Column(db.Boolean, default=True)           # Si está activo
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha de registro
    
    def __repr__(self):
        return f"<Usuario {self.nombres} {self.apellido_paterno} ({self.rol})>"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

# ===== MODELO APODERADO =====
# Tabla: apoderados
# Descripción: Datos del padre/tutor de un alumno.
class Apoderado(db.Model):
    __tablename__ = 'apoderados'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único del apoderado
    alumno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # FK a Usuario (alumno)
    nombres = db.Column(db.String(100), nullable=False)    # Nombres del apoderado
    apellido_paterno = db.Column(db.String(80), nullable=False)  # Apellido paterno
    apellido_materno = db.Column(db.String(80), nullable=False)  # Apellido materno
    telefono_principal = db.Column(db.String(20))           # Teléfono principal
    telefono_secundario = db.Column(db.String(20))          # Teléfono secundario
    es_apoderado = db.Column(db.Boolean, default=True)     # Si es el apoderado principal
    activo = db.Column(db.Boolean, default=True)           # Si está activo
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha de registro
    
    # Relaciones
    alumno = db.relationship('Usuario', backref='apoderados', lazy=True)
    
    def __repr__(self):
        return f"<Apoderado {self.nombres} {self.apellido_paterno} - Alumno {self.alumno.nombre_completo}>"
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del apoderado"""
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

# ===== MODELO LOG ACCESO =====
# Tabla: logs_acceso
# Descripción: Historial de acciones de usuarios (auditoría).
class LogAcceso(db.Model):
    __tablename__ = 'logs_acceso'
    
    id = db.Column(db.Integer, primary_key=True)           # ID único del log
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)  # FK a Usuario
    accion = db.Column(db.String(255))                     # Descripción de la acción realizada
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)  # Fecha y hora de la acción
    
    # Relaciones
    usuario = db.relationship('Usuario', backref='logs', lazy=True)
    
    def __repr__(self):
        return f"<LogAcceso {self.usuario.nombres} - {self.accion}>"