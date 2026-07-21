from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from db import db
from models import (
    Colaborador, Estudiante, Familiar, EstudianteFamiliar,
    PeriodoAcademico, Nivel, Grado, Seccion, Curso,
    AulaAsignada, Matricula, Inscripcion, AsignacionDocente,
    Asistencia, Justificacion, Evaluacion, Calificacion,
    SeguimientoEstudiante, PagoPlan, Pago, Usuario
)
from functools import wraps
from types import SimpleNamespace
import os

estudiante_bp = Blueprint('estudiante', __name__, url_prefix='/estudiante')

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

def nota_a_letra(nota):
    if nota is None: return '-'
    if nota >= 18: return 'AD'
    if nota >= 16: return 'A'
    if nota >= 14: return 'B'
    return 'C'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')


def _obtener_matricula_activa(estudiante_id):
    return Matricula.query.options(
        joinedload(Matricula.periodo)
    ).filter_by(
        id_estudiante=estudiante_id,
        estado_matricula='Activo'
    ).order_by(Matricula.fecha_matricula.desc()).first()


def _obtener_cursos_por_aula(aula_id):
    aulas = AulaAsignada.query.options(
        joinedload(AulaAsignada.seccion).joinedload(Seccion.grado),
        joinedload(AulaAsignada.periodo),
    ).filter_by(id=aula_id).all()
    result = []
    for aula in aulas:
        seccion = aula.seccion
        grado = seccion.grado if seccion else None
        nivel = grado.nivel if grado else None
        asignaciones = AsignacionDocente.query.options(
            joinedload(AsignacionDocente.curso),
            joinedload(AsignacionDocente.profesor).joinedload(Usuario.colaborador),
        ).filter_by(id_aula_asignada=aula.id).all()
        for asig in asignaciones:
            if asig.curso:
                result.append((asig.curso, asig, aula, seccion, grado, nivel))
    return result


def _curso_simple(curso, asig, seccion, grado, nivel):
    prof = asig.profesor
    docente_nombre = prof.colaborador.nombre_completo if (prof and hasattr(prof, 'colaborador') and prof.colaborador) else 'Sin asignar'
    return SimpleNamespace(
        id=str(curso.id),
        nombre=curso.nombre_curso,
        codigo=curso.nombre_curso[:4].upper(),
        activo=curso.estado_curso == 'Activo',
        docente=SimpleNamespace(nombre_completo=docente_nombre),
        grado_rel=SimpleNamespace(nombre=grado.nombre_grado) if grado else None,
        seccion_rel=SimpleNamespace(nombre=seccion.nombre_seccion) if seccion else None,
    )


def _periodo_simple(pa):
    return SimpleNamespace(id=str(pa.id), nombre=pa.nombre_periodo)


def _calcular_promedio_y_evals(inscripciones):
    promedios = {}
    evaluaciones_por_curso = {}
    for ins in inscripciones:
        cursos_data = _obtener_cursos_por_aula(ins.id_aula_asignada)
        for curso, asig, aula, seccion, grado, nivel in cursos_data:
            cid = str(curso.id)
            evals_curso = {}
            total_peso = 0.0
            suma_pond = 0.0
            for cal in ins.calificaciones:
                ev = cal.evaluacion
                if ev and str(ev.id_asignacion_docente) == str(asig.id):
                    peso = float(ev.porcentaje_peso)
                    nota = float(cal.nota)
                    evals_curso[ev.nombre_evaluacion] = {
                        'nota': nota,
                        'peso': peso,
                        'comentarios': cal.comentarios,
                    }
                    suma_pond += nota * peso
                    total_peso += peso
            evaluaciones_por_curso[cid] = evals_curso
            prom = round(suma_pond / total_peso, 2) if total_peso > 0 else None
            if prom is not None:
                promedios[cid] = {
                    'promedio': prom,
                    'letra': nota_a_letra(prom),
                    'asistencia': None,
                    'total_asistencias': 0,
                }
    return promedios, evaluaciones_por_curso


@estudiante_bp.route('/dashboard')
@login_required
@role_required('alumno')
def dashboard():
    uid = session['usuario_id']
    estudiante = Estudiante.query.get(uid)
    if not estudiante:
        flash('Perfil de estudiante no encontrado', 'danger')
        return render_template('error.html', error='No se encontró el perfil del estudiante')

    colaborador = Colaborador.query.get(uid)
    matricula = _obtener_matricula_activa(uid)

    periodos = PeriodoAcademico.query.order_by(PeriodoAcademico.fecha_inicio.desc()).all()
    periodo_activo = next((p for p in periodos if p.estado_activo), periodos[0] if periodos else None)
    periodo_id = request.args.get('bimestre_id') or (str(periodo_activo.id) if periodo_activo else None)
    selected_periodo = next((p for p in periodos if str(p.id) == periodo_id), periodo_activo)

    cursos = []
    promedios = {}
    evaluaciones_por_curso = {}
    asistencias = []
    justificadas = set()
    pagos = []
    inscripciones = []

    if matricula:
        inscripciones = Inscripcion.query.options(
            joinedload(Inscripcion.calificaciones).joinedload(Calificacion.evaluacion),
            joinedload(Inscripcion.asistencias).joinedload(Asistencia.justificacion),
        ).filter_by(id_matricula=matricula.id).all()

        promedios, evaluaciones_por_curso = _calcular_promedio_y_evals(inscripciones)

        curso_nombre_map = {}
        for ins in inscripciones:
            cursos_data = _obtener_cursos_por_aula(ins.id_aula_asignada)
            for curso, asig, aula, seccion, grado, nivel in cursos_data:
                cid = str(curso.id)
                if cid not in curso_nombre_map:
                    curso_nombre_map[cid] = curso.nombre_curso
                cobj = _curso_simple(curso, asig, seccion, grado, nivel)
                if not any(c.id == cid for c in cursos):
                    cursos.append(cobj)

            for a in ins.asistencias:
                cursos_data2 = _obtener_cursos_por_aula(ins.id_aula_asignada)
                nom_curso = cursos_data2[0][0].nombre_curso if cursos_data2 else 'General'
                asis = SimpleNamespace(
                    id=str(a.id),
                    fecha=a.fecha_asistencia,
                    estado=a.estado_asistencia,
                    curso=SimpleNamespace(nombre=nom_curso),
                )
                asistencias.append(asis)
                if a.justificacion:
                    justificadas.add(str(a.id))

        asistencias.sort(key=lambda x: x.fecha, reverse=True)

        for cid in promedios:
            nom = curso_nombre_map.get(cid, '')
            total = sum(1 for a in asistencias if a.curso.nombre == nom)
            presentes = sum(1 for a in asistencias if a.curso.nombre == nom and a.estado in ('P', 'T'))
            pct = round(presentes / total * 100, 1) if total > 0 else None
            promedios[cid]['asistencia'] = pct
            promedios[cid]['total_asistencias'] = total

        pagos_q = Pago.query.options(
            joinedload(Pago.plan),
        ).filter_by(id_matricula=matricula.id).order_by(Pago.fecha_transaccion.desc()).all()

        for p in pagos_q:
            pagos.append(SimpleNamespace(
                monto_pagado=p.monto_pagado,
                monto_mora=p.monto_mora,
                fecha_pago=p.fecha_transaccion,
                plan=SimpleNamespace(
                    nombre=p.plan.concepto_pago,
                    fecha_vencimiento=p.plan.fecha_vencimiento,
                ) if p.plan else None,
                estado='cancelado',
            ))

    bimestres_ns = [_periodo_simple(p) for p in periodos]
    bimestre_obj = _periodo_simple(selected_periodo) if selected_periodo else None
    bimestre_id_str = str(selected_periodo.id) if selected_periodo else None

    return render_template('dashboard_estudiante.html',
        estudiante=estudiante,
        cursos=cursos,
        promedios=promedios,
        evaluaciones_por_curso=evaluaciones_por_curso,
        bimestre=bimestre_obj,
        bimestre_id=bimestre_id_str,
        pagos_pendientes=0,
        pagos_atrasados=0,
        pagos=pagos,
        comentarios=[],
        asistencias=asistencias,
        justificadas=justificadas,
        bimestres=bimestres_ns,
        horarios_est=[])


@estudiante_bp.route('/notas')
@login_required
@role_required('alumno')
def notas():
    uid = session['usuario_id']
    estudiante = Estudiante.query.get(uid)
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('estudiante.dashboard'))

    periodos = PeriodoAcademico.query.order_by(PeriodoAcademico.fecha_inicio.desc()).all()
    bimestres = [_periodo_simple(p) for p in periodos]

    bimestre_bloque = request.args.get('bimestre_id', type=int)

    matricula = _obtener_matricula_activa(uid)
    notas_data = {}

    if matricula:
        inscripciones = Inscripcion.query.options(
            joinedload(Inscripcion.calificaciones).joinedload(Calificacion.evaluacion),
        ).filter_by(id_matricula=matricula.id).all()

        for ins in inscripciones:
            cursos_data = _obtener_cursos_por_aula(ins.id_aula_asignada)
            for curso, asig, aula, seccion, grado, nivel in cursos_data:
                cid = str(curso.id)
                if cid in notas_data:
                    continue

                califs = [
                    c for c in ins.calificaciones
                    if c.evaluacion and str(c.evaluacion.id_asignacion_docente) == str(asig.id)
                ]
                if bimestre_bloque:
                    califs = [c for c in califs if c.evaluacion.bimestre_bloque == bimestre_bloque]

                total_peso = 0.0
                suma_pond = 0.0
                for cal in califs:
                    peso = float(cal.evaluacion.porcentaje_peso)
                    nota = float(cal.nota)
                    suma_pond += nota * peso
                    total_peso += peso

                prom = round(suma_pond / total_peso, 2) if total_peso > 0 else None

                asistencias = Asistencia.query.filter_by(id_inscripcion=ins.id).all()
                total_asis = len(asistencias)
                presentes = sum(1 for a in asistencias if a.estado_asistencia in ('P', 'T'))
                asistencia_pct = round(presentes / total_asis * 100, 1) if total_asis > 0 else None

                notas_data[cid] = {
                    'curso': SimpleNamespace(nombre=curso.nombre_curso),
                    'promedio': prom,
                    'letra': nota_a_letra(prom),
                    'asistencia': asistencia_pct,
                }

    return render_template('estudiante_notas.html',
        notas=notas_data,
        bimestre_id=bimestre_bloque,
        bimestres=bimestres)


@estudiante_bp.route('/asistencia', methods=['GET', 'POST'])
@login_required
@role_required('alumno')
def asistencia():
    uid = session['usuario_id']
    estudiante = Estudiante.query.get(uid)
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('estudiante.dashboard'))

    periodos = PeriodoAcademico.query.order_by(PeriodoAcademico.fecha_inicio.desc()).all()
    bimestres = [_periodo_simple(p) for p in periodos]

    periodo_id = request.form.get('bimestre_id') or request.args.get('bimestre_id') or (
        str(next((p for p in periodos if p.estado_activo), periodos[0]).id) if periodos else None
    )

    if request.method == 'POST':
        from werkzeug.utils import secure_filename
        asistencia_id = request.form.get('asistencia_id')
        motivo = request.form.get('motivo', '').strip()
        archivo = request.files.get('archivo')

        if not asistencia_id:
            flash('Registro de asistencia no válido', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))
        if not motivo:
            flash('Debes escribir un motivo de justificación', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))
        if not archivo or not archivo.filename:
            flash('Debes adjuntar un archivo como evidencia', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

        ALLOWED_EXT = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'txt'}
        ext = archivo.filename.rsplit('.', 1)[1].lower() if '.' in archivo.filename else ''
        if ext not in ALLOWED_EXT:
            flash('Tipo de archivo no permitido. Extensiones: pdf, doc, docx, xls, xlsx, jpg, png, gif, txt', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

        asistencia_obj = Asistencia.query.get(asistencia_id)
        if not asistencia_obj:
            flash('Registro de asistencia no encontrado', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

        familiar = Familiar.query.filter_by(id_colaborador=uid).first()
        if not familiar:
            familiar = Familiar.query.join(
                EstudianteFamiliar, EstudianteFamiliar.id_familiar == Familiar.id_colaborador
            ).filter(
                EstudianteFamiliar.id_estudiante == uid,
                EstudianteFamiliar.es_apoderado_legal.is_(True),
            ).first()
        if not familiar:
            familiar = Familiar.query.join(
                EstudianteFamiliar, EstudianteFamiliar.id_familiar == Familiar.id_colaborador
            ).filter(
                EstudianteFamiliar.id_estudiante == uid,
            ).first()
        if not familiar:
            flash('No tienes un familiar vinculado para realizar la justificación. Contacta al administrador.', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

        existing_just = Justificacion.query.filter_by(id_asistencia=asistencia_id).first()
        if existing_just:
            flash('Esta asistencia ya fue justificada anteriormente', 'warning')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

        filename = secure_filename(archivo.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            archivo.save(filepath)
        except Exception:
            flash('Error al guardar el archivo. Intenta nuevamente.', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

        just = Justificacion(
            id_asistencia=asistencia_id,
            id_familiar=familiar.id_colaborador,
            motivo_justificacion=motivo,
            evidencia_archivo_url=f'uploads/{filename}',
        )
        db.session.add(just)
        try:
            db.session.commit()
            flash('Justificación enviada correctamente', 'success')
        except Exception:
            db.session.rollback()
            flash('Error al guardar la justificación. Intenta nuevamente.', 'danger')
        return redirect(url_for('estudiante.asistencia', bimestre_id=periodo_id))

    matricula = _obtener_matricula_activa(uid)
    asistencias = []
    justificadas = set()

    if matricula:
        inscripciones = Inscripcion.query.filter_by(id_matricula=matricula.id).all()
        for ins in inscripciones:
            cursos_data = _obtener_cursos_por_aula(ins.id_aula_asignada)
            nom_curso = cursos_data[0][0].nombre_curso if cursos_data else 'General'
            asis_records = Asistencia.query.options(
                joinedload(Asistencia.justificacion),
            ).filter_by(id_inscripcion=ins.id).order_by(Asistencia.fecha_asistencia.desc()).all()

            for a in asis_records:
                asistencias.append(SimpleNamespace(
                    id=str(a.id),
                    fecha=a.fecha_asistencia,
                    estado=a.estado_asistencia,
                    curso=SimpleNamespace(nombre=nom_curso),
                ))
                if a.justificacion:
                    justificadas.add(str(a.id))

    justificadas_ids = set(
        str(j[0]) for j in db.session.query(Justificacion.id_asistencia).join(
            Asistencia, Asistencia.id == Justificacion.id_asistencia
        ).join(
            Inscripcion, Inscripcion.id == Asistencia.id_inscripcion
        ).join(
            Matricula, Matricula.id == Inscripcion.id_matricula
        ).filter(
            Matricula.id_estudiante == uid,
        ).all()
    )
    justificadas.update(justificadas_ids)

    return render_template('estudiante_asistencia.html',
        asistencias=asistencias,
        bimestre_id=periodo_id,
        bimestres=bimestres,
        justificadas=justificadas_ids)


@estudiante_bp.route('/pagos')
@login_required
@role_required('alumno')
def pagos():
    uid = session['usuario_id']
    estudiante = Estudiante.query.get(uid)
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('estudiante.dashboard'))

    matricula = _obtener_matricula_activa(uid)
    pagos = []
    planes = []

    if matricula:
        pagos_q = Pago.query.options(
            joinedload(Pago.plan),
        ).filter_by(id_matricula=matricula.id).order_by(Pago.fecha_transaccion.desc()).all()

        for p in pagos_q:
            pagos.append(SimpleNamespace(
                id=str(p.id),
                monto_pagado=p.monto_pagado,
                monto_mora=p.monto_mora,
                fecha_pago=p.fecha_transaccion,
                metodo_pago=p.metodo_pago,
                comprobante_numero=p.comprobante_numero,
                plan=SimpleNamespace(
                    nombre=p.plan.concepto_pago,
                    monto=p.plan.monto_base,
                    fecha_vencimiento=p.plan.fecha_vencimiento,
                ) if p.plan else None,
                estado='cancelado',
            ))

        inscripciones = Inscripcion.query.filter_by(id_matricula=matricula.id).all()
        aulas_ids = list(set(ins.id_aula_asignada for ins in inscripciones))
        planes_q = PagoPlan.query.filter(
            PagoPlan.id_aula_asignada.in_(aulas_ids),
        ).order_by(PagoPlan.fecha_vencimiento).all() if aulas_ids else []

        for pl in planes_q:
            planes.append(SimpleNamespace(
                id=str(pl.id),
                concepto=pl.concepto_pago,
                nombre=pl.concepto_pago,
                monto=pl.monto_base,
                fecha_vencimiento=pl.fecha_vencimiento,
            ))

    return render_template('estudiante_pagos.html',
        pagos=pagos,
        planes=planes,
        estudiante=estudiante)


@estudiante_bp.route('/api/detalle_notas/<curso_id>')
@login_required
@role_required('alumno')
def api_detalle_notas(curso_id):
    uid = session['usuario_id']
    estudiante = Estudiante.query.get(uid)
    if not estudiante:
        return jsonify({'error': 'Estudiante no encontrado'}), 404

    matricula = _obtener_matricula_activa(uid)
    if not matricula:
        return jsonify({'bimestres': []})

    inscripciones = Inscripcion.query.options(
        joinedload(Inscripcion.calificaciones).joinedload(Calificacion.evaluacion),
    ).filter_by(id_matricula=matricula.id).all()

    bloque_data = {}
    for ins in inscripciones:
        cursos_data = _obtener_cursos_por_aula(ins.id_aula_asignada)
        for c, asig, _, _, _, _ in cursos_data:
            if str(c.id) != curso_id:
                continue
            for cal in ins.calificaciones:
                ev = cal.evaluacion
                if not ev or str(ev.id_asignacion_docente) != str(asig.id):
                    continue
                bloque = ev.bimestre_bloque
                if bloque not in bloque_data:
                    bloque_data[bloque] = []
                bloque_data[bloque].append({
                    'id_evaluacion': str(ev.id),
                    'nombre_evaluacion': ev.nombre_evaluacion,
                    'nota': float(cal.nota),
                    'peso': float(ev.porcentaje_peso),
                    'comentarios': cal.comentarios,
                    'porcentaje_peso': float(ev.porcentaje_peso),
                })
            break

    resultado = []
    for bloque in sorted(bloque_data.keys()):
        evals = bloque_data[bloque]
        total_peso = sum(e['peso'] for e in evals)
        prom = round(sum(e['nota'] * e['peso'] for e in evals) / total_peso, 2) if total_peso > 0 else None
        resultado.append({
            'nombre': f'Bimestre {bloque}',
            'evaluaciones': evals,
            'promedio': prom,
            'letra': nota_a_letra(prom),
        })

    return jsonify({'bimestres': resultado})


@estudiante_bp.route('/api/resumen')
@login_required
@role_required('alumno')
def api_resumen():
    uid = session['usuario_id']
    estudiante = Estudiante.query.get(uid)
    if not estudiante:
        return jsonify({'error': 'No encontrado'}), 404

    matricula = _obtener_matricula_activa(uid)
    if not matricula:
        return jsonify({'promedio_general': None, 'cursos': 0, 'asistencia': None})

    inscripciones = Inscripcion.query.filter_by(id_matricula=matricula.id).all()
    promedios, _ = _calcular_promedio_y_evals(inscripciones)

    proms = [v['promedio'] for v in promedios.values() if v['promedio'] is not None]
    prom_gral = round(sum(proms) / len(proms), 2) if proms else None

    total_cursos = len(promedios)

    asistencias = Asistencia.query.join(
        Inscripcion, Inscripcion.id == Asistencia.id_inscripcion
    ).filter(
        Inscripcion.id_matricula == matricula.id,
    ).all()
    total_asis = len(asistencias)
    presentes = sum(1 for a in asistencias if a.estado_asistencia in ('P', 'T'))
    asistencia_pct = round(presentes / total_asis * 100, 1) if total_asis > 0 else None

    return jsonify({
        'promedio_general': prom_gral,
        'letra': nota_a_letra(prom_gral),
        'cursos': total_cursos,
        'asistencia': asistencia_pct,
    })
