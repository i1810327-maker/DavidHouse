import uuid
from db import db
from datetime import datetime

class MensajeContacto(db.Model):
    __tablename__ = 'mensajes_contacto'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    nombre_remitente = db.Column(db.String(100), nullable=False)
    correo_remitente = db.Column(db.String(254), nullable=False)
    telefono_remitente = db.Column(db.String(20))
    asunto = db.Column(db.String(150), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    estado_atencion = db.Column(db.String(20), default='Pendiente')
    notas_administrador = db.Column(db.Text)

class Colaborador(db.Model):
    __tablename__ = 'colaboradores'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    tipo_documento = db.Column(db.String(15), nullable=False)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(70), nullable=False)
    apellidos = db.Column(db.String(70), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(1), nullable=False)
    telefono_principal = db.Column(db.String(20), nullable=False)
    telefono_secundario = db.Column(db.String(20))
    direccion_fisica = db.Column(db.Text, nullable=False)
    tipo_direccion = db.Column(db.String(30), default='Casa')
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref='colaborador', uselist=False, lazy=True)
    estudiante = db.relationship('Estudiante', backref='colaborador', uselist=False, lazy=True)
    familiar = db.relationship('Familiar', backref='colaborador', uselist=False, lazy=True)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(30), unique=True, nullable=False)
    descripcion_rol = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    usuarios = db.relationship('UsuarioRol', backref='rol', lazy=True)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_colaborador = db.Column(db.Uuid, db.ForeignKey('colaboradores.id'), primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    estado_activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    roles = db.relationship('UsuarioRol', backref='usuario', lazy=True)
    logs = db.relationship('LogAcceso', backref='usuario', lazy=True)
    asignaciones = db.relationship('AsignacionDocente', backref='profesor', lazy=True)

class UsuarioRol(db.Model):
    __tablename__ = 'usuarios_roles'
    id_colaborador = db.Column(db.Uuid, db.ForeignKey('usuarios.id_colaborador'), primary_key=True)
    id_rol = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    fecha_asignacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class LogAcceso(db.Model):
    __tablename__ = 'logs_acceso'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_colaborador = db.Column(db.Uuid, db.ForeignKey('usuarios.id_colaborador'))
    nombre_usuario_intentado = db.Column(db.String(50))
    ip_direccion = db.Column(db.String(45), nullable=False)
    dispositivo = db.Column(db.Text)
    fecha_ingreso = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    exitoso = db.Column(db.Boolean, nullable=False)

class IntentoLogin(db.Model):
    __tablename__ = 'intentos_login'
    ip_direccion = db.Column(db.String(45), primary_key=True)
    intentos_fallidos = db.Column(db.Integer, default=1, nullable=False)
    ultima_falla = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Baneo(db.Model):
    __tablename__ = 'baneos'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    ip_direccion = db.Column(db.String(45), unique=True)
    id_colaborador = db.Column(db.Uuid, db.ForeignKey('usuarios.id_colaborador'))
    razon_baneo = db.Column(db.Text, nullable=False)
    fecha_baneo = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime(timezone=True))

class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    id_colaborador = db.Column(db.Uuid, db.ForeignKey('colaboradores.id'), primary_key=True)
    codigo_estudiante = db.Column(db.String(20), unique=True, nullable=False)
    historial_medico = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    familiares = db.relationship('EstudianteFamiliar', backref='estudiante', lazy=True)
    matriculas = db.relationship('Matricula', backref='estudiante', lazy=True)

class Familiar(db.Model):
    __tablename__ = 'familiares'
    id_colaborador = db.Column(db.Uuid, db.ForeignKey('colaboradores.id'), primary_key=True)
    ocupacion_laboral = db.Column(db.String(100))
    telefono_emergencia = db.Column(db.String(20), nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    estudiantes = db.relationship('EstudianteFamiliar', backref='familiar', lazy=True)
    justificaciones = db.relationship('Justificacion', backref='familiar', lazy=True)

class EstudianteFamiliar(db.Model):
    __tablename__ = 'estudiante_familiares'
    id_estudiante = db.Column(db.Uuid, db.ForeignKey('estudiantes.id_colaborador'), primary_key=True)
    id_familiar = db.Column(db.Uuid, db.ForeignKey('familiares.id_colaborador'), primary_key=True)
    parentesco = db.Column(db.String(30), nullable=False)
    es_apoderado_legal = db.Column(db.Boolean, default=False, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class PeriodoAcademico(db.Model):
    __tablename__ = 'periodos_academicos'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    nombre_periodo = db.Column(db.String(50), unique=True, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    estado_activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    aulas = db.relationship('AulaAsignada', backref='periodo', lazy=True)
    matriculas = db.relationship('Matricula', backref='periodo', lazy=True)

class Nivel(db.Model):
    __tablename__ = 'niveles'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    nombre_nivel = db.Column(db.String(30), unique=True, nullable=False)
    descripcion_nivel = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    grados = db.relationship('Grado', backref='nivel', lazy=True)

class Grado(db.Model):
    __tablename__ = 'grados'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_nivel = db.Column(db.Uuid, db.ForeignKey('niveles.id'), nullable=False)
    nombre_grado = db.Column(db.String(50), nullable=False)
    descripcion_grado = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    secciones = db.relationship('Seccion', backref='grado', lazy=True)

class Seccion(db.Model):
    __tablename__ = 'secciones'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_grado = db.Column(db.Uuid, db.ForeignKey('grados.id'), nullable=False)
    nombre_seccion = db.Column(db.String(10), nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    aulas = db.relationship('AulaAsignada', backref='seccion', lazy=True)

class Curso(db.Model):
    __tablename__ = 'cursos'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    nombre_curso = db.Column(db.String(100), unique=True, nullable=False)
    descripcion_curso = db.Column(db.Text)
    estado_curso = db.Column(db.String(20), default='Activo')
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    asignaciones = db.relationship('AsignacionDocente', backref='curso', lazy=True)

class AulaAsignada(db.Model):
    __tablename__ = 'aulas_asignadas'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_periodo_academico = db.Column(db.Uuid, db.ForeignKey('periodos_academicos.id'), nullable=False)
    id_seccion = db.Column(db.Uuid, db.ForeignKey('secciones.id'), nullable=False)
    capacidad_maxima = db.Column(db.Integer, default=30, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    inscripciones = db.relationship('Inscripcion', backref='aula', lazy=True)
    asignaciones = db.relationship('AsignacionDocente', backref='aula', lazy=True)
    planes_pago = db.relationship('PagoPlan', backref='aula', lazy=True)

class Matricula(db.Model):
    __tablename__ = 'matriculas'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_estudiante = db.Column(db.Uuid, db.ForeignKey('estudiantes.id_colaborador'), nullable=False)
    id_periodo_academico = db.Column(db.Uuid, db.ForeignKey('periodos_academicos.id'), nullable=False)
    fecha_matricula = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    estado_matricula = db.Column(db.String(20), default='Activo')
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    inscripciones = db.relationship('Inscripcion', backref='matricula', lazy=True)
    pagos = db.relationship('Pago', backref='matricula', lazy=True)

class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_matricula = db.Column(db.Uuid, db.ForeignKey('matriculas.id'), nullable=False)
    id_aula_asignada = db.Column(db.Uuid, db.ForeignKey('aulas_asignadas.id'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    estado_inscripcion = db.Column(db.String(20), default='Asignado')
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    asistencias = db.relationship('Asistencia', backref='inscripcion', lazy=True)
    calificaciones = db.relationship('Calificacion', backref='inscripcion', lazy=True)
    seguimientos = db.relationship('SeguimientoEstudiante', backref='inscripcion', lazy=True)

class AsignacionDocente(db.Model):
    __tablename__ = 'asignaciones_docentes'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_profesor = db.Column(db.Uuid, db.ForeignKey('usuarios.id_colaborador'), nullable=False)
    id_curso = db.Column(db.Uuid, db.ForeignKey('cursos.id'), nullable=False)
    id_aula_asignada = db.Column(db.Uuid, db.ForeignKey('aulas_asignadas.id'), nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    evaluaciones = db.relationship('Evaluacion', backref='asignacion', lazy=True)
    carpeta = db.relationship('CarpetaDocente', backref='asignacion', uselist=False, lazy=True)

class Asistencia(db.Model):
    __tablename__ = 'asistencias'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_inscripcion = db.Column(db.Uuid, db.ForeignKey('inscripciones.id'), nullable=False)
    fecha_asistencia = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    estado_asistencia = db.Column(db.String(1), nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    justificacion = db.relationship('Justificacion', backref='asistencia', uselist=False, lazy=True)

class Justificacion(db.Model):
    __tablename__ = 'justificaciones'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_asistencia = db.Column(db.Uuid, db.ForeignKey('asistencias.id'), unique=True, nullable=False)
    id_familiar = db.Column(db.Uuid, db.ForeignKey('familiares.id_colaborador'), nullable=False)
    motivo_justificacion = db.Column(db.Text, nullable=False)
    evidencia_archivo_url = db.Column(db.String(255))
    fecha_presentacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_asignacion_docente = db.Column(db.Uuid, db.ForeignKey('asignaciones_docentes.id'), nullable=False)
    nombre_evaluacion = db.Column(db.String(100), nullable=False)
    bimestre_bloque = db.Column(db.Integer, nullable=False)
    porcentaje_peso = db.Column(db.Numeric(5, 2), nullable=False)
    fecha_limite = db.Column(db.Date, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    calificaciones = db.relationship('Calificacion', backref='evaluacion', lazy=True)

class Calificacion(db.Model):
    __tablename__ = 'calificaciones'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_inscripcion = db.Column(db.Uuid, db.ForeignKey('inscripciones.id'), nullable=False)
    id_evaluacion = db.Column(db.Uuid, db.ForeignKey('evaluaciones.id'), nullable=False)
    nota = db.Column(db.Numeric(4, 2), nullable=False)
    comentarios = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class SeguimientoEstudiante(db.Model):
    __tablename__ = 'seguimientos_estudiantes'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_inscripcion = db.Column(db.Uuid, db.ForeignKey('inscripciones.id'), nullable=False)
    id_colaborador_registra = db.Column(db.Uuid, db.ForeignKey('usuarios.id_colaborador'), nullable=False)
    tipo_registro = db.Column(db.String(30), nullable=False)
    gravedad = db.Column(db.String(15), default='Informativo')
    descripcion = db.Column(db.Text, nullable=False)
    fecha_suceso = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    registrador = db.relationship('Usuario', backref='seguimientos', lazy=True)

class CarpetaDocente(db.Model):
    __tablename__ = 'carpetas_docentes'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_asignacion_docente = db.Column(db.Uuid, db.ForeignKey('asignaciones_docentes.id'), unique=True, nullable=False)
    nombre_carpeta = db.Column(db.String(100), nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    documentos = db.relationship('DocumentoDocente', backref='carpeta', lazy=True)

class DocumentoDocente(db.Model):
    __tablename__ = 'documentos_docentes'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_carpeta = db.Column(db.Uuid, db.ForeignKey('carpetas_docentes.id'), nullable=False)
    nombre_archivo = db.Column(db.String(150), nullable=False)
    archivo_url = db.Column(db.String(255), nullable=False)
    fecha_subida = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class PagoPlan(db.Model):
    __tablename__ = 'pago_planes'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_aula_asignada = db.Column(db.Uuid, db.ForeignKey('aulas_asignadas.id'), nullable=False)
    concepto_pago = db.Column(db.String(100), nullable=False)
    monto_base = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    pagos = db.relationship('Pago', backref='plan', lazy=True)

class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Uuid, primary_key=True, default=uuid.uuid4)
    id_matricula = db.Column(db.Uuid, db.ForeignKey('matriculas.id'), nullable=False)
    id_pago_plan = db.Column(db.Uuid, db.ForeignKey('pago_planes.id'), nullable=False)
    monto_pagado = db.Column(db.Numeric(10, 2), nullable=False)
    monto_mora = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    fecha_transaccion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    metodo_pago = db.Column(db.String(30), nullable=False)
    comprobante_numero = db.Column(db.String(50), unique=True, nullable=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
