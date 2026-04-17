from db import db
from datetime import datetime

# ===== MODELO GRADO =====
class Grado(db.Model):
    __tablename__ = 'grados'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200))
    nivel = db.Column(db.Enum('inicial', 'primaria'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    secciones = db.relationship('Seccion', backref='grado', lazy=True, cascade='all, delete-orphan')
    usuarios = db.relationship('Usuario', backref='grado_rel', lazy=True)
    cursos = db.relationship('Curso', backref='grado_rel', lazy=True)
    
    def __repr__(self):
        return f"<Grado {self.nombre}>"

# ===== MODELO SECCION =====
class Seccion(db.Model):
    __tablename__ = 'secciones'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    capacidad = db.Column(db.Integer, default=30)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    docente = db.relationship('Usuario', backref='secciones_docente', lazy=True, foreign_keys=[docente_id])
    usuarios = db.relationship('Usuario', backref='seccion_rel', lazy=True, foreign_keys='Usuario.seccion_id')
    cursos = db.relationship('Curso', backref='seccion_rel', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Seccion {self.nombre} - Grado {self.grado.nombre}>"

# ===== MODELO CURSO =====
class Curso(db.Model):
    __tablename__ = 'cursos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    docente = db.relationship('Usuario', backref='cursos_docente', lazy=True)
    inscripciones = db.relationship('Inscripcion', backref='curso', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Curso {self.nombre}>"

# ===== MODELO INSCRIPCION =====
class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'
    
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    calificacion = db.Column(db.Numeric(5, 2))
    asistencias = db.Column(db.Integer, default=0)
    
    # Relaciones
    alumno = db.relationship('Usuario', backref='inscripciones', lazy=True, foreign_keys=[alumno_id])
    __table_args__ = (db.UniqueConstraint('alumno_id', 'curso_id', name='unique_inscripcion'),)
    
    def __repr__(self):
        return f"<Inscripcion {self.alumno.nombres} - {self.curso.nombre}>"

# ===== MODELO USUARIO =====
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(80), nullable=False)
    apellido_materno = db.Column(db.String(80), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    clave = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('directora', 'docente', 'alumno'), nullable=False)
    profesion = db.Column(db.String(100))
    tiene_especialidad = db.Column(db.Boolean, default=False)
    descripcion_especialidad = db.Column(db.Text)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'))
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Usuario {self.nombres} {self.apellido_paterno} ({self.rol})>"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

# ===== MODELO LOG ACCESO =====
class LogAcceso(db.Model):
    __tablename__ = 'logs_acceso'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    accion = db.Column(db.String(255))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref='logs', lazy=True)
    
    def __repr__(self):
        return f"<LogAcceso {self.usuario.nombres} - {self.accion}>"