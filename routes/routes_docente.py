from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from db import db
from models import (
    MensajeContacto, Colaborador, Rol, Usuario, UsuarioRol,
    LogAcceso, IntentoLogin, Baneo, Estudiante, Familiar,
    EstudianteFamiliar, PeriodoAcademico, Nivel, Grado, Seccion,
    Curso, AulaAsignada, Matricula, Inscripcion, AsignacionDocente,
    Asistencia, Justificacion, Evaluacion, Calificacion,
    SeguimientoEstudiante, CarpetaDocente, DocumentoDocente,
    PagoPlan, Pago
)
from functools import wraps
from werkzeug.utils import secure_filename
import uuid, os

docente_bp = Blueprint('docente', __name__, url_prefix='/docente')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')

# ---------------------------------------------------------------------------
# Decoradores
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class BimestreSimple:
    def __init__(self, id, nombre):
        self.id = id
        self.nombre = nombre

def _bimestres_disponibles():
    bloques = db.session.query(Evaluacion.bimestre_bloque).distinct().order_by(Evaluacion.bimestre_bloque).all()
    if bloques:
        return [BimestreSimple(b[0], f'{b[0]}° Bimestre') for b in bloques]
    return [BimestreSimple(i, f'{i}° Bimestre') for i in range(1, 5)]

def _autorizar_asignacion(curso_id):
    usuario_id = session['usuario_id']
    ad = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.seccion).joinedload(Seccion.grado).joinedload(Grado.nivel),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.periodo)
    ).filter(
        AsignacionDocente.id_profesor == usuario_id,
        AsignacionDocente.id_curso == curso_id
    ).first()
    if not ad:
        flash('No tienes permiso para este curso', 'danger')
        return None, None, redirect(url_for('docente.dashboard'))
    ad.curso.nombre = ad.curso.nombre_curso
    if ad.aula and ad.aula.seccion:
        ad.curso.grado_rel = ad.aula.seccion.grado
        ad.curso.seccion_rel = ad.aula.seccion
    return ad, ad.curso, None

def _inscripciones_por_aula(aula_id):
    return Inscripcion.query.options(
        joinedload(Inscripcion.matricula).joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador),
        joinedload(Inscripcion.asistencias),
        joinedload(Inscripcion.calificaciones)
    ).filter(
        Inscripcion.id_aula_asignada == aula_id,
        Inscripcion.estado_inscripcion == 'Asignado'
    ).all()

def _adaptar_estudiante(est):
    col = est.colaborador
    est.id = est.id_colaborador
    est.dni = col.numero_documento
    est.nombre_completo = col.nombre_completo
    est.nombres = col.nombres
    partes = col.apellidos.split(' ', 1)
    est.apellido_paterno = partes[0] if partes else col.apellidos
    est.apellido_materno = partes[1] if len(partes) > 1 else ''
    est.correo = ''
    return est

def _adaptar_estudiante_lista(inscripciones):
    for ins in inscripciones:
        _adaptar_estudiante(ins.matricula.estudiante)
    return [ins.matricula.estudiante for ins in inscripciones]

def _nota_a_letra(nota):
    if nota is None:
        return '-'
    if nota >= 18:
        return 'AD'
    if nota >= 16:
        return 'A'
    if nota >= 12:
        return 'B'
    return 'C'

# ---------------------------------------------------------------------------
# 1. Dashboard
# ---------------------------------------------------------------------------

@docente_bp.route('/dashboard')
@login_required
@role_required('docente')
def dashboard():
    usuario_id = session['usuario_id']

    asignaciones = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.seccion).joinedload(Seccion.grado).joinedload(Grado.nivel),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.periodo)
    ).filter(AsignacionDocente.id_profesor == usuario_id).all()

    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones = Seccion.query.all()

    cursos = []
    estudiantes_por_curso = {}
    total_estudiantes = 0

    for ad in asignaciones:
        curso = ad.curso
        curso.nombre = curso.nombre_curso
        curso.grado_rel = ad.aula.seccion.grado if ad.aula and ad.aula.seccion else None
        curso.seccion_rel = ad.aula.seccion if ad.aula else None
        cursos.append(curso)

        inscripciones = Inscripcion.query.options(
            joinedload(Inscripcion.matricula).joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador)
        ).filter(
            Inscripcion.id_aula_asignada == ad.id_aula_asignada,
            Inscripcion.estado_inscripcion == 'Asignado'
        ).all()

        ests = []
        for ins in inscripciones:
            e = ins.matricula.estudiante
            _adaptar_estudiante(e)
            ests.append(e)
        estudiantes_por_curso[curso.id] = ests
        total_estudiantes += len(ests)

    docente_col = Colaborador.query.get(usuario_id)
    if docente_col:
        partes = docente_col.apellidos.split(' ', 1)
        docente_col.apellido_paterno = partes[0] if partes else docente_col.apellidos
        docente_col.apellido_materno = partes[1] if len(partes) > 1 else ''

    bimestres = _bimestres_disponibles()

    return render_template('dashboard_docente.html',
        docente=docente_col,
        cursos=cursos,
        total_estudiantes=total_estudiantes,
        niveles=niveles,
        grados=grados,
        secciones=secciones,
        bimestres=bimestres,
        horarios=[],
        solicitudes=[],
        estudiantes_por_curso=estudiantes_por_curso)

# ---------------------------------------------------------------------------
# 2. Evaluaciones (listar y crear evaluaciones del curso)
# ---------------------------------------------------------------------------

@docente_bp.route('/cursos/<uuid:curso_id>/evaluaciones', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def evaluaciones_curso(curso_id):
    ad, curso, error = _autorizar_asignacion(curso_id)
    if error:
        return error

    bimestre_bloque = request.args.get('bimestre', type=int) or 1

    if request.method == 'POST':
        accion = request.form.get('accion', 'crear')
        try:
            if accion == 'crear':
                evaluacion = Evaluacion(
                    id_asignacion_docente=ad.id,
                    nombre_evaluacion=request.form.get('nombre_evaluacion', '').strip(),
                    bimestre_bloque=int(request.form.get('bimestre_bloque', bimestre_bloque)),
                    porcentaje_peso=float(request.form.get('porcentaje_peso', 0)),
                    fecha_limite=datetime.strptime(request.form.get('fecha_limite'), '%Y-%m-%d').date()
                )
                db.session.add(evaluacion)
                db.session.commit()
                flash('Evaluación creada correctamente', 'success')

            elif accion == 'editar':
                ev = Evaluacion.query.get(request.form.get('evaluacion_id'))
                if ev and ev.id_asignacion_docente == ad.id:
                    ev.nombre_evaluacion = request.form.get('nombre_evaluacion', ev.nombre_evaluacion)
                    ev.bimestre_bloque = int(request.form.get('bimestre_bloque', ev.bimestre_bloque))
                    ev.porcentaje_peso = float(request.form.get('porcentaje_peso', ev.porcentaje_peso))
                    ev.fecha_limite = datetime.strptime(request.form.get('fecha_limite'), '%Y-%m-%d').date()
                    db.session.commit()
                    flash('Evaluación actualizada', 'success')

            elif accion == 'eliminar':
                ev = Evaluacion.query.get(request.form.get('evaluacion_id'))
                if ev and ev.id_asignacion_docente == ad.id:
                    Calificacion.query.filter_by(id_evaluacion=ev.id).delete()
                    db.session.delete(ev)
                    db.session.commit()
                    flash('Evaluación eliminada', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar evaluación: {str(e)}', 'danger')

        return redirect(url_for('docente.evaluaciones_curso', curso_id=curso_id))

    evaluaciones = Evaluacion.query.filter(
        Evaluacion.id_asignacion_docente == ad.id,
        Evaluacion.bimestre_bloque == bimestre_bloque
    ).order_by(Evaluacion.fecha_limite).all()

    inscripciones = _inscripciones_por_aula(ad.id_aula_asignada)
    estudiantes = _adaptar_estudiante_lista(inscripciones)

    ev_ids = [ev.id for ev in evaluaciones]
    ids_insc = [ins.id for ins in inscripciones]

    calificaciones = Calificacion.query.filter(
        Calificacion.id_inscripcion.in_(ids_insc),
        Calificacion.id_evaluacion.in_(ev_ids)
    ).all() if ev_ids and ids_insc else []

    calif_idx = {}
    for c in calificaciones:
        calif_idx[(c.id_inscripcion, c.id_evaluacion)] = c

    evals_dict = {}
    for est in estudiantes:
        eid = est.id_colaborador
        ins = None
        for i in inscripciones:
            if i.matricula.estudiante.id_colaborador == eid:
                ins = i
                break
        if ins:
            evals_dict[eid] = {}
            for ev in evaluaciones:
                c = calif_idx.get((ins.id, ev.id))
                if c is not None:
                    evals_dict[eid][ev.nombre_evaluacion] = c.nota

    bimestres = _bimestres_disponibles()

    def calcular_promedio_bimestre(est_id, c_id, bim_id):
        for ins in inscripciones:
            if ins.matricula.estudiante.id_colaborador != est_id:
                continue
            peso_total = sum(float(ev.porcentaje_peso) for ev in evaluaciones) or 1
            suma_ponderada = 0.0
            tiene_notas = False
            for ev in evaluaciones:
                c = calif_idx.get((ins.id, ev.id))
                if c is not None and c.nota is not None:
                    suma_ponderada += float(c.nota) * float(ev.porcentaje_peso)
                    tiene_notas = True
            if tiene_notas:
                return (round(suma_ponderada / peso_total, 2),)
            return (None,)
        return (None,)

    return render_template('evaluaciones.html',
        curso=curso,
        estudiantes=estudiantes,
        evaluaciones=evaluaciones,
        bimestre_id=bimestre_bloque,
        bimestres=bimestres,
        evals=evals_dict,
        calcular_promedio_bimestre=calcular_promedio_bimestre)

# ---------------------------------------------------------------------------
# 3. Calificaciones (ingreso de notas por evaluación)
# ---------------------------------------------------------------------------

@docente_bp.route('/cursos/<uuid:curso_id>/calificaciones', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def calificaciones_curso(curso_id):
    ad, curso, error = _autorizar_asignacion(curso_id)
    if error:
        return error

    evaluacion_id = request.args.get('evaluacion_id', type=uuid.UUID)
    bimestre_bloque = request.args.get('bimestre', type=int) or 1

    if request.method == 'POST':
        try:
            ev_id = request.form.get('evaluacion_id')
            inscripciones = _inscripciones_por_aula(ad.id_aula_asignada)
            for ins in inscripciones:
                nota_raw = request.form.get(f'nota_{ins.id}')
                if nota_raw is not None and nota_raw.strip() != '':
                    nota_val = float(nota_raw)
                    if 0 <= nota_val <= 20:
                        existing = Calificacion.query.filter_by(
                            id_inscripcion=ins.id,
                            id_evaluacion=ev_id
                        ).first()
                        if existing:
                            existing.nota = nota_val
                            existing.fecha_actualizacion = datetime.utcnow()
                        else:
                            cal = Calificacion(
                                id_inscripcion=ins.id,
                                id_evaluacion=ev_id,
                                nota=nota_val,
                                comentarios=request.form.get(f'comentarios_{ins.id}', '')
                            )
                            db.session.add(cal)
                    else:
                        flash(f'La nota debe estar entre 0 y 20', 'warning')
            db.session.commit()
            flash('Calificaciones guardadas correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar calificaciones: {str(e)}', 'danger')
        return redirect(url_for('docente.calificaciones_curso', curso_id=curso_id))

    evaluaciones = Evaluacion.query.filter(
        Evaluacion.id_asignacion_docente == ad.id,
        Evaluacion.bimestre_bloque == bimestre_bloque
    ).order_by(Evaluacion.nombre_evaluacion).all()

    if not evaluacion_id and evaluaciones:
        evaluacion_id = evaluaciones[0].id

    inscripciones = _inscripciones_por_aula(ad.id_aula_asignada)
    estudiantes = _adaptar_estudiante_lista(inscripciones)

    calificaciones = {}
    if evaluacion_id:
        califs = Calificacion.query.filter(Calificacion.id_evaluacion == evaluacion_id).all()
        for c in califs:
            calificaciones[c.id_inscripcion] = c

    evaluacion_actual = Evaluacion.query.get(evaluacion_id) if evaluacion_id else None

    bimestres = _bimestres_disponibles()

    return render_template('estudiante_notas.html',
        curso=curso,
        estudiantes=estudiantes,
        inscripciones=inscripciones,
        evaluaciones=evaluaciones,
        evaluacion_actual=evaluacion_actual,
        calificaciones=calificaciones,
        bimestre_id=bimestre_bloque,
        bimestres=bimestres)

# ---------------------------------------------------------------------------
# 4. Asistencia
# ---------------------------------------------------------------------------

@docente_bp.route('/cursos/<uuid:curso_id>/asistencia', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def asistencia_curso(curso_id):
    ad, curso, error = _autorizar_asignacion(curso_id)
    if error:
        return error

    fecha_str = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    try:
        fecha_asistencia = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_asistencia = date.today()
        fecha_str = fecha_asistencia.strftime('%Y-%m-%d')

    inscripciones = _inscripciones_por_aula(ad.id_aula_asignada)
    estudiantes = _adaptar_estudiante_lista(inscripciones)
    est_insc_map = {ins.matricula.estudiante.id_colaborador: ins.id for ins in inscripciones}

    if request.method == 'POST':
        try:
            for key, value in request.form.items():
                if key.startswith('estado_'):
                    est_id_str = key.replace('estado_', '')
                    try:
                        est_id = uuid.UUID(est_id_str)
                    except ValueError:
                        continue
                    ins_id = est_insc_map.get(est_id)
                    if not ins_id:
                        continue
                    estado = value.upper()
                    if estado not in ('P', 'A', 'T', 'J'):
                        estado = 'P'

                    existing = Asistencia.query.filter_by(
                        id_inscripcion=ins_id,
                        fecha_asistencia=fecha_asistencia
                    ).first()
                    if existing:
                        existing.estado_asistencia = estado
                    else:
                        asis = Asistencia(
                            id_inscripcion=ins_id,
                            fecha_asistencia=fecha_asistencia,
                            estado_asistencia=estado
                        )
                        db.session.add(asis)
            db.session.commit()
            flash('Asistencia guardada correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar asistencia: {str(e)}', 'danger')
        return redirect(url_for('docente.asistencia_curso', curso_id=curso_id, fecha=fecha_str))

    asistencias = {}
    ids_insc = list(est_insc_map.values())
    asis_records = Asistencia.query.filter(
        Asistencia.id_inscripcion.in_(ids_insc),
        Asistencia.fecha_asistencia == fecha_asistencia
    ).all() if ids_insc else []

    ins_est_map = {ins_id: est_id for est_id, ins_id in est_insc_map.items()}
    for a in asis_records:
        est_id = ins_est_map.get(a.id_inscripcion)
        if est_id:
            asistencias[est_id] = a.estado_asistencia

    bimestres = _bimestres_disponibles()

    return render_template('asistencia.html',
        curso=curso,
        estudiantes=estudiantes,
        fecha=fecha_str,
        asistencias=asistencias,
        bimestre_id=1,
        bimestres=bimestres)

# ---------------------------------------------------------------------------
# 5. Listado de estudiantes con resumen de notas
# ---------------------------------------------------------------------------

@docente_bp.route('/cursos/<uuid:curso_id>/estudiantes')
@login_required
@role_required('docente')
def estudiantes_curso(curso_id):
    ad, curso, error = _autorizar_asignacion(curso_id)
    if error:
        return error

    inscripciones = _inscripciones_por_aula(ad.id_aula_asignada)
    estudiantes = _adaptar_estudiante_lista(inscripciones)
    ids_insc = [ins.id for ins in inscripciones]

    evaluaciones = Evaluacion.query.filter(
        Evaluacion.id_asignacion_docente == ad.id
    ).all()
    ev_ids = [ev.id for ev in evaluaciones]

    calificaciones = Calificacion.query.filter(
        Calificacion.id_evaluacion.in_(ev_ids),
        Calificacion.id_inscripcion.in_(ids_insc)
    ).all() if ev_ids and ids_insc else []

    peso_por_ev = {ev.id: float(ev.porcentaje_peso) for ev in evaluaciones}
    total_peso = sum(peso_por_ev.values()) or 100

    notas_por_insc = {}
    for c in calificaciones:
        notas_por_insc.setdefault(c.id_inscripcion, []).append(c)

    notas = {}
    for ins in inscripciones:
        eid = ins.matricula.estudiante.id_colaborador
        cals = notas_por_insc.get(ins.id, [])
        if cals and total_peso > 0:
            ponderado = sum(float(c.nota) * (peso_por_ev.get(c.id_evaluacion, 0) / total_peso) for c in cals)
            promedio = round(ponderado, 2)
        else:
            promedio = None

        asistencias = Asistencia.query.filter(Asistencia.id_inscripcion == ins.id).all()
        total_asist = len(asistencias)
        presentes = sum(1 for a in asistencias if a.estado_asistencia == 'P')
        pct_asistencia = round((presentes / total_asist * 100), 1) if total_asist > 0 else None

        notas[eid] = {
            'curso': curso,
            'promedio': promedio,
            'letra': _nota_a_letra(promedio) if promedio is not None else '-',
            'asistencia': pct_asistencia or 0
        }

    bimestres = _bimestres_disponibles()

    return render_template('estudiante_notas.html',
        curso=curso,
        estudiantes=estudiantes,
        notas=notas,
        bimestre_id=1,
        bimestres=bimestres)

# ---------------------------------------------------------------------------
# 6. Carpeta / Documentos
# ---------------------------------------------------------------------------

@docente_bp.route('/carpeta', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def carpeta():
    usuario_id = session['usuario_id']

    asignaciones = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.seccion).joinedload(Seccion.grado),
        joinedload(AsignacionDocente.carpeta)
    ).filter(AsignacionDocente.id_profesor == usuario_id).all()

    if request.method == 'POST':
        try:
            ad_id = request.form.get('asignacion_id')
            if not ad_id:
                flash('Selecciona una asignación', 'danger')
                return redirect(url_for('docente.carpeta'))

            ad_obj = AsignacionDocente.query.get(ad_id)
            if not ad_obj or ad_obj.id_profesor != usuario_id:
                flash('Asignación no válida', 'danger')
                return redirect(url_for('docente.carpeta'))

            carpeta = CarpetaDocente.query.filter_by(id_asignacion_docente=ad_id).first()
            if not carpeta:
                nombre = ad_obj.curso.nombre_curso
                if ad_obj.aula and ad_obj.aula.seccion:
                    nombre += f' - {ad_obj.aula.seccion.grado.nombre_grado} {ad_obj.aula.seccion.nombre_seccion}'
                carpeta = CarpetaDocente(
                    id_asignacion_docente=ad_id,
                    nombre_carpeta=nombre
                )
                db.session.add(carpeta)
                db.session.flush()

            archivo = request.files.get('archivo')
            if archivo and archivo.filename:
                ALLOWED = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'txt'}
                ext = archivo.filename.rsplit('.', 1)[1].lower() if '.' in archivo.filename else ''
                if ext not in ALLOWED:
                    flash('Tipo de archivo no permitido. Extensiones: pdf, doc, docx, xls, xlsx, jpg, png, txt', 'danger')
                    return redirect(url_for('docente.carpeta'))

                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filename = f"{uuid.uuid4().hex}_{secure_filename(archivo.filename)}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                archivo.save(filepath)

                doc = DocumentoDocente(
                    id_carpeta=carpeta.id,
                    nombre_archivo=request.form.get('titulo', archivo.filename),
                    archivo_url=f'uploads/{filename}'
                )
                db.session.add(doc)
                db.session.commit()
                flash('Documento subido correctamente', 'success')
            else:
                flash('Debes seleccionar un archivo', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al subir documento: {str(e)}', 'danger')
        return redirect(url_for('docente.carpeta'))

    carpetas_list = []
    todos_documentos = []
    for ad in asignaciones:
        carpeta = ad.carpeta
        if not carpeta:
            nombre = ad.curso.nombre_curso
            if ad.aula and ad.aula.seccion:
                nombre += f' - {ad.aula.seccion.grado.nombre_grado} {ad.aula.seccion.nombre_seccion}'
            carpeta = CarpetaDocente(
                id_asignacion_docente=ad.id,
                nombre_carpeta=nombre
            )
            db.session.add(carpeta)
            db.session.flush()
        carpeta.nombre = carpeta.nombre_carpeta
        carpetas_list.append(carpeta)

        docs = DocumentoDocente.query.filter_by(id_carpeta=carpeta.id).order_by(DocumentoDocente.fecha_subida.desc()).all()
        for d in docs:
            d.carpeta = carpeta
            d.titulo = d.nombre_archivo
            d.archivo_ruta = d.archivo_url
            d.estado = 'pendiente'
            d.comentario_revision = ''
        todos_documentos.extend(docs)

    db.session.commit()

    return render_template('documentos_docente.html',
        carpetas=carpetas_list,
        documentos=todos_documentos)

# ---------------------------------------------------------------------------
# 7. Seguimientos de estudiantes
# ---------------------------------------------------------------------------

@docente_bp.route('/seguimientos', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def seguimientos():
    usuario_id = session['usuario_id']

    asignaciones = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.seccion).joinedload(Seccion.grado)
    ).filter(AsignacionDocente.id_profesor == usuario_id).all()

    aulas_ids = [ad.id_aula_asignada for ad in asignaciones]
    inscripciones = Inscripcion.query.options(
        joinedload(Inscripcion.matricula).joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador)
    ).filter(
        Inscripcion.id_aula_asignada.in_(aulas_ids),
        Inscripcion.estado_inscripcion == 'Asignado'
    ).all() if aulas_ids else []

    if request.method == 'POST':
        try:
            ins_id = request.form.get('inscripcion_id')
            if not ins_id:
                flash('Selecciona un estudiante', 'danger')
                return redirect(url_for('docente.seguimientos'))

            ins = Inscripcion.query.get(ins_id)
            if not ins or ins.id_aula_asignada not in aulas_ids:
                flash('Estudiante no válido', 'danger')
                return redirect(url_for('docente.seguimientos'))

            seguimiento = SeguimientoEstudiante(
                id_inscripcion=ins_id,
                id_colaborador_registra=usuario_id,
                tipo_registro=request.form.get('tipo_registro', 'Académico'),
                gravedad=request.form.get('gravedad', 'Informativo'),
                descripcion=request.form.get('descripcion', ''),
                fecha_suceso=datetime.strptime(request.form.get('fecha_suceso'), '%Y-%m-%d').date() if request.form.get('fecha_suceso') else date.today()
            )
            db.session.add(seguimiento)
            db.session.commit()
            flash('Seguimiento registrado correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar seguimiento: {str(e)}', 'danger')
        return redirect(url_for('docente.seguimientos'))

    ids_insc = [ins.id for ins in inscripciones]
    todos_seguimientos = SeguimientoEstudiante.query.options(
        joinedload(SeguimientoEstudiante.inscripcion).joinedload(Inscripcion.matricula).joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador),
        joinedload(SeguimientoEstudiante.registrador)
    ).filter(
        SeguimientoEstudiante.id_inscripcion.in_(ids_insc)
    ).order_by(SeguimientoEstudiante.fecha_registro.desc()).all() if ids_insc else []

    estudiantes_data = []
    for ins in inscripciones:
        est = ins.matricula.estudiante
        _adaptar_estudiante(est)
        aula_label = ''
        for ad in asignaciones:
            if ad.id_aula_asignada == ins.id_aula_asignada:
                aula_label = f'{ad.curso.nombre_curso} - {ad.aula.seccion.grado.nombre_grado} {ad.aula.seccion.nombre_seccion}'
                break
        estudiantes_data.append({
            'inscripcion_id': ins.id,
            'estudiante': est,
            'aula': aula_label
        })

    return render_template('estudiante_comentarios.html',
        estudiantes=estudiantes_data,
        seguimientos=todos_seguimientos,
        asignaciones=asignaciones)

# ---------------------------------------------------------------------------
# 8. Reportes
# ---------------------------------------------------------------------------

@docente_bp.route('/reportes')
@login_required
@role_required('docente')
def reportes():
    usuario_id = session['usuario_id']

    asignaciones = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.seccion).joinedload(Seccion.grado).joinedload(Grado.nivel),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.periodo)
    ).filter(AsignacionDocente.id_profesor == usuario_id).all()

    reportes = []
    for ad in asignaciones:
        total_insc = Inscripcion.query.filter(
            Inscripcion.id_aula_asignada == ad.id_aula_asignada,
            Inscripcion.estado_inscripcion == 'Asignado'
        ).count()

        total_evs = Evaluacion.query.filter(
            Evaluacion.id_asignacion_docente == ad.id
        ).count()

        ids_sub = db.session.query(Inscripcion.id).filter(
            Inscripcion.id_aula_asignada == ad.id_aula_asignada,
            Inscripcion.estado_inscripcion == 'Asignado'
        ).subquery()

        asistencias_hoy = Asistencia.query.filter(
            Asistencia.id_inscripcion.in_(ids_sub),
            Asistencia.fecha_asistencia == date.today()
        ).all()
        total_asist = len(asistencias_hoy)
        presentes = sum(1 for a in asistencias_hoy if a.estado_asistencia == 'P')
        pct_asist = round((presentes / total_asist * 100), 1) if total_asist > 0 else None

        califs = db.session.query(func.avg(Calificacion.nota)).join(
            Evaluacion, Evaluacion.id == Calificacion.id_evaluacion
        ).filter(
            Evaluacion.id_asignacion_docente == ad.id,
            Calificacion.id_inscripcion.in_(ids_sub)
        ).scalar()
        promedio_general = round(float(califs), 2) if califs else None

        reportes.append({
            'curso': ad.curso.nombre_curso,
            'grado': ad.aula.seccion.grado.nombre_grado if ad.aula and ad.aula.seccion else '-',
            'seccion': ad.aula.seccion.nombre_seccion if ad.aula and ad.aula.seccion else '-',
            'periodo': ad.aula.periodo.nombre_periodo if ad.aula and ad.aula.periodo else '-',
            'total_estudiantes': total_insc,
            'total_evaluaciones': total_evs,
            'asistencia_hoy_pct': pct_asist,
            'presentes_hoy': presentes,
            'ausentes_hoy': total_asist - presentes,
            'total_asistencia_hoy': total_asist,
            'promedio_general': promedio_general
        })

    docente_col = Colaborador.query.get(usuario_id)
    if docente_col:
        partes = docente_col.apellidos.split(' ', 1)
        docente_col.apellido_paterno = partes[0] if partes else docente_col.apellidos
        docente_col.apellido_materno = partes[1] if len(partes) > 1 else ''

    return render_template('dashboard_docente.html',
        docente=docente_col,
        cursos=[],
        reportes_data=reportes,
        total_estudiantes=sum(r['total_estudiantes'] for r in reportes),
        niveles=[],
        grados=[],
        secciones=[],
        bimestres=_bimestres_disponibles(),
        horarios=[],
        solicitudes=[],
        estudiantes_por_curso={})


@docente_bp.route('/api/asistencia_estudiantes', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def api_asistencia_estudiantes():
    if request.method == 'GET':
        seccion_id = request.args.get('seccion_id')
        fecha = request.args.get('fecha', date.today().isoformat())
        inscripciones = Inscripcion.query.filter(
            Inscripcion.id_aula_asignada == seccion_id,
            Inscripcion.estado_inscripcion == 'Asignado'
        ).options(
            joinedload(Inscripcion.matricula).joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador)
        ).all()
        result = []
        for ins in inscripciones:
            asist = Asistencia.query.filter_by(id_inscripcion=ins.id, fecha_asistencia=fecha).first()
            result.append({
                'id_inscripcion': str(ins.id),
                'estudiante': ins.matricula.estudiante.colaborador.nombre_completo if ins.matricula and ins.matricula.estudiante and ins.matricula.estudiante.colaborador else '-',
                'asistencia_id': str(asist.id) if asist else None,
                'estado': asist.estado_asistencia if asist else 'SIN_REGISTRO'
            })
        return jsonify(result)
    data = request.get_json() or {}
    inscripcion_id = data.get('inscripcion_id')
    fecha = data.get('fecha', date.today().isoformat())
    estado = data.get('estado', 'P')
    asist = Asistencia.query.filter_by(id_inscripcion=inscripcion_id, fecha_asistencia=fecha).first()
    if asist:
        asist.estado_asistencia = estado
    else:
        asist = Asistencia(id_inscripcion=inscripcion_id, fecha_asistencia=fecha, estado_asistencia=estado)
        db.session.add(asist)
    db.session.commit()
    return jsonify({'success': True})


@docente_bp.route('/api/evaluaciones', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def api_evaluaciones():
    if request.method == 'GET':
        curso_id = request.args.get('curso_id')
        bimestre_id = request.args.get('bimestre_id')
        query = Evaluacion.query
        if curso_id:
            query = query.filter_by(id_asignacion_docente=curso_id)
        if bimestre_id:
            query = query.filter_by(id_bimestre=bimestre_id)
        evals = query.all()
        return jsonify([{
            'id': str(e.id),
            'nombre': e.nombre_evaluacion,
            'tipo': e.tipo_evaluacion,
            'peso': e.peso_porcentaje,
            'fecha': e.fecha_evaluacion.isoformat() if e.fecha_evaluacion else ''
        } for e in evals])
    data = request.get_json() or {}
    eval = Evaluacion(
        id_asignacion_docente=data.get('curso_id'),
        nombre_evaluacion=data.get('nombre', 'Evaluacion'),
        tipo_evaluacion=data.get('tipo', 'practica'),
        peso_porcentaje=data.get('peso', 0),
        fecha_evaluacion=data.get('fecha')
    )
    db.session.add(eval)
    db.session.commit()
    return jsonify({'success': True, 'id': str(eval.id)})


@docente_bp.route('/descargar_plantilla_notas')
@login_required
@role_required('docente')
def descargar_plantilla_notas():
    flash('Descarga de plantilla en desarrollo', 'info')
    return redirect(url_for('docente.dashboard'))


@docente_bp.route('/importar_notas_excel', methods=['POST'])
@login_required
@role_required('docente')
def importar_notas_excel():
    flash('Importacion de notas en desarrollo', 'info')
    return redirect(url_for('docente.dashboard'))


@docente_bp.route('/comentarios', methods=['GET', 'POST'])
@login_required
@role_required('docente')
def comentarios():
    usuario_id = session['usuario_id']
    from models import SeguimientoEstudiante, Inscripcion, Matricula, Estudiante
    if request.method == 'POST':
        contenido = request.form.get('contenido', '')
        tipo = request.form.get('tipo', 'neutral')
        estudiante_id = request.form.get('estudiante_id')
        bimestre_id = request.form.get('bimestre_id')
        if contenido and estudiante_id:
            insc = Inscripcion.query.join(Matricula).filter(
                Matricula.id_estudiante == estudiante_id
            ).first()
            if insc:
                seg = SeguimientoEstudiante(
                    id_inscripcion=insc.id,
                    id_registrador=usuario_id,
                    tipo_seguimiento=tipo,
                    descripcion=contenido,
                    fecha_registro=datetime.utcnow()
                )
                db.session.add(seg)
                db.session.commit()
                flash('Comentario guardado', 'success')
            else:
                flash('Estudiante no encontrado en inscripciones', 'danger')
        return redirect(url_for('docente.comentarios'))

    asignaciones = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula).joinedload(AulaAsignada.seccion).joinedload(Seccion.grado).joinedload(Grado.nivel),
    ).filter(AsignacionDocente.id_profesor == usuario_id).all()

    seguimientos = SeguimientoEstudiante.query.options(
        joinedload(SeguimientoEstudiante.inscripcion)
    ).filter(
        SeguimientoEstudiante.id_registrador == usuario_id
    ).order_by(SeguimientoEstudiante.fecha_registro.desc()).limit(50).all()

    return render_template('comentarios_docente.html',
        cursos=[a.curso for a in asignaciones if a.curso],
        comentarios=seguimientos,
        bimestres=[],
        estudiantes=[])
