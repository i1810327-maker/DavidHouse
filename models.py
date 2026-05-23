from db import db
from datetime import datetime

# ===== NIVEL =====
class Nivel(db.Model):
    __tablename__ = 'niveles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    grados = db.relationship('Grado', backref='nivel_rel', lazy=True)

# ===== PERIODO ACADEMICO =====
class PeriodoAcademico(db.Model):
    __tablename__ = 'periodos_academicos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    bimestres = db.relationship('Bimestre', backref='periodo_rel', lazy=True, cascade='all, delete-orphan')

# ===== BIMESTRE =====
class Bimestre(db.Model):
    __tablename__ = 'bimestres'
    id = db.Column(db.Integer, primary_key=True)
    periodo_academico_id = db.Column(db.Integer, db.ForeignKey('periodos_academicos.id'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)

# ===== GRADO (existente + nivel_id) =====
class Grado(db.Model):
    __tablename__ = 'grados'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(200))
    nivel = db.Column(db.String(20))
    nivel_id = db.Column(db.Integer, db.ForeignKey('niveles.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    secciones = db.relationship('Seccion', backref='grado', lazy=True, cascade='all, delete-orphan')

# ===== SECCION (existente) =====
class Seccion(db.Model):
    __tablename__ = 'secciones'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'))
    capacidad = db.Column(db.Integer, default=30)
    activo = db.Column(db.Boolean, default=True)
    colaborador = db.relationship('Colaborador', backref='secciones_docente', lazy=True, foreign_keys=[docente_id])

# ===== COLABORADOR =====
class Colaborador(db.Model):
    __tablename__ = 'colaboradores'
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(80), nullable=False)
    apellido_materno = db.Column(db.String(80), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    clave = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('directora', 'docente'), nullable=False)
    telefono_principal = db.Column(db.String(20))
    telefono_secundario = db.Column(db.String(20))
    profesion = db.Column(db.String(100))
    tiene_especialidad = db.Column(db.Boolean, default=False)
    descripcion_especialidad = db.Column(db.Text)
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    seccion_rel = db.relationship('Seccion', lazy=True, foreign_keys=[seccion_id], uselist=False)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

    def obtener_niveles(self):
        niveles = set()
        for c in self.cursos_dictados:
            if c.grado_rel and c.grado_rel.nivel_rel:
                niveles.add(c.grado_rel.nivel_rel.nombre)
        return ','.join(niveles)

    def obtener_grados(self):
        grados = set()
        for c in self.cursos_dictados:
            if c.grado_rel:
                grados.add(str(c.grado_id))
        return ','.join(grados)

    def obtener_secciones(self):
        secciones = set()
        for c in self.cursos_dictados:
            if c.seccion_rel:
                secciones.add(str(c.seccion_id))
        return ','.join(secciones)

# ===== ESTUDIANTE =====
class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(80), nullable=False)
    apellido_materno = db.Column(db.String(80), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    clave = db.Column(db.String(255), nullable=False)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'))
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    grado_rel = db.relationship('Grado', backref='estudiantes', lazy=True, foreign_keys=[grado_id])
    seccion_rel = db.relationship('Seccion', backref='estudiantes', lazy=True, foreign_keys=[seccion_id])

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

# ===== APODERADO (existente) =====
class Apoderado(db.Model):
    __tablename__ = 'apoderados'
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellido_paterno = db.Column(db.String(80), nullable=False)
    apellido_materno = db.Column(db.String(80), nullable=False)
    telefono_principal = db.Column(db.String(20))
    telefono_secundario = db.Column(db.String(20))
    es_apoderado = db.Column(db.Boolean, default=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    alumno = db.relationship('Estudiante', backref='apoderados', lazy=True)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"

# ===== CURSO =====
class Curso(db.Model):
    __tablename__ = 'cursos_nuevos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    docente_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'), nullable=False)
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'), nullable=False)
    periodo_academico_id = db.Column(db.Integer, db.ForeignKey('periodos_academicos.id'), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    docente = db.relationship('Colaborador', backref='cursos_dictados', lazy=True)
    grado_rel = db.relationship('Grado', backref='cursos', lazy=True)
    seccion_rel = db.relationship('Seccion', backref='cursos', lazy=True)
    periodo = db.relationship('PeriodoAcademico', backref='cursos', lazy=True)

# ===== INSCRIPCION (existente) =====
class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'
    id = db.Column(db.Integer, primary_key=True)
    alumno_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos_nuevos.id'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    calificacion = db.Column(db.Numeric(5, 2))
    asistencia = db.Column(db.Integer, default=0)
    alumno = db.relationship('Estudiante', backref='inscripciones', lazy=True, foreign_keys=[alumno_id])
    curso = db.relationship('Curso', backref='inscripciones', lazy=True)
    __table_args__ = (db.UniqueConstraint('alumno_id', 'curso_id', name='unique_inscripcion'),)

# ===== HORARIO =====
class Horario(db.Model):
    __tablename__ = 'horarios'
    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos_nuevos.id'), nullable=False)
    seccion_id = db.Column(db.Integer, db.ForeignKey('secciones.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    bimestre_id = db.Column(db.Integer, db.ForeignKey('bimestres.id'))
    curso = db.relationship('Curso', backref='horarios', lazy=True)
    seccion = db.relationship('Seccion', backref='horarios', lazy=True)
    docente = db.relationship('Colaborador', backref='horarios', lazy=True)
    bimestre = db.relationship('Bimestre', backref='horarios', lazy=True)

# ===== EVALUACION =====
class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'
    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos_nuevos.id'), nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    bimestre_id = db.Column(db.Integer, db.ForeignKey('bimestres.id'), nullable=False)
    tipo = db.Column(db.Enum('cuaderno', 'libro', 'practicas', 'exposiciones', 'examen'), nullable=False)
    calificacion = db.Column(db.Numeric(4, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    observaciones = db.Column(db.Text)
    curso = db.relationship('Curso', backref='evaluaciones', lazy=True)
    estudiante = db.relationship('Estudiante', backref='evaluaciones', lazy=True)
    bimestre = db.relationship('Bimestre', backref='evaluaciones', lazy=True)

# ===== ASISTENCIA =====
class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos_nuevos.id'), nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    bimestre_id = db.Column(db.Integer, db.ForeignKey('bimestres.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    estado = db.Column(db.Enum('presente', 'tarde', 'falta', 'justificado'), nullable=False, default='presente')
    marcado_por = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    curso = db.relationship('Curso', backref='asistencias', lazy=True)
    estudiante = db.relationship('Estudiante', backref='asistencias', lazy=True)
    bimestre = db.relationship('Bimestre', backref='asistencias', lazy=True)
    marcador = db.relationship('Colaborador', backref='asistencias_marcadas', lazy=True)

# ===== JUSTIFICACION =====
class Justificacion(db.Model):
    __tablename__ = 'justificaciones'
    id = db.Column(db.Integer, primary_key=True)
    asistencia_id = db.Column(db.Integer, db.ForeignKey('asistencias.id'), nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    archivo_ruta = db.Column(db.String(500))
    estado = db.Column(db.Enum('pendiente', 'aprobado', 'rechazado'), default='pendiente')
    revisado_por = db.Column(db.Integer, db.ForeignKey('colaboradores.id'))
    comentario_revision = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_revision = db.Column(db.DateTime)
    asistencia = db.relationship('Asistencia', backref='justificacion', lazy=True, uselist=False)
    estudiante = db.relationship('Estudiante', backref='justificaciones', lazy=True)
    revisor = db.relationship('Colaborador', backref='justificaciones_revisadas', lazy=True)

# ===== COMENTARIO =====
class Comentario(db.Model):
    __tablename__ = 'comentarios'
    id = db.Column(db.Integer, primary_key=True)
    docente_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    tipo = db.Column(db.Enum('positivo', 'negativo', 'neutral', 'informativo'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    bimestre_id = db.Column(db.Integer, db.ForeignKey('bimestres.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    docente = db.relationship('Colaborador', backref='comentarios', lazy=True)
    estudiante = db.relationship('Estudiante', backref='comentarios', lazy=True)
    bimestre = db.relationship('Bimestre', backref='comentarios', lazy=True)

# ===== PAGO PLAN =====
class PagoPlan(db.Model):
    __tablename__ = 'pago_planes'
    id = db.Column(db.Integer, primary_key=True)
    periodo_academico_id = db.Column(db.Integer, db.ForeignKey('periodos_academicos.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    monto = db.Column(db.Numeric(8, 2), nullable=False)
    nivel_id = db.Column(db.Integer, db.ForeignKey('niveles.id'))
    grado_id = db.Column(db.Integer, db.ForeignKey('grados.id'))
    tipo = db.Column(db.Enum('matricula', 'mensualidad', 'otro'), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    periodo = db.relationship('PeriodoAcademico', backref='pago_planes', lazy=True)
    nivel = db.relationship('Nivel', backref='pago_planes', lazy=True)
    grado = db.relationship('Grado', backref='pago_planes', lazy=True)

# ===== PAGO REALIZADO =====
class PagoRealizado(db.Model):
    __tablename__ = 'pago_realizados'
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'), nullable=False)
    pago_plan_id = db.Column(db.Integer, db.ForeignKey('pago_planes.id'), nullable=False)
    monto_pagado = db.Column(db.Numeric(8, 2), nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.Enum('pagado', 'pendiente', 'atrasado'), default='pendiente')
    observaciones = db.Column(db.Text)
    estudiante = db.relationship('Estudiante', backref='pagos', lazy=True)
    plan = db.relationship('PagoPlan', backref='pagos_realizados', lazy=True)

# ===== CARPETA DOCENTE =====
class CarpetaDocente(db.Model):
    __tablename__ = 'carpetas_docentes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    bimestre_id = db.Column(db.Integer, db.ForeignKey('bimestres.id'))
    fecha_inicio_entrega = db.Column(db.DateTime, nullable=False)
    fecha_fin_entrega = db.Column(db.DateTime, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_por = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    bimestre = db.relationship('Bimestre', backref='carpetas', lazy=True)
    creador = db.relationship('Colaborador', backref='carpetas_creadas', lazy=True)

# ===== DOCUMENTO DOCENTE =====
class DocumentoDocente(db.Model):
    __tablename__ = 'documentos_docentes'
    id = db.Column(db.Integer, primary_key=True)
    carpeta_id = db.Column(db.Integer, db.ForeignKey('carpetas_docentes.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    archivo_nombre = db.Column(db.String(255), nullable=False)
    archivo_ruta = db.Column(db.String(500), nullable=False)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.Enum('pendiente', 'aprobado', 'rechazado'), default='pendiente')
    comentario_revision = db.Column(db.Text)
    fecha_revision = db.Column(db.DateTime)
    carpeta = db.relationship('CarpetaDocente', backref='documentos', lazy=True)
    docente = db.relationship('Colaborador', backref='documentos', lazy=True)

# ===== LOG ACCESO (existente, modificado) =====
class LogAcceso(db.Model):
    __tablename__ = 'logs_acceso'
    id = db.Column(db.Integer, primary_key=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'))
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiantes.id'))
    apoderado_id = db.Column(db.Integer)
    accion = db.Column(db.String(255))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)

# ===== INTENTO LOGIN =====
class IntentoLogin(db.Model):
    __tablename__ = 'intentos_login'
    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    tipo_usuario = db.Column(db.Enum('colaborador', 'estudiante', 'apoderado'))
    fecha_intento = db.Column(db.DateTime, default=datetime.utcnow)

# ===== BANEO =====
class Baneo(db.Model):
    __tablename__ = 'baneos'
    id = db.Column(db.Integer, primary_key=True)
    tipo_baneo = db.Column(db.Enum('usuario', 'ip'), nullable=False)
    identificador = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45))
    motivo = db.Column(db.String(255), default='Demasiados intentos fallidos')
    fecha_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    @property
    def esta_activo(self):
        return self.activo and self.fecha_fin > datetime.utcnow()
