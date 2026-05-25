from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from sqlalchemy.orm import joinedload
from db import db
from models import (
    Estudiante, Curso, Inscripcion, Evaluacion, Asistencia,
    Justificacion, Comentario, Bimestre, PagoRealizado, PagoPlan, Horario
)
from functools import wraps
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

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')

def obtener_bimestre_actual():
    hoy = datetime.now().date()
    return Bimestre.query.filter(
        Bimestre.fecha_inicio <= hoy,
        Bimestre.fecha_fin >= hoy
    ).first()

@estudiante_bp.route('/dashboard')
@login_required
@role_required('alumno')
def dashboard():
    estudiante = Estudiante.query.get(session['usuario_id'])
    bimestre = obtener_bimestre_actual()
    inscripciones = Inscripcion.query.filter_by(alumno_id=estudiante.id).all()
    cursos = [i.curso for i in inscripciones]
    bimestre_id = request.args.get('bimestre_id', type=int) or (bimestre.id if bimestre else None)
    selected_bimestre = Bimestre.query.get(bimestre_id) if bimestre_id else bimestre

    from app import _calcular_promedio_desde_datos, nota_a_letra, sincronizar_estado_pagos, sincronizar_mora
    promedios = {}
    evaluaciones_por_curso = {}
    if selected_bimestre and cursos:
        curso_ids = [c.id for c in cursos]
        todas_evals = Evaluacion.query.filter(
            Evaluacion.estudiante_id == estudiante.id,
            Evaluacion.curso_id.in_(curso_ids),
            Evaluacion.bimestre_id == selected_bimestre.id
        ).all()
        todas_asistencias = Asistencia.query.filter(
            Asistencia.estudiante_id == estudiante.id,
            Asistencia.curso_id.in_(curso_ids),
            Asistencia.bimestre_id == selected_bimestre.id
        ).all()
        evals_idx = {}
        for ev in todas_evals:
            evals_idx.setdefault(ev.curso_id, []).append(ev)
        for curso in cursos:
            evs = evals_idx.get(curso.id, [])
            notas = {}
            for ev in evs:
                notas[ev.tipo] = float(ev.calificacion)
            evaluaciones_por_curso[curso.id] = notas
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

    sincronizar_estado_pagos(estudiante.id)
    sincronizar_mora(estudiante.id)
    pagos_pendientes = PagoRealizado.query.filter_by(estudiante_id=estudiante.id, estado='pendiente').count()
    pagos_atrasados = PagoRealizado.query.filter_by(estudiante_id=estudiante.id, estado='atrasado').count()
    pagos = PagoRealizado.query.options(
        joinedload(PagoRealizado.plan)
    ).filter_by(estudiante_id=estudiante.id).order_by(PagoRealizado.fecha_pago.desc()).all()
    comentarios = Comentario.query.options(
        joinedload(Comentario.docente)
    ).filter_by(estudiante_id=estudiante.id).order_by(Comentario.fecha_creacion.desc()).all()
    asistencias = Asistencia.query.options(
        joinedload(Asistencia.curso)
    ).filter_by(estudiante_id=estudiante.id, bimestre_id=selected_bimestre.id if selected_bimestre else None).order_by(Asistencia.fecha.desc()).all() if selected_bimestre else []
    justificadas = {j.asistencia_id for j in Justificacion.query.filter_by(estudiante_id=estudiante.id).all()}
    bimestres = Bimestre.query.all()

    return render_template('dashboard_estudiante.html',
        estudiante=estudiante, cursos=cursos,
        promedios=promedios, evaluaciones_por_curso=evaluaciones_por_curso,
        bimestre=selected_bimestre, bimestre_id=bimestre_id,
        pagos_pendientes=pagos_pendientes, pagos_atrasados=pagos_atrasados,
        pagos=pagos, comentarios=comentarios,
        asistencias=asistencias, justificadas=justificadas,
        bimestres=bimestres)

@estudiante_bp.route('/horario')
@login_required
@role_required('alumno')
def horario():
    estudiante = Estudiante.query.get(session['usuario_id'])
    horarios = Horario.query.options(
        joinedload(Horario.curso), joinedload(Horario.docente)
    ).filter_by(seccion_id=estudiante.seccion_id).all()
    return render_template('estudiante_horario.html', horarios=horarios, dias=['Lunes','Martes','Miércoles','Jueves','Viernes'])

@estudiante_bp.route('/notas')
@login_required
@role_required('alumno')
def notas():
    from app import _calcular_promedio_desde_datos, nota_a_letra
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
                'promedio': prom, 'letra': nota_a_letra(prom) if prom is not None else '-',
                'asistencia': asist
            }
    return render_template('estudiante_notas.html', notas=notas_por_curso, bimestre_id=bimestre_id, bimestres=bimestres)

@estudiante_bp.route('/asistencia', methods=['GET', 'POST'])
@login_required
@role_required('alumno')
def asistencia():
    from werkzeug.utils import secure_filename
    estudiante = Estudiante.query.get(session['usuario_id'])
    bimestre_id = request.form.get('bimestre_id', type=int) or request.args.get('bimestre_id', type=int) or (obtener_bimestre_actual().id if obtener_bimestre_actual() else None)

    if request.method == 'POST':
        asistencia_id = int(request.form.get('asistencia_id'))
        titulo = request.form.get('titulo', '')
        motivo = request.form.get('motivo')
        archivo = request.files.get('archivo')
        if not archivo or not archivo.filename:
            flash('El archivo es obligatorio para justificar', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=bimestre_id))
        if not titulo:
            flash('El título es obligatorio', 'danger')
            return redirect(url_for('estudiante.asistencia', bimestre_id=bimestre_id))
        filename = secure_filename(archivo.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        archivo.save(filepath)
        j = Justificacion(
            asistencia_id=asistencia_id, estudiante_id=estudiante.id,
            titulo=titulo, motivo=motivo,
            archivo_ruta=f'uploads/{filename}', archivo_nombre=filename
        )
        db.session.add(j); db.session.commit()
        flash('Justificación enviada', 'success')
        return redirect(url_for('estudiante.asistencia', bimestre_id=bimestre_id))

    asistencias = Asistencia.query.options(
        joinedload(Asistencia.curso)
    ).filter_by(estudiante_id=estudiante.id, bimestre_id=bimestre_id).order_by(Asistencia.fecha.desc()).all()
    justificadas = {j.asistencia_id for j in Justificacion.query.filter_by(estudiante_id=estudiante.id).all()}
    return render_template('estudiante_asistencia.html',
        asistencias=asistencias, bimestre_id=bimestre_id,
        bimestres=Bimestre.query.all(), justificadas=justificadas)

@estudiante_bp.route('/comentarios')
@login_required
@role_required('alumno')
def comentarios():
    estudiante = Estudiante.query.get(session['usuario_id'])
    comentarios = Comentario.query.options(
        joinedload(Comentario.docente)
    ).filter_by(estudiante_id=estudiante.id).order_by(Comentario.fecha_creacion.desc()).all()
    return render_template('estudiante_comentarios.html', comentarios=comentarios)

@estudiante_bp.route('/api/detalle_notas/<int:curso_id>')
@login_required
@role_required('alumno')
def api_detalle_notas(curso_id):
    from app import nota_a_letra
    estudiante = Estudiante.query.get(session['usuario_id'])
    bimestres = Bimestre.query.order_by(Bimestre.numero).all()
    resultado = []
    for b in bimestres:
        evals = Evaluacion.query.filter_by(
            estudiante_id=estudiante.id, curso_id=curso_id, bimestre_id=b.id
        ).all()
        notas = {}
        for ev in evals:
            notas[ev.tipo] = float(ev.calificacion)
        c = notas.get('cuaderno')
        l = notas.get('libro')
        p = notas.get('practicas')
        ex = notas.get('exposiciones')
        em = notas.get('examen')
        prom = None
        if c is not None and l is not None and p is not None and ex is not None and em is not None:
            prom = round(c*0.10 + l*0.10 + p*0.20 + ex*0.10 + em*0.50, 2)
        resultado.append({
            'nombre': b.nombre,
            'notas': {'cuaderno': c, 'libro': l, 'practicas': p, 'exposiciones': ex, 'examen': em},
            'promedio': prom,
            'letra': nota_a_letra(prom) if prom is not None else '-'
        })
    return jsonify({'bimestres': resultado})

@estudiante_bp.route('/pagos')
@login_required
@role_required('alumno')
def pagos():
    from app import sincronizar_estado_pagos, sincronizar_mora
    estudiante = Estudiante.query.get(session['usuario_id'])
    sincronizar_estado_pagos(estudiante.id)
    sincronizar_mora(estudiante.id)
    pagos = PagoRealizado.query.options(
        joinedload(PagoRealizado.plan)
    ).filter_by(estudiante_id=estudiante.id).all()
    planes = PagoPlan.query.filter_by(activo=True).all()
    return render_template('estudiante_pagos.html', pagos=pagos, planes=planes, estudiante=estudiante)
