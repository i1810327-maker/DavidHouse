from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import os
import re
from db import db, init_db
from models import (
    Nivel, PeriodoAcademico, Bimestre, Grado, Seccion,
    Colaborador, Estudiante, Apoderado,
    Curso, Inscripcion, Horario, Evaluacion, Asistencia,
    Justificacion, Comentario, PagoPlan, PagoRealizado,
    CarpetaDocente, DocumentoDocente, LogAcceso, IntentoLogin, Baneo,
    Evento, SolicitudReporte
)

import logging
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ====================== CONFIG ======================
app = Flask(__name__)
app.secret_key = "clave_super_segura_2026_ColegioSys"

MAX_INTENTOS_USUARIO = 3
TIEMPO_BANEO_MINUTOS = 5
VENTANA_TIEMPO_MINUTOS = 5
FECHA_PERMANENTE = datetime(2100, 1, 1)
PESOS_EVALUACION = {'cuaderno': 0.10, 'libro': 0.10, 'practicas': 0.20, 'exposiciones': 0.10, 'examen': 0.50}

init_db(app)
bcrypt = Bcrypt(app)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def extension_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validar_archivo(archivo):
    if not archivo or not archivo.filename:
        return False, 'No se seleccionó ningún archivo'
    if not extension_permitida(archivo.filename):
        return False, 'Tipo de archivo no permitido. Extensiones: pdf, doc, docx, xls, xlsx, jpg, png, gif, txt'
    archivo.seek(0, os.SEEK_END)
    size = archivo.tell()
    archivo.seek(0)
    if size > MAX_FILE_SIZE:
        return False, 'El archivo excede el tamaño máximo de 10MB'
    return True, None

# ====================== VALIDACIONES ======================
def validar_clave(clave, usuario=None):
    errores = []
    if len(clave) < 8: errores.append('Mínimo 8 caracteres')
    if len(clave) > 50: errores.append('Máximo 50 caracteres')
    if not re.search(r'[A-Z]', clave): errores.append('Debe incluir mayúsculas')
    if not re.search(r'[a-z]', clave): errores.append('Debe incluir minúsculas')
    if not re.search(r'\d', clave): errores.append('Debe incluir números')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=]', clave): errores.append('Debe incluir símbolos')
    if usuario:
        for campo in ['dni', 'nombres', 'apellido_paterno', 'apellido_materno']:
            val = getattr(usuario, campo, '')
            if val and val.lower() in clave.lower():
                errores.append(f'No debe contener {campo.replace("_", " ")}')
    return errores

def obtener_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def tiempo_actual():
    return datetime.utcnow()

# ====================== DECORADORES ======================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión primero', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('rol') not in roles:
                flash('No tienes permisos para acceder aquí', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def log_accion(accion):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            resultado = f(*args, **kwargs)
            try:
                log = LogAcceso(
                    colaborador_id=session.get('usuario_id') if session.get('tipo') == 'colaborador' else None,
                    estudiante_id=session.get('usuario_id') if session.get('tipo') == 'estudiante' else None,
                    accion=accion
                )
                db.session.add(log)
                db.session.commit()
            except:
                db.session.rollback()
            return resultado
        return decorated
    return decorator

# ====================== HELPERS (used by blueprints) =====
def obtener_bimestre_actual():
    hoy = datetime.now().date()
    return Bimestre.query.filter(
        Bimestre.fecha_inicio <= hoy,
        Bimestre.fecha_fin >= hoy
    ).first()

def _calcular_promedio_desde_datos(evals, asistencias, pesos=None):
    if not evals:
        return None, 0, 0
    if pesos is None:
        pesos = {'cuaderno': 0.10, 'libro': 0.10, 'practicas': 0.20, 'exposiciones': 0.10, 'examen': 0.50}
    notas_por_tipo = {}
    for e in evals:
        notas_por_tipo.setdefault(e.tipo, []).append(float(e.calificacion))
    suma_ponderada = 0
    for tipo, peso in pesos.items():
        if tipo in notas_por_tipo and notas_por_tipo[tipo]:
            suma_ponderada += (sum(notas_por_tipo[tipo]) / len(notas_por_tipo[tipo])) * peso
    total_asistencias = len(asistencias)
    faltas = sum(1 for a in asistencias if a.estado == 'falta')
    pct_asistencia = 0
    if total_asistencias > 0:
        pct_asistencia = ((total_asistencias - faltas) / total_asistencias) * 100
        if faltas / total_asistencias >= 0.3:
            return 0, round(pct_asistencia, 1), total_asistencias
        if pct_asistencia == 100:
            suma_ponderada += 1
    return round(min(suma_ponderada, 20), 2), round(pct_asistencia, 1), total_asistencias

def nota_a_letra(nota):
    if nota is None: return '-'
    if nota >= 18: return 'AD'
    if nota >= 16: return 'A'
    if nota >= 12: return 'B'
    return 'C'

def sincronizar_estado_pagos(estudiante_id=None):
    query = PagoRealizado.query.options(joinedload(PagoRealizado.plan))
    if estudiante_id:
        query = query.filter_by(estudiante_id=estudiante_id)
    pagos = query.filter(PagoRealizado.estado != 'pagado').all()
    ahora = datetime.utcnow().date()
    for p in pagos:
        if p.plan and p.plan.fecha_vencimiento < ahora:
            p.estado = 'atrasado'
    db.session.commit()

def sincronizar_mora(estudiante_id=None):
    query = PagoRealizado.query.options(joinedload(PagoRealizado.plan))
    if estudiante_id:
        query = query.filter_by(estudiante_id=estudiante_id)
    pagos = query.filter(PagoRealizado.estado.in_(['pendiente', 'atrasado'])).all()
    ahora = datetime.utcnow().date()
    for p in pagos:
        if p.plan and p.plan.fecha_vencimiento < ahora:
            dias_mora = (ahora - p.plan.fecha_vencimiento).days
            p.mora_acumulada = dias_mora * 5
            p.estado = 'atrasado'
    db.session.commit()

# Registrar helpers como globales de Jinja
def calcular_promedio_bimestre(estudiante_id, curso_id, bimestre_id):
    evals = Evaluacion.query.filter_by(
        estudiante_id=estudiante_id, curso_id=curso_id, bimestre_id=bimestre_id
    ).all()
    asistencias = Asistencia.query.filter_by(
        estudiante_id=estudiante_id, curso_id=curso_id, bimestre_id=bimestre_id
    ).all()
    return _calcular_promedio_desde_datos(evals, asistencias)
app.jinja_env.globals.update(calcular_promedio_bimestre=calcular_promedio_bimestre)
app.jinja_env.globals.update(nota_a_letra=nota_a_letra)
app.jinja_env.globals.update(obtener_bimestre_actual=obtener_bimestre_actual)
app.jinja_env.globals.update(ahora=lambda: datetime.now().strftime('%d/%m/%Y %H:%M'))
app.jinja_env.globals.update(now=datetime.now)

# ====================== AUTH ======================
@app.route('/')
def index():
    if 'usuario_id' in session:
        r = session.get('rol')
        if r == 'directora': return redirect(url_for('directora.dashboard'))
        if r == 'docente': return redirect(url_for('docente.dashboard'))
        if r == 'alumno': return redirect(url_for('estudiante.dashboard'))
    eventos = Evento.query.filter_by(activo=True).order_by(Evento.orden).all()
    return render_template('home.html', eventos=eventos)

@app.route('/contacto', methods=['POST'])
def contacto():
    nombre = request.form.get('nombre', '')
    correo = request.form.get('correo', '')
    telefono = request.form.get('telefono', '')
    interes = request.form.get('interes', '')
    mensaje = request.form.get('mensaje', '')
    flash(f'Gracias {nombre}, hemos recibido tu solicitud. Te contactaremos pronto.', 'success')
    return redirect(url_for('index') + '#contacto')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        clave = request.form.get('clave', '')
        ip = obtener_ip()
        ahora = datetime.utcnow()

        baneo = Baneo.query.filter(
            db.or_(
                db.and_(Baneo.tipo_baneo == 'usuario', Baneo.identificador == correo),
                db.and_(Baneo.tipo_baneo == 'ip', Baneo.ip_address == ip)
            ),
            Baneo.activo == True, Baneo.fecha_fin > ahora
        ).first()
        if baneo:
            flash('Cuenta temporalmente bloqueada. Intente más tarde.', 'danger')
            return render_template('login.html')

        usuario = Colaborador.query.filter_by(correo=correo).first()
        tipo = 'colaborador'
        if not usuario:
            usuario = Estudiante.query.filter_by(correo=correo).first()
            tipo = 'estudiante'

        if usuario and bcrypt.check_password_hash(usuario.clave, clave):
            if not usuario.activo:
                flash('Usuario inactivo', 'danger')
                return render_template('login.html')
            IntentoLogin.query.filter_by(correo=correo).delete()
            session.clear()
            session['usuario_id'] = usuario.id
            session['tipo'] = tipo
            session['nombres'] = usuario.nombres
            if tipo == 'colaborador':
                session['rol'] = usuario.rol
                if usuario.rol == 'directora': return redirect(url_for('directora.dashboard'))
                return redirect(url_for('docente.dashboard'))
            else:
                session['rol'] = 'alumno'
                return redirect(url_for('estudiante.dashboard'))

        intento = IntentoLogin(correo=correo, ip_address=ip, tipo_usuario=tipo if usuario else 'colaborador')
        db.session.add(intento)
        db.session.commit()

        desde = ahora - timedelta(minutes=VENTANA_TIEMPO_MINUTOS)
        intentos_recientes = IntentoLogin.query.filter(
            IntentoLogin.correo == correo,
            IntentoLogin.fecha_intento > desde
        ).count()
        if intentos_recientes >= MAX_INTENTOS_USUARIO:
            ban = Baneo(
                tipo_baneo='usuario', identificador=correo, ip_address=ip,
                fecha_fin=ahora + timedelta(minutes=TIEMPO_BANEO_MINUTOS)
            )
            db.session.add(ban)
            db.session.commit()
            flash('Demasiados intentos. Cuenta bloqueada por 5 minutos.', 'danger')
            return render_template('login.html')

        flash('Correo o Contraseña incorrecta', 'danger')
        return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'success')
    return redirect(url_for('login'))

@app.route('/recuperar_contrasena')
def recuperar_contrasena():
    return render_template('recuperar_contrasena.html')

# ====================== PERFIL ======================
@app.route('/perfil')
@login_required
def perfil():
    uid = request.args.get('id', type=int) or session.get('usuario_id')
    t = session.get('tipo')
    r = session.get('rol')

    # Si se pide un perfil distinto al propio, verificar permisos
    if uid != session.get('usuario_id'):
        if r not in ('directora', 'docente'):
            flash('No tienes permiso para ver este perfil', 'danger')
            return redirect(url_for('login'))
        # Buscar en colaboradores primero, luego estudiantes
        usuario = Colaborador.query.get(uid)
        if not usuario:
            usuario = Estudiante.query.get(uid)
    else:
        if t == 'colaborador': usuario = Colaborador.query.get(uid)
        elif t == 'estudiante': usuario = Estudiante.query.get(uid)
        else: return redirect(url_for('logout'))
    if not usuario:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('directora.dashboard') if r == 'directora' else url_for('docente.dashboard'))
    # Determinar rol del usuario visto
    if hasattr(usuario, 'rol'):
        viewed_rol = usuario.rol
    else:
        viewed_rol = 'alumno'
    return render_template('perfil.html', usuario=usuario, viewed_rol=viewed_rol)

@app.route('/cambiar_clave', methods=['POST'])
@login_required
def cambiar_clave():
    actual = request.form.get('clave_actual')
    nueva = request.form.get('clave_nueva')
    confirmar = request.form.get('clave_confirmar')
    if nueva != confirmar:
        flash('Las contraseñas nuevas no coinciden', 'danger')
        return redirect(url_for('perfil'))
    uid = session.get('usuario_id')
    t = session.get('tipo')
    usuario = None
    if t == 'colaborador': usuario = Colaborador.query.get(uid)
    elif t == 'estudiante': usuario = Estudiante.query.get(uid)
    if not usuario or not bcrypt.check_password_hash(usuario.clave, actual):
        flash('Contraseña actual incorrecta', 'danger')
        return redirect(url_for('perfil'))
    errores = validar_clave(nueva, usuario)
    if errores:
        for e in errores: flash(e, 'danger')
        return redirect(url_for('perfil'))
    usuario.clave = bcrypt.generate_password_hash(nueva).decode('utf-8')
    db.session.commit()
    flash('Contraseña cambiada exitosamente', 'success')
    return redirect(url_for('perfil'))

# ====================== BLUEPRINT REGISTRATION ==========
from routes.routes_directora import directora_bp
from routes.routes_docente import docente_bp
from routes.routes_estudiante import estudiante_bp

app.register_blueprint(directora_bp)
app.register_blueprint(docente_bp)
app.register_blueprint(estudiante_bp)

# ====================== ERROR HANDLERS ======================
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Error interno del servidor'), 500

if __name__ == '__main__':
    app.run(debug=True)
