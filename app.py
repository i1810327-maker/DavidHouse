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
    CarpetaDocente, DocumentoDocente, LogAcceso, IntentoLogin, Baneo
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

init_db(app)
bcrypt = Bcrypt(app)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
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

# ====================== AUTH ======================
@app.route('/')
def index():
    if 'usuario_id' in session:
        r = session.get('rol')
        if r == 'directora': return redirect(url_for('directora_dashboard'))
        if r == 'docente': return redirect(url_for('docente_dashboard'))
        if r == 'alumno': return redirect(url_for('estudiante_dashboard'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        clave = request.form.get('clave', '')
        ip = obtener_ip()
        ahora = datetime.utcnow()

        # Verificar baneos
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
            # Limpiar intentos previos
            IntentoLogin.query.filter_by(correo=correo).delete()
            session.clear()
            session['usuario_id'] = usuario.id
            session['tipo'] = tipo
            session['nombres'] = usuario.nombres
            if tipo == 'colaborador':
                session['rol'] = usuario.rol
                if usuario.rol == 'directora': return redirect(url_for('directora_dashboard'))
                return redirect(url_for('docente_dashboard'))
            else:
                session['rol'] = 'alumno'
                return redirect(url_for('estudiante_dashboard'))

        # Registrar intento fallido
        intento = IntentoLogin(correo=correo, ip_address=ip, tipo_usuario=tipo if usuario else 'colaborador')
        db.session.add(intento)
        db.session.commit()

        # Verificar si excede el límite
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
        return redirect(url_for('directora_dashboard' if r == 'directora' else 'docente_dashboard'))
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

# ====================== HELPERS ======================
def obtener_bimestre_actual():
    hoy = datetime.now().date()
    return Bimestre.query.filter(
        Bimestre.fecha_inicio <= hoy,
        Bimestre.fecha_fin >= hoy
    ).first()

def calcular_promedio_bimestre(estudiante_id, curso_id, bimestre_id):
    evals = Evaluacion.query.filter_by(
        estudiante_id=estudiante_id, curso_id=curso_id, bimestre_id=bimestre_id
    ).all()
    asistencias = Asistencia.query.filter_by(
        estudiante_id=estudiante_id, curso_id=curso_id, bimestre_id=bimestre_id
    ).all()
    return _calcular_promedio_desde_datos(evals, asistencias)

def nota_a_letra(nota):
    if nota is None: return '-'
    if nota >= 18: return 'AD'
    if nota >= 16: return 'A'
    if nota >= 12: return 'B'
    return 'C'

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

# Registrar helpers como globales de Jinja
app.jinja_env.globals.update(calcular_promedio_bimestre=calcular_promedio_bimestre)
app.jinja_env.globals.update(nota_a_letra=nota_a_letra)
app.jinja_env.globals.update(obtener_bimestre_actual=obtener_bimestre_actual)
app.jinja_env.globals.update(ahora=lambda: datetime.now().strftime('%d/%m/%Y %H:%M'))

# ====================== RUTAS DIRECTORA ======================

@app.route('/directora/dashboard')
@login_required
@role_required('directora')
def directora_dashboard():
    colaboradores_count = Colaborador.query.count()
    estudiantes_count = Estudiante.query.count()
    docentes = Colaborador.query.filter_by(rol='docente').all()
    alumnos = Estudiante.query.all()
    grados = Grado.query.all()
    secciones = Seccion.query.all()
    niveles = Nivel.query.all()
    periodos = PeriodoAcademico.query.all()
    cursos = Curso.query.options(
        joinedload(Curso.docente), joinedload(Curso.grado_rel), joinedload(Curso.seccion_rel), joinedload(Curso.periodo)
    ).all()
    bimestres = Bimestre.query.all()
    horarios_list = Horario.query.options(
        joinedload(Horario.curso), joinedload(Horario.seccion), joinedload(Horario.docente), joinedload(Horario.bimestre)
    ).all()
    planes = PagoPlan.query.filter_by(activo=True).all()
    estudiantes = alumnos
    documentos = DocumentoDocente.query.options(
        joinedload(DocumentoDocente.carpeta), joinedload(DocumentoDocente.docente)
    ).filter(DocumentoDocente.estado == 'pendiente').order_by(DocumentoDocente.fecha_subida.desc()).all()
    justificaciones_pendientes = Justificacion.query.options(
        joinedload(Justificacion.asistencia), joinedload(Justificacion.estudiante)
    ).filter_by(estado='pendiente').order_by(Justificacion.fecha_envio.desc()).all()

    # Docentes con conteo de cursos y estudiantes
    docentes_data = []
    for d in docentes:
        cursos_docente = [c for c in cursos if c.docente_id == d.id]
        seccion_ids = set(c.seccion_id for c in cursos_docente if c.seccion_id)
        total_est = Estudiante.query.filter(Estudiante.seccion_id.in_(seccion_ids)).count() if seccion_ids else 0
        iniciales = (d.nombres[0] if d.nombres else '') + (d.apellido_paterno[0] if d.apellido_paterno else '')
        materia = cursos_docente[0].nombre if cursos_docente else (d.profesion or 'Sin asignar')
        docentes_data.append(dict(id=d.id, dni=d.dni, nombres=d.nombres,
            apellido_paterno=d.apellido_paterno, apellido_materno=d.apellido_materno,
            nombre_completo=d.nombre_completo, correo=d.correo, rol=d.rol,
            profesion=d.profesion, activo=d.activo,
            telefono_principal=d.telefono_principal,
            tiene_especialidad=d.tiene_especialidad,
            descripcion_especialidad=d.descripcion_especialidad,
            cursos_count=len(cursos_docente), estudiantes_count=total_est,
            iniciales=iniciales, materia=materia))

    return render_template('dashboard_directora.html',
        colaboradores_count=colaboradores_count,
        estudiantes_count=estudiantes_count,
        docentes=docentes, docentes_data=docentes_data,
        alumnos=alumnos,
        grados=grados, secciones=secciones,
        niveles=niveles, periodos=periodos,
        cursos=cursos, bimestres=bimestres,
        horarios=horarios_list, planes=planes,
        estudiantes=estudiantes, documentos=documentos,
        justificaciones=justificaciones_pendientes)

# ----- CRUD NIVELES -----
@app.route('/directora/niveles', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def niveles_crud():
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'crear':
            n = Nivel(nombre=request.form.get('nombre'))
            db.session.add(n); db.session.commit()
            flash('Nivel creado', 'success')
        elif accion == 'editar':
            n = Nivel.query.get(int(request.form.get('id')))
            if n: n.nombre = request.form.get('nombre'); db.session.commit()
            flash('Nivel actualizado', 'success')
        elif accion == 'toggle':
            n = Nivel.query.get(int(request.form.get('id')))
            if n: n.activo = not n.activo; db.session.commit()
    return redirect(url_for('directora_dashboard'))

# ----- CRUD GRADOS -----
@app.route('/directora/grados', methods=['POST'])
@login_required
@role_required('directora')
def grados_crud():
    accion = request.form.get('accion')
    if accion == 'crear':
        g = Grado(nombre=request.form.get('nombre'), nivel_id=int(request.form.get('nivel_id')), activo=True)
        db.session.add(g); db.session.commit()
        flash('Grado creado', 'success')
    elif accion == 'editar':
        g = Grado.query.get(int(request.form.get('id')))
        if g:
            g.nombre = request.form.get('nombre')
            g.nivel_id = int(request.form.get('nivel_id'))
            db.session.commit()
            flash('Grado actualizado', 'success')
    elif accion == 'toggle':
        g = Grado.query.get(int(request.form.get('id')))
        if g: g.activo = not g.activo; db.session.commit()
    return redirect(url_for('directora_dashboard'))

# ----- CRUD SECCIONES -----
@app.route('/directora/secciones', methods=['POST'])
@login_required
@role_required('directora')
def secciones_crud():
    accion = request.form.get('accion')
    if accion == 'crear':
        s = Seccion(nombre=request.form.get('nombre'), grado_id=int(request.form.get('grado_id')), activo=True)
        db.session.add(s); db.session.commit()
        flash('Sección creada', 'success')
    elif accion == 'editar':
        s = Seccion.query.get(int(request.form.get('id')))
        if s:
            s.nombre = request.form.get('nombre')
            s.grado_id = int(request.form.get('grado_id'))
            db.session.commit()
            flash('Sección actualizada', 'success')
    elif accion == 'toggle':
        s = Seccion.query.get(int(request.form.get('id')))
        if s: s.activo = not s.activo; db.session.commit()
    return redirect(url_for('directora_dashboard'))

# ----- CRUD PERIODOS -----
@app.route('/directora/periodos', methods=['POST'])
@login_required
@role_required('directora')
def periodos_crud():
    accion = request.form.get('accion')
    if accion == 'crear':
        p = PeriodoAcademico(
            nombre=request.form.get('nombre'),
            fecha_inicio=datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d'),
            fecha_fin=datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d')
        )
        db.session.add(p); db.session.commit()
        flash('Periodo creado', 'success')
    elif accion == 'editar':
        p = PeriodoAcademico.query.get(int(request.form.get('id')))
        if p:
            p.nombre = request.form.get('nombre')
            p.fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d')
            p.fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d')
            db.session.commit()
            flash('Periodo actualizado', 'success')
    elif accion == 'toggle':
        p = PeriodoAcademico.query.get(int(request.form.get('id')))
        if p: p.activo = not p.activo; db.session.commit()
    return redirect(url_for('directora_dashboard'))

# ----- CRUD BIMESTRES -----
@app.route('/directora/bimestres', methods=['POST'])
@login_required
@role_required('directora')
def bimestres_crud():
    accion = request.form.get('accion')
    if accion == 'crear':
        b = Bimestre(
            periodo_academico_id=int(request.form.get('periodo_academico_id')),
            nombre=request.form.get('nombre'),
            numero=int(request.form.get('numero')),
            fecha_inicio=datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d'),
            fecha_fin=datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d')
        )
        db.session.add(b); db.session.commit()
        flash('Bimestre creado', 'success')
    elif accion == 'editar':
        b = Bimestre.query.get(int(request.form.get('id')))
        if b:
            for campo in ['nombre', 'numero', 'periodo_academico_id']:
                val = request.form.get(campo)
                if val: setattr(b, campo, int(val) if campo in ('numero', 'periodo_academico_id') else val)
            for campo in ['fecha_inicio', 'fecha_fin']:
                val = request.form.get(campo)
                if val: setattr(b, campo, datetime.strptime(val, '%Y-%m-%d'))
            db.session.commit()
            flash('Bimestre actualizado', 'success')
    elif accion == 'toggle':
        b = Bimestre.query.get(int(request.form.get('id')))
        # No tiene activo, así que simplemente lo eliminamos lógicamente
        flash('Usa el periodo para activar/desactivar', 'info')
    return redirect(url_for('directora_dashboard'))

# ----- CRUD CURSOS -----
@app.route('/directora/cursos', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def cursos_crud():
    if request.method == 'POST':
        accion = request.form.get('accion', 'crear')
        if accion == 'crear':
            c = Curso(
                nombre=request.form.get('nombre'),
                codigo=request.form.get('codigo'),
                descripcion=request.form.get('descripcion', ''),
                docente_id=int(request.form.get('docente_id')),
                grado_id=int(request.form.get('grado_id')),
                seccion_id=int(request.form.get('seccion_id')),
                periodo_academico_id=int(request.form.get('periodo_academico_id'))
            )
            db.session.add(c); db.session.commit()
            flash('Curso creado', 'success')
        elif accion == 'editar':
            c = Curso.query.get(int(request.form.get('id')))
            if c:
                c.nombre = request.form.get('nombre')
                c.codigo = request.form.get('codigo')
                c.descripcion = request.form.get('descripcion', '')
                c.docente_id = int(request.form.get('docente_id'))
                c.grado_id = int(request.form.get('grado_id'))
                c.seccion_id = int(request.form.get('seccion_id'))
                c.periodo_academico_id = int(request.form.get('periodo_academico_id'))
                db.session.commit()
                flash('Curso actualizado', 'success')
        elif accion == 'toggle':
            c = Curso.query.get(int(request.form.get('id')))
            if c: c.activo = not c.activo; db.session.commit()
    return redirect(url_for('directora_dashboard'))

# ----- API: dropdowns dinámicos -----
@app.route('/directora/api/grados/<int:nivel_id>')
@login_required
@role_required('directora')
def api_grados_por_nivel(nivel_id):
    grados = Grado.query.filter_by(nivel_id=nivel_id, activo=True).all()
    return jsonify([{'id': g.id, 'nombre': g.nombre} for g in grados])

@app.route('/directora/api/secciones/<int:grado_id>')
@login_required
@role_required('directora')
def api_secciones_por_grado(grado_id):
    secciones = Seccion.query.filter_by(grado_id=grado_id, activo=True).all()
    return jsonify([{'id': s.id, 'nombre': s.nombre} for s in secciones])

@app.route('/api/estudiantes_por_curso/<int:curso_id>')
@login_required
@role_required('directora', 'docente')
def api_estudiantes_por_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    inscripciones = Inscripcion.query.filter_by(curso_id=curso_id).all()
    estudiantes = [{'id': ins.alumno.id, 'nombre': ins.alumno.nombre_completo} for ins in inscripciones]
    return jsonify(estudiantes)

# ----- CRUD HORARIOS -----
@app.route('/directora/horarios', methods=['POST'])
@login_required
@role_required('directora')
def horarios_crud():
    accion = request.form.get('accion', 'crear')
    if accion == 'crear':
        h = Horario(
            curso_id=int(request.form.get('curso_id')),
            seccion_id=int(request.form.get('seccion_id')),
            docente_id=int(request.form.get('docente_id')),
            dia_semana=int(request.form.get('dia_semana')),
            hora_inicio=datetime.strptime(request.form.get('hora_inicio'), '%H:%M').time(),
            hora_fin=datetime.strptime(request.form.get('hora_fin'), '%H:%M').time(),
            bimestre_id=int(request.form.get('bimestre_id')) if request.form.get('bimestre_id') else None
        )
        db.session.add(h); db.session.commit()
        flash('Horario creado', 'success')
    elif accion == 'eliminar':
        h = Horario.query.get(int(request.form.get('id')))
        if h: db.session.delete(h); db.session.commit()
        flash('Horario eliminado', 'success')
    return redirect(url_for('directora_dashboard'))

# ----- COLABORADORES (CRUD completo) -----
@app.route('/directora/colaboradores')
@login_required
@role_required('directora')
def listar_colaboradores():
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/colaboradores/crear', methods=['POST'])
@login_required
@role_required('directora')
def crear_colaborador():
    dni = request.form.get('dni')
    if Colaborador.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora_dashboard'))
    correo = request.form.get('correo')
    if Colaborador.query.filter_by(correo=correo).first():
        flash('El correo ya existe', 'danger')
        return redirect(url_for('directora_dashboard'))
    clave = request.form.get('clave')
    errores = validar_clave(clave)
    if errores:
        for e in errores: flash(e, 'danger')
        return redirect(url_for('directora_dashboard'))
    c = Colaborador(
        dni=dni,
        nombres=request.form.get('nombres'),
        apellido_paterno=request.form.get('apellido_paterno'),
        apellido_materno=request.form.get('apellido_materno'),
        correo=correo,
        clave=bcrypt.generate_password_hash(clave).decode('utf-8'),
        rol=request.form.get('rol'),
        profesion=request.form.get('profesion', ''),
        tiene_especialidad='tiene_especialidad' in request.form,
        descripcion_especialidad=request.form.get('descripcion_especialidad', ''),
        telefono_principal=request.form.get('telefono_principal', ''),
        telefono_secundario=request.form.get('telefono_secundario', ''),
        seccion_id=int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None
    )
    db.session.add(c); db.session.commit()
    flash(f'Colaborador {c.nombre_completo} creado', 'success')
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/colaboradores/editar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def editar_colaborador(id):
    c = Colaborador.query.get_or_404(id)
    dni = request.form.get('dni')
    if dni != c.dni and Colaborador.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora_dashboard'))
    c.dni = dni
    c.nombres = request.form.get('nombres')
    c.apellido_paterno = request.form.get('apellido_paterno')
    c.apellido_materno = request.form.get('apellido_materno')
    c.correo = request.form.get('correo')
    c.rol = request.form.get('rol')
    c.profesion = request.form.get('profesion', '')
    c.tiene_especialidad = 'tiene_especialidad' in request.form
    c.descripcion_especialidad = request.form.get('descripcion_especialidad', '')
    c.telefono_principal = request.form.get('telefono_principal', '')
    c.telefono_secundario = request.form.get('telefono_secundario', '')
    c.seccion_id = int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None
    clave = request.form.get('clave')
    if clave:
        errores = validar_clave(clave, c)
        if errores:
            for e in errores: flash(e, 'danger')
            return redirect(url_for('directora_dashboard'))
        c.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
    db.session.commit()
    flash('Colaborador actualizado', 'success')
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/colaboradores/toggle/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def toggle_colaborador(id):
    c = Colaborador.query.get_or_404(id)
    c.activo = not c.activo
    db.session.commit()
    flash(f'Colaborador {"activado" if c.activo else "desactivado"}', 'success')
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/colaboradores/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def eliminar_colaborador(id):
    c = Colaborador.query.get_or_404(id)
    Horario.query.filter_by(docente_id=c.id).delete()
    db.session.delete(c); db.session.commit()
    flash('Colaborador eliminado', 'success')
    return redirect(url_for('directora_dashboard'))

# ----- FORMULARIOS COMPLETOS (separados) -----
@app.route('/directora/registrar_docente', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def registrar_docente():
    if request.method == 'POST':
        dni = request.form.get('dni')
        if Colaborador.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('registrar_docente'))
        correo = request.form.get('correo')
        if Colaborador.query.filter_by(correo=correo).first():
            flash('El correo ya existe', 'danger')
            return redirect(url_for('registrar_docente'))
        clave = request.form.get('clave')
        errores = validar_clave(clave)
        if errores:
            for e in errores: flash(e, 'danger')
            return redirect(url_for('registrar_docente'))
        c = Colaborador(
            dni=dni,
            nombres=request.form.get('nombres'),
            apellido_paterno=request.form.get('apellido_paterno'),
            apellido_materno=request.form.get('apellido_materno'),
            correo=correo,
            clave=bcrypt.generate_password_hash(clave).decode('utf-8'),
            rol='docente',
            profesion=request.form.get('profesion', ''),
            tiene_especialidad='tiene_especialidad' in request.form,
            descripcion_especialidad=request.form.get('descripcion_especialidad', ''),
            telefono_principal=request.form.get('telefono_principal', ''),
            telefono_secundario=request.form.get('telefono_secundario', '')
        )
        db.session.add(c); db.session.commit()
        seccion_id = request.form.get('seccion_docente_id')
        if seccion_id:
            s = Seccion.query.get(int(seccion_id))
            if s: s.docente_id = c.id; db.session.commit()
        flash(f'Docente {c.nombre_completo} registrado', 'success')
        return redirect(url_for('listar_docentes'))
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('docentes_form.html', grados_data=grados_data)

@app.route('/directora/listar_docentes')
@login_required
@role_required('directora')
def listar_docentes():
    docentes = Colaborador.query.filter_by(rol='docente').all()
    return render_template('listar_docentes.html', docentes=docentes)

@app.route('/directora/listar_alumnos')
@login_required
@role_required('directora')
def listar_alumnos():
    alumnos = Estudiante.query.all()
    return render_template('listar_alumnos.html', alumnos=alumnos)

@app.route('/directora/registrar_alumno', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def registrar_alumno():
    if request.method == 'POST':
        dni = request.form.get('dni')
        if Estudiante.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('registrar_alumno'))
        correo = request.form.get('correo')
        if Estudiante.query.filter_by(correo=correo).first():
            flash('El correo ya existe', 'danger')
            return redirect(url_for('registrar_alumno'))
        clave = request.form.get('clave')
        errores = validar_clave(clave)
        if errores:
            for e in errores: flash(e, 'danger')
            return redirect(url_for('registrar_alumno'))
        a = Estudiante(
            dni=dni,
            nombres=request.form.get('nombres'),
            apellido_paterno=request.form.get('apellido_paterno'),
            apellido_materno=request.form.get('apellido_materno'),
            correo=correo,
            clave=bcrypt.generate_password_hash(clave).decode('utf-8'),
            grado_id=int(request.form.get('grado_id')) if request.form.get('grado_id') else None,
            seccion_id=int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None
        )
        db.session.add(a); db.session.commit()
        ap_nombres = request.form.get('apoderado_nombres')
        if ap_nombres:
            ap = Apoderado(
                nombres=ap_nombres,
                apellido_paterno=request.form.get('apoderado_apellido_paterno', ''),
                apellido_materno=request.form.get('apoderado_apellido_materno', ''),
                telefono_principal=request.form.get('apoderado_telefono_principal', ''),
                telefono_secundario=request.form.get('apoderado_telefono_secundario', ''),
                alumno_id=a.id
            )
            db.session.add(ap); db.session.commit()
        flash(f'Estudiante {a.nombre_completo} registrado', 'success')
        return redirect(url_for('listar_alumnos'))
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('registrar_alumno.html', grados_data=grados_data)

@app.route('/directora/editar_docente/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def editar_docente(id):
    c = Colaborador.query.get_or_404(id)
    if c.rol != 'docente':
        flash('No es un docente', 'danger')
        return redirect(url_for('listar_docentes'))
    if request.method == 'POST':
        dni = request.form.get('dni')
        if dni != c.dni and Colaborador.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('editar_docente', id=id))
        c.dni = dni
        c.nombres = request.form.get('nombres')
        c.apellido_paterno = request.form.get('apellido_paterno')
        c.apellido_materno = request.form.get('apellido_materno')
        c.correo = request.form.get('correo')
        c.profesion = request.form.get('profesion', '')
        c.tiene_especialidad = 'tiene_especialidad' in request.form
        c.descripcion_especialidad = request.form.get('descripcion_especialidad', '')
        c.telefono_principal = request.form.get('telefono_principal', '')
        c.telefono_secundario = request.form.get('telefono_secundario', '')
        clave = request.form.get('clave')
        if clave:
            errores = validar_clave(clave, c)
            if errores:
                for e in errores: flash(e, 'danger')
                return redirect(url_for('editar_docente', id=id))
            c.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
        seccion_id = request.form.get('seccion_docente_id')
        if seccion_id:
            s = Seccion.query.get(int(seccion_id))
            if s: s.docente_id = c.id
        db.session.commit()
        flash('Docente actualizado', 'success')
        return redirect(url_for('listar_docentes'))
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('editar_docente.html', docente=c, grados_data=grados_data)

@app.route('/directora/editar_alumno/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def editar_alumno(id):
    a = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        dni = request.form.get('dni')
        if dni != a.dni and Estudiante.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('editar_alumno', id=id))
        correo = request.form.get('correo')
        if correo != a.correo and Estudiante.query.filter_by(correo=correo).first():
            flash('El correo ya existe', 'danger')
            return redirect(url_for('editar_alumno', id=id))
        a.dni = dni
        a.nombres = request.form.get('nombres')
        a.apellido_paterno = request.form.get('apellido_paterno')
        a.apellido_materno = request.form.get('apellido_materno')
        a.correo = correo
        a.grado_id = int(request.form.get('grado_id')) if request.form.get('grado_id') else None
        a.seccion_id = int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None
        clave = request.form.get('clave')
        if clave:
            errores = validar_clave(clave)
            if errores:
                for e in errores: flash(e, 'danger')
                return redirect(url_for('editar_alumno', id=id))
            a.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
        # Guardar apoderado
        ap = Apoderado.query.filter_by(alumno_id=a.id).first()
        if request.form.get('apo_nombres'):
            if not ap:
                ap = Apoderado(alumno_id=a.id)
                db.session.add(ap)
            ap.nombres = request.form.get('apo_nombres')
            ap.apellido_paterno = request.form.get('apo_apellido_paterno')
            ap.apellido_materno = request.form.get('apo_apellido_materno')
            ap.telefono_principal = request.form.get('apo_telefono_principal')
            ap.telefono_secundario = request.form.get('apo_telefono_secundario')
            ap.es_apoderado = request.form.get('es_apoderado') == 'on'
        db.session.commit()
        flash('Estudiante actualizado', 'success')
        return redirect(url_for('listar_alumnos'))
    apoderado = Apoderado.query.filter_by(alumno_id=a.id).first()
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('editar_alumno.html', alumno=a, apoderado=apoderado,
                           grados=grados, grados_data=grados_data)

@app.route('/directora/eliminar_alumno/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def eliminar_alumno(id):
    a = Estudiante.query.get_or_404(id)
    Apoderado.query.filter_by(alumno_id=a.id).delete()
    Inscripcion.query.filter_by(alumno_id=a.id).delete()
    Evaluacion.query.filter_by(estudiante_id=a.id).delete()
    Asistencia.query.filter_by(estudiante_id=a.id).delete()
    Comentario.query.filter_by(estudiante_id=a.id).delete()
    PagoRealizado.query.filter_by(estudiante_id=a.id).delete()
    db.session.delete(a); db.session.commit()
    flash('Estudiante eliminado', 'success')
    return redirect(url_for('listar_alumnos'))

@app.route('/directora/eliminar_docente/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def eliminar_docente(id):
    c = Colaborador.query.get_or_404(id)
    Horario.query.filter_by(docente_id=c.id).delete()
    db.session.delete(c); db.session.commit()
    flash('Docente eliminado', 'success')
    return redirect(url_for('listar_docentes'))

# ----- ESTUDIANTES (CRUD completo) -----
@app.route('/directora/estudiantes')
@login_required
@role_required('directora')
def listar_estudiantes():
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/estudiantes/crear', methods=['POST'])
@login_required
@role_required('directora')
def crear_estudiante():
    dni = request.form.get('dni')
    if Estudiante.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora_dashboard'))
    correo = request.form.get('correo')
    if Estudiante.query.filter_by(correo=correo).first():
        flash('El correo ya existe', 'danger')
        return redirect(url_for('directora_dashboard'))
    clave = request.form.get('clave')
    errores = validar_clave(clave)
    if errores:
        for e in errores: flash(e, 'danger')
        return redirect(url_for('directora_dashboard'))
    e = Estudiante(
        dni=dni,
        nombres=request.form.get('nombres'),
        apellido_paterno=request.form.get('apellido_paterno'),
        apellido_materno=request.form.get('apellido_materno'),
        correo=correo,
        clave=bcrypt.generate_password_hash(clave).decode('utf-8'),
        grado_id=int(request.form.get('grado_id')) if request.form.get('grado_id') else None,
        seccion_id=int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None
    )
    db.session.add(e); db.session.commit()
    flash(f'Estudiante {e.nombre_completo} creado', 'success')
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/estudiantes/editar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def editar_estudiante(id):
    e = Estudiante.query.get_or_404(id)
    dni = request.form.get('dni')
    if dni != e.dni and Estudiante.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora_dashboard'))
    e.dni = dni
    e.nombres = request.form.get('nombres')
    e.apellido_paterno = request.form.get('apellido_paterno')
    e.apellido_materno = request.form.get('apellido_materno')
    e.correo = request.form.get('correo')
    e.grado_id = int(request.form.get('grado_id')) if request.form.get('grado_id') else None
    e.seccion_id = int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None
    clave = request.form.get('clave')
    if clave:
        errores = validar_clave(clave, e)
        if errores:
            for e2 in errores: flash(e2, 'danger')
            return redirect(url_for('directora_dashboard'))
        e.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
    db.session.commit()
    flash('Estudiante actualizado', 'success')
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/estudiantes/toggle/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def toggle_estudiante(id):
    e = Estudiante.query.get_or_404(id)
    e.activo = not e.activo
    db.session.commit()
    flash(f'Estudiante {"activado" if e.activo else "desactivado"}', 'success')
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/estudiantes/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def eliminar_estudiante(id):
    e = Estudiante.query.get_or_404(id)
    Apoderado.query.filter_by(alumno_id=e.id).delete()
    Inscripcion.query.filter_by(alumno_id=e.id).delete()
    Evaluacion.query.filter_by(estudiante_id=e.id).delete()
    Asistencia.query.filter_by(estudiante_id=e.id).delete()
    Comentario.query.filter_by(estudiante_id=e.id).delete()
    PagoRealizado.query.filter_by(estudiante_id=e.id).delete()
    db.session.delete(e); db.session.commit()
    flash('Estudiante eliminado', 'success')
    return redirect(url_for('directora_dashboard'))

# ----- JUSTIFICACIONES (revisión directora) -----
@app.route('/directora/justificaciones', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def justificaciones_revision():
    if request.method == 'POST':
        j = Justificacion.query.get(int(request.form.get('id')))
        if j:
            j.estado = request.form.get('estado')
            j.comentario_revision = request.form.get('comentario_revision', '')
            j.fecha_revision = tiempo_actual()
            j.revisado_por = session['usuario_id']
            # Si se aprueba, cambiar asistencia a justificado
            if j.estado == 'aprobado' and j.asistencia:
                j.asistencia.estado = 'justificado'
            db.session.commit()
            flash('Justificación revisada', 'success')
        return redirect(url_for('directora_dashboard'))
    justificaciones = Justificacion.query.options(
        joinedload(Justificacion.asistencia), joinedload(Justificacion.estudiante)
    ).order_by(Justificacion.fecha_envio.desc()).all()
    return redirect(url_for('directora_dashboard'))

# ----- BOLETA DE NOTAS -----
@app.route('/directora/boletas')
@login_required
@role_required('directora')
def boletas():
    return redirect(url_for('directora_dashboard'))

@app.route('/directora/boletas/generar', methods=['POST'])
@login_required
@role_required('directora')
def generar_boleta():
    seccion_id = int(request.form.get('seccion_id'))
    bimestre_id = int(request.form.get('bimestre_id'))
    estudiantes = Estudiante.query.filter_by(seccion_id=seccion_id, activo=True).order_by(Estudiante.apellido_paterno).all()
    seccion = Seccion.query.get(seccion_id)
    bimestre = Bimestre.query.get(bimestre_id)
    cursos = Curso.query.filter_by(seccion_id=seccion_id, periodo_academico_id=bimestre.periodo_academico_id).all()
    curso_ids = [c.id for c in cursos]
    estudiante_ids = [e.id for e in estudiantes]

    # Batch fetch all evaluations and asistencia for this section/bimestre
    todas_evals = Evaluacion.query.filter(
        Evaluacion.estudiante_id.in_(estudiante_ids),
        Evaluacion.curso_id.in_(curso_ids),
        Evaluacion.bimestre_id == bimestre_id
    ).all()
    todas_asistencias = Asistencia.query.filter(
        Asistencia.estudiante_id.in_(estudiante_ids),
        Asistencia.curso_id.in_(curso_ids),
        Asistencia.bimestre_id == bimestre_id
    ).all()

    # Index by (estudiante_id, curso_id)
    evals_idx = {}
    for ev in todas_evals:
        key = (ev.estudiante_id, ev.curso_id)
        if key not in evals_idx:
            evals_idx[key] = []
        evals_idx[key].append(ev)

    asistencias_idx = {}
    for a in todas_asistencias:
        key = (a.estudiante_id, a.curso_id)
        if key not in asistencias_idx:
            asistencias_idx[key] = []
        asistencias_idx[key].append(a)

    pesos = {'cuaderno': 0.10, 'libro': 0.10, 'practicas': 0.20, 'exposiciones': 0.10, 'examen': 0.50}

    notas_data = {}
    for estudiante in estudiantes:
        notas_data[estudiante.id] = {}
        for curso in cursos:
            evals = evals_idx.get((estudiante.id, curso.id), [])
            asistencias = asistencias_idx.get((estudiante.id, curso.id), [])

            if not evals:
                continue

            prom_final, pct_asistencia, total_asistencias = _calcular_promedio_desde_datos(evals, asistencias, pesos)

            notas_data[estudiante.id][curso.id] = {
                'promedio': prom_final,
                'letra': nota_a_letra(prom_final),
                'asistencia': round(pct_asistencia, 1),
                'total_asistencias': total_asistencias
            }

    return render_template('boleta_pdf.html',
        estudiantes=estudiantes, cursos=cursos,
        notas=notas_data, seccion=seccion, bimestre=bimestre)

# ----- PAGOS -----
@app.route('/directora/pagos', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def pagos_directora():
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'crear_plan':
            p = PagoPlan(
                periodo_academico_id=int(request.form.get('periodo_academico_id')),
                nombre=request.form.get('nombre'),
                monto=request.form.get('monto'),
                nivel_id=int(request.form.get('nivel_id')) if request.form.get('nivel_id') else None,
                grado_id=int(request.form.get('grado_id')) if request.form.get('grado_id') else None,
                tipo=request.form.get('tipo'),
                fecha_vencimiento=datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')
            )
            db.session.add(p); db.session.commit()
            flash('Plan de pago creado', 'success')
        elif accion == 'registrar_pago':
            r = PagoRealizado(
                estudiante_id=int(request.form.get('estudiante_id')),
                pago_plan_id=int(request.form.get('pago_plan_id')),
                monto_pagado=request.form.get('monto_pagado'),
                estado='pagado'
            )
            db.session.add(r); db.session.commit()
            flash('Pago registrado', 'success')
        return redirect(url_for('directora_dashboard'))
    return redirect(url_for('directora_dashboard'))

# ----- CARPETA DOCENTE (admin) -----
@app.route('/directora/carpetas', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def carpetas_admin():
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'crear':
            c = CarpetaDocente(
                nombre=request.form.get('nombre'),
                descripcion=request.form.get('descripcion', ''),
                bimestre_id=int(request.form.get('bimestre_id')) if request.form.get('bimestre_id') else None,
                fecha_inicio_entrega=datetime.strptime(request.form.get('fecha_inicio_entrega'), '%Y-%m-%dT%H:%M'),
                fecha_fin_entrega=datetime.strptime(request.form.get('fecha_fin_entrega'), '%Y-%m-%dT%H:%M'),
                creado_por=session['usuario_id']
            )
            db.session.add(c); db.session.commit()
            flash('Carpeta creada', 'success')
        elif accion == 'revisar':
            doc = DocumentoDocente.query.get(int(request.form.get('id')))
            if doc:
                doc.estado = request.form.get('estado')
                doc.comentario_revision = request.form.get('comentario_revision', '')
                doc.fecha_revision = tiempo_actual()
                db.session.commit()
                flash('Documento revisado', 'success')
        return redirect(url_for('directora_dashboard'))
    return redirect(url_for('directora_dashboard'))

# ====================== RUTAS DOCENTE ======================

@app.route('/docente/dashboard')
@login_required
@role_required('docente')
def docente_dashboard():
    docente = Colaborador.query.get(session['usuario_id'])
    cursos = Curso.query.options(
        joinedload(Curso.grado_rel), joinedload(Curso.seccion_rel), joinedload(Curso.periodo)
    ).filter_by(docente_id=docente.id, activo=True).all()
    seccion_ids = {c.seccion_id for c in cursos if c.seccion_id}
    total_estudiantes = Estudiante.query.filter(Estudiante.seccion_id.in_(seccion_ids)).count() if seccion_ids else 0
    return render_template('dashboard_docente.html', docente=docente, cursos=cursos, total_estudiantes=total_estudiantes)

@app.route('/docente/cursos/<int:curso_id>/evaluaciones', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def evaluaciones_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    if curso.docente_id != session['usuario_id']:
        flash('No tienes permiso para este curso', 'danger')
        return redirect(url_for('docente_dashboard'))
    bimestre_id = request.args.get('bimestre_id', type=int) or (obtener_bimestre_actual().id if obtener_bimestre_actual() else None)
    estudiantes = Estudiante.query.filter_by(
        seccion_id=curso.seccion_id, activo=True
    ).order_by(Estudiante.apellido_paterno).all()
    bimestres = Bimestre.query.filter_by(periodo_academico_id=curso.periodo_academico_id).all()

    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'guardar':
            estudiante_id = int(request.form.get('estudiante_id'))
            tipo = request.form.get('tipo')
            calificacion = float(request.form.get('calificacion'))
            if 0 <= calificacion <= 20:
                e = Evaluacion(
                    curso_id=curso_id, estudiante_id=estudiante_id,
                    bimestre_id=bimestre_id, tipo=tipo,
                    calificacion=calificacion,
                    fecha=datetime.now().date(),
                    observaciones=request.form.get('observaciones', '')
                )
                db.session.add(e); db.session.commit()
                flash('Calificación guardada', 'success')
            else:
                flash('La nota debe ser entre 0 y 20', 'danger')
        elif accion == 'importar':
            archivo = request.files.get('archivo')
            valido, msg = validar_archivo(archivo)
            if not valido or not archivo.filename.endswith('.xlsx'):
                flash(msg or 'Sube un archivo .xlsx válido', 'danger')
            elif not HAS_OPENPYXL:
                flash('openpyxl no instalado. Ejecuta: pip install openpyxl', 'danger')
            else:
                try:
                    wb = openpyxl.load_workbook(archivo)
                    ws = wb.active

                    # Pre-fetch all students and existing evaluations for this course/bimestre
                    dnis = []
                    rows_data = []
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        dni = str(row[2]) if row[2] is not None else ''
                        if dni:
                            dnis.append(dni)
                            rows_data.append((dni, row[3], row[4], row[5], row[6], row[7]))

                    estudiantes_map = {}
                    if dnis:
                        for e in Estudiante.query.filter(Estudiante.dni.in_(dnis)).all():
                            estudiantes_map[e.dni] = e

                    existing_evals = Evaluacion.query.filter_by(
                        curso_id=curso_id, bimestre_id=bimestre_id
                    ).all()
                    evals_key = {}
                    for ev in existing_evals:
                        evals_key[(ev.estudiante_id, ev.tipo)] = ev

                    for dni, cuaderno, libro, practicas, exposiciones, examen in rows_data:
                        est = estudiantes_map.get(dni)
                        if not est:
                            continue
                        for tipo, nota in [('cuaderno', cuaderno), ('libro', libro), ('practicas', practicas), ('exposiciones', exposiciones), ('examen', examen)]:
                            if nota is not None:
                                key = (est.id, tipo)
                                if key in evals_key:
                                    evals_key[key].calificacion = float(nota)
                                else:
                                    ev = Evaluacion(
                                        curso_id=curso_id, estudiante_id=est.id,
                                        bimestre_id=bimestre_id, tipo=tipo,
                                        calificacion=float(nota), fecha=datetime.now().date()
                                    )
                                    db.session.add(ev)
                    db.session.commit()
                    flash('Notas importadas desde Excel', 'success')
                except Exception as ex:
                    flash(f'Error al importar: {str(ex)}', 'danger')
        return redirect(url_for('evaluaciones_curso', curso_id=curso_id))

    # Recuperar evaluaciones existentes para mostrarlas
    evaluaciones = Evaluacion.query.filter_by(curso_id=curso_id, bimestre_id=bimestre_id).all()
    evals_por_estudiante = {}
    for ev in evaluaciones:
        if ev.estudiante_id not in evals_por_estudiante:
            evals_por_estudiante[ev.estudiante_id] = {}
        if ev.tipo not in evals_por_estudiante[ev.estudiante_id]:
            evals_por_estudiante[ev.estudiante_id][ev.tipo] = []
        evals_por_estudiante[ev.estudiante_id][ev.tipo].append(float(ev.calificacion))

    return render_template('evaluaciones.html',
        curso=curso, estudiantes=estudiantes,
        bimestre_id=bimestre_id, bimestres=bimestres,
        evals=evals_por_estudiante)

@app.route('/docente/cursos/<int:curso_id>/asistencia', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def asistencia_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    if curso.docente_id != session['usuario_id']:
        flash('No tienes permiso para este curso', 'danger')
        return redirect(url_for('docente_dashboard'))
    bimestre_id = request.args.get('bimestre_id', type=int) or (obtener_bimestre_actual().id if obtener_bimestre_actual() else None)
    estudiantes = Estudiante.query.filter_by(
        seccion_id=curso.seccion_id, activo=True
    ).order_by(Estudiante.apellido_paterno).all()

    if request.method == 'POST':
        fecha = datetime.strptime(request.form.get('fecha'), '%Y-%m-%d').date()
        # Pre-fetch existing records for this date
        existentes = Asistencia.query.filter_by(
            curso_id=curso_id, fecha=fecha, bimestre_id=bimestre_id
        ).all()
        existentes_idx = {a.estudiante_id: a for a in existentes}
        for est in estudiantes:
            estado = request.form.get(f'estado_{est.id}', 'presente')
            if est.id in existentes_idx:
                existentes_idx[est.id].estado = estado
            else:
                a = Asistencia(curso_id=curso_id, estudiante_id=est.id,
                    bimestre_id=bimestre_id, fecha=fecha,
                    estado=estado, marcado_por=session['usuario_id'])
                db.session.add(a)
        db.session.commit()
        flash('Asistencia guardada', 'success')
        return redirect(url_for('asistencia_curso', curso_id=curso_id))

    fecha_seleccionada = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    asistencias_hoy = {}
    asis = Asistencia.query.filter_by(curso_id=curso_id, fecha=fecha_seleccionada, bimestre_id=bimestre_id).all()
    for a in asis:
        asistencias_hoy[a.estudiante_id] = a.estado

    bimestres = Bimestre.query.filter_by(periodo_academico_id=curso.periodo_academico_id).all()
    return render_template('asistencia.html',
        curso=curso, estudiantes=estudiantes,
        fecha=fecha_seleccionada, asistencias=asistencias_hoy,
        bimestre_id=bimestre_id, bimestres=bimestres)

@app.route('/docente/comentarios', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def comentarios_docente():
    docente = Colaborador.query.get(session['usuario_id'])
    cursos = Curso.query.options(joinedload(Curso.grado_rel), joinedload(Curso.seccion_rel)).filter_by(docente_id=docente.id).all()
    if request.method == 'POST':
        c = Comentario(
            docente_id=docente.id,
            estudiante_id=int(request.form.get('estudiante_id')),
            tipo=request.form.get('tipo'),
            contenido=request.form.get('contenido'),
            bimestre_id=int(request.form.get('bimestre_id')) if request.form.get('bimestre_id') else None
        )
        db.session.add(c); db.session.commit()
        flash('Comentario enviado', 'success')
        return redirect(url_for('comentarios_docente'))
    comentarios = Comentario.query.filter_by(docente_id=docente.id).order_by(Comentario.fecha_creacion.desc()).all()
    return render_template('comentarios_docente.html', cursos=cursos, comentarios=comentarios, bimestres=Bimestre.query.all())

@app.route('/docente/documentos', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def documentos_docente():
    docente = Colaborador.query.get(session['usuario_id'])
    if request.method == 'POST':
        archivo = request.files.get('archivo')
        valido, msg = validar_archivo(archivo)
        if not valido:
            flash(msg, 'danger')
            return redirect(url_for('documentos_docente'))
        from werkzeug.utils import secure_filename
        filename = secure_filename(archivo.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        archivo.save(filepath)
        d = DocumentoDocente(
            carpeta_id=int(request.form.get('carpeta_id')),
            docente_id=docente.id,
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion', ''),
            archivo_nombre=filename,
            archivo_ruta=f'uploads/{filename}'
        )
        db.session.add(d); db.session.commit()
        flash('Documento subido', 'success')
        return redirect(url_for('documentos_docente'))
    carpetas = CarpetaDocente.query.filter_by(activo=True).all()
    documentos = DocumentoDocente.query.filter_by(docente_id=docente.id).order_by(DocumentoDocente.fecha_subida.desc()).all()
    return render_template('documentos_docente.html', carpetas=carpetas, documentos=documentos)

# ====================== RUTAS ESTUDIANTE ======================

@app.route('/estudiante/dashboard')
@login_required
@role_required('alumno')
def estudiante_dashboard():
    estudiante = Estudiante.query.get(session['usuario_id'])
    bimestre = obtener_bimestre_actual()

    # Cursos del estudiante
    inscripciones = Inscripcion.query.filter_by(alumno_id=estudiante.id).all()
    cursos = [i.curso for i in inscripciones]

    # Promedios por curso - batch
    promedios = {}
    if bimestre and cursos:
        curso_ids = [c.id for c in cursos]
        todas_evals = Evaluacion.query.filter(
            Evaluacion.estudiante_id == estudiante.id,
            Evaluacion.curso_id.in_(curso_ids),
            Evaluacion.bimestre_id == bimestre.id
        ).all()
        todas_asistencias = Asistencia.query.filter(
            Asistencia.estudiante_id == estudiante.id,
            Asistencia.curso_id.in_(curso_ids),
            Asistencia.bimestre_id == bimestre.id
        ).all()

        evals_idx = {}
        for ev in todas_evals:
            evals_idx.setdefault(ev.curso_id, []).append(ev)
        asistencias_idx = {}
        for a in todas_asistencias:
            asistencias_idx.setdefault(a.curso_id, []).append(a)

        pesos = {'cuaderno': 0.10, 'libro': 0.10, 'practicas': 0.20, 'exposiciones': 0.10, 'examen': 0.50}
        for curso in cursos:
            prom, asist, total = _calcular_promedio_desde_datos(
                evals_idx.get(curso.id, []), asistencias_idx.get(curso.id, []), pesos
            )
            if prom is not None:
                promedios[curso.id] = {'promedio': prom, 'letra': nota_a_letra(prom), 'asistencia': asist, 'total_asistencias': total}

    # Pagos pendientes
    sincronizar_estado_pagos(estudiante.id)
    pagos_pendientes = PagoRealizado.query.filter_by(
        estudiante_id=estudiante.id, estado='pendiente'
    ).count()
    pagos_atrasados = PagoRealizado.query.filter_by(
        estudiante_id=estudiante.id, estado='atrasado'
    ).count()

    return render_template('dashboard_estudiante.html',
        estudiante=estudiante, cursos=cursos,
        promedios=promedios, bimestre=bimestre,
        pagos_pendientes=pagos_pendientes, pagos_atrasados=pagos_atrasados)

@app.route('/estudiante/horario')
@login_required
@role_required('alumno')
def estudiante_horario():
    estudiante = Estudiante.query.get(session['usuario_id'])
    bimestre = obtener_bimestre_actual()
    horarios = Horario.query.options(
        joinedload(Horario.curso), joinedload(Horario.docente)
    ).filter_by(seccion_id=estudiante.seccion_id).all()
    return render_template('estudiante_horario.html', horarios=horarios, dias=['Lunes','Martes','Miércoles','Jueves','Viernes'])

@app.route('/estudiante/notas')
@login_required
@role_required('alumno')
def estudiante_notas():
    estudiante = Estudiante.query.get(session['usuario_id'])
    inscripciones = Inscripcion.query.filter_by(alumno_id=estudiante.id).all()
    bimestre_id = request.args.get('bimestre_id', type=int) or (obtener_bimestre_actual().id if obtener_bimestre_actual() else None)
    bimestres = Bimestre.query.all()

    notas_por_curso = {}
    if bimestre_id and inscripciones:
        curso_ids = [ins.curso_id for ins in inscripciones]
        todas_evals = Evaluacion.query.filter(
            Evaluacion.estudiante_id == estudiante.id,
            Evaluacion.curso_id.in_(curso_ids),
            Evaluacion.bimestre_id == bimestre_id
        ).all()
        todas_asistencias = Asistencia.query.filter(
            Asistencia.estudiante_id == estudiante.id,
            Asistencia.curso_id.in_(curso_ids),
            Asistencia.bimestre_id == bimestre_id
        ).all()

        evals_idx = {}
        for ev in todas_evals:
            evals_idx.setdefault(ev.curso_id, []).append(ev)
        asistencias_idx = {}
        for a in todas_asistencias:
            asistencias_idx.setdefault(a.curso_id, []).append(a)

        pesos = {'cuaderno': 0.10, 'libro': 0.10, 'practicas': 0.20, 'exposiciones': 0.10, 'examen': 0.50}
        for ins in inscripciones:
            prom, asist, total = _calcular_promedio_desde_datos(
                evals_idx.get(ins.curso_id, []), asistencias_idx.get(ins.curso_id, []), pesos
            )
            notas_por_curso[ins.curso_id] = {
                'curso': ins.curso,
                'promedio': prom,
                'letra': nota_a_letra(prom),
                'asistencia': asist
            }
    return render_template('estudiante_notas.html', notas=notas_por_curso, bimestre_id=bimestre_id, bimestres=bimestres)

@app.route('/estudiante/asistencia', methods=['GET', 'POST'])
@login_required
@role_required('alumno')
def estudiante_asistencia():
    estudiante = Estudiante.query.get(session['usuario_id'])
    bimestre_id = request.form.get('bimestre_id', type=int) or request.args.get('bimestre_id', type=int) or (obtener_bimestre_actual().id if obtener_bimestre_actual() else None)

    if request.method == 'POST':
        asistencia_id = int(request.form.get('asistencia_id'))
        motivo = request.form.get('motivo')
        j = Justificacion(asistencia_id=asistencia_id, estudiante_id=estudiante.id, motivo=motivo)
        db.session.add(j); db.session.commit()
        flash('Justificación enviada', 'success')
        return redirect(url_for('estudiante_asistencia', bimestre_id=bimestre_id))

    asistencias = Asistencia.query.options(
        joinedload(Asistencia.curso)
    ).filter_by(estudiante_id=estudiante.id, bimestre_id=bimestre_id).order_by(Asistencia.fecha.desc()).all()
    justificadas = {j.asistencia_id for j in Justificacion.query.filter_by(estudiante_id=estudiante.id).all()}
    return render_template('estudiante_asistencia.html',
        asistencias=asistencias, bimestre_id=bimestre_id,
        bimestres=Bimestre.query.all(), justificadas=justificadas)

@app.route('/estudiante/comentarios')
@login_required
@role_required('alumno')
def estudiante_comentarios():
    estudiante = Estudiante.query.get(session['usuario_id'])
    comentarios = Comentario.query.options(
        joinedload(Comentario.docente)
    ).filter_by(estudiante_id=estudiante.id).order_by(Comentario.fecha_creacion.desc()).all()
    return render_template('estudiante_comentarios.html', comentarios=comentarios)

@app.route('/estudiante/pagos')
@login_required
@role_required('alumno')
def estudiante_pagos():
    estudiante = Estudiante.query.get(session['usuario_id'])
    sincronizar_estado_pagos(estudiante.id)
    pagos = PagoRealizado.query.options(
        joinedload(PagoRealizado.plan)
    ).filter_by(estudiante_id=estudiante.id).all()
    planes = PagoPlan.query.filter_by(activo=True).all()
    return render_template('estudiante_pagos.html', pagos=pagos, planes=planes, estudiante=estudiante)

# ====================== ERROR HANDLERS ======================
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Error interno del servidor'), 500

if __name__ == '__main__':
    app.run(debug=True)
