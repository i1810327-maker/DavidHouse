from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, Response
from datetime import datetime
from sqlalchemy.orm import joinedload
from db import db
from models import (
    Nivel, PeriodoAcademico, Bimestre, Grado, Seccion,
    Colaborador, Estudiante, Apoderado,
    Curso, Inscripcion, Horario, Evaluacion, Asistencia,
    Justificacion, Comentario, PagoPlan, PagoRealizado,
    CarpetaDocente, DocumentoDocente, Evento, SolicitudReporte
)
from functools import wraps
import logging, os, csv, io


logger = logging.getLogger(__name__)
directora_bp = Blueprint('directora', __name__, url_prefix='/directora')

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

@directora_bp.route('/dashboard')
@login_required
@role_required('directora')
def dashboard():
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
    pagos_realizados = PagoRealizado.query.options(
        joinedload(PagoRealizado.estudiante), joinedload(PagoRealizado.plan)
    ).order_by(PagoRealizado.fecha_pago.desc()).all()
    estudiantes = alumnos
    eventos = Evento.query.filter_by(activo=True).order_by(Evento.orden).all()
    documentos = DocumentoDocente.query.options(
        joinedload(DocumentoDocente.carpeta), joinedload(DocumentoDocente.docente)
    ).filter(DocumentoDocente.estado == 'pendiente').order_by(DocumentoDocente.fecha_subida.desc()).all()
    justificaciones_pendientes = Justificacion.query.options(
        joinedload(Justificacion.asistencia), joinedload(Justificacion.estudiante)
    ).filter_by(estado='pendiente').order_by(Justificacion.fecha_envio.desc()).all()
    solicitudes = SolicitudReporte.query.options(
        joinedload(SolicitudReporte.creador)
    ).order_by(SolicitudReporte.fecha_creacion.desc()).all()

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
        horarios=horarios_list, planes=planes, pagos_realizados=pagos_realizados,
        estudiantes=estudiantes, documentos=documentos,
        justificaciones=justificaciones_pendientes,
        eventos=eventos, solicitudes=solicitudes)

# ----- CRUD NIVELES -----
@directora_bp.route('/niveles', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def niveles_crud():
    if request.method == 'POST':
        try:
            accion = request.form.get('accion')
            ajax = request.form.get('ajax') == '1'
            logger.warning('niveles_crud POST: ajax=%s, accion=%s, form_keys=%s, accion_raw=%r, nombre=%r',
                           ajax, accion, list(request.form.keys()), request.form.get('accion'), request.form.get('nombre'))
            if accion == 'crear':
                nombre = request.form.get('nombre', '').strip()
                if not nombre:
                    if ajax: return jsonify({'success': False, 'error': 'El nombre es obligatorio'})
                    flash('El nombre es obligatorio', 'danger')
                    return redirect(url_for('directora.dashboard') + '#academico')
                if Nivel.query.filter_by(nombre=nombre).first():
                    if ajax: return jsonify({'success': False, 'error': 'Ya existe un nivel con ese nombre'})
                    flash('Ya existe un nivel con ese nombre', 'danger')
                    return redirect(url_for('directora.dashboard') + '#academico')
                n = Nivel(nombre=nombre)
                db.session.add(n); db.session.commit()
                if ajax:
                    return jsonify({'success': True, 'item': {'id': n.id, 'nombre': n.nombre, 'activo': n.activo}})
                flash('Nivel creado', 'success')
            elif accion == 'editar':
                n = Nivel.query.get(int(request.form.get('id')))
                if n: n.nombre = request.form.get('nombre'); db.session.commit()
                flash('Nivel actualizado', 'success')
            elif accion == 'toggle':
                n = Nivel.query.get(int(request.form.get('id')))
                if n: n.activo = not n.activo; db.session.commit()
                if ajax:
                    return jsonify({'success': True, 'item': {'id': n.id, 'activo': n.activo}})
                flash('Nivel actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            logger.exception('Error en niveles_crud: %s', e)
            if request.form.get('ajax') == '1':
                return jsonify({'success': False, 'error': str(e)})
            flash('Error: ' + str(e), 'danger')
    return redirect(url_for('directora.dashboard') + '#academico')

@directora_bp.route('/grados', methods=['POST'])
@login_required
@role_required('directora')
def grados_crud():
    try:
        accion = request.form.get('accion')
        ajax = request.form.get('ajax') == '1'
        logger.warning('grados_crud POST: ajax=%s, accion=%s, form_keys=%s, nombre=%r, nivel_id=%r',
                       ajax, accion, list(request.form.keys()), request.form.get('nombre'), request.form.get('nivel_id'))
        if accion == 'crear':
            nombre = request.form.get('nombre', '').strip()
            nivel_id = request.form.get('nivel_id')
            if not nombre or not nivel_id:
                if ajax: return jsonify({'success': False, 'error': 'Nombre y nivel son obligatorios'})
                flash('Nombre y nivel son obligatorios', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            if Grado.query.filter_by(nombre=nombre, nivel_id=int(nivel_id)).first():
                if ajax: return jsonify({'success': False, 'error': 'Ya existe un grado con ese nombre en este nivel'})
                flash('Ya existe un grado con ese nombre en este nivel', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            nivel_obj = Nivel.query.get(int(nivel_id))
            if not nivel_obj:
                if ajax: return jsonify({'success': False, 'error': 'Nivel no encontrado'})
                flash('Nivel no encontrado', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            g = Grado(nombre=nombre, nivel_id=nivel_obj.id, nivel=nivel_obj.nombre, activo=True)
            db.session.add(g); db.session.commit()
            if ajax:
                return jsonify({'success': True, 'item': {'id': g.id, 'nombre': g.nombre, 'nivel_id': g.nivel_id, 'nivel_nombre': g.nivel_rel.nombre if g.nivel_rel else '', 'activo': g.activo}})
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
            if ajax:
                return jsonify({'success': True, 'item': {'id': g.id, 'activo': g.activo}})
            flash('Grado actualizado', 'success')
    except Exception as e:
        db.session.rollback()
        logger.exception('Error en grados_crud: %s', e)
        if request.form.get('ajax') == '1':
            return jsonify({'success': False, 'error': str(e)})
        flash('Error: ' + str(e), 'danger')
    return redirect(url_for('directora.dashboard') + '#academico')

@directora_bp.route('/secciones', methods=['POST'])
@login_required
@role_required('directora')
def secciones_crud():
    try:
        accion = request.form.get('accion')
        ajax = request.form.get('ajax') == '1'
        logger.warning('secciones_crud POST: ajax=%s, accion=%s, form_keys=%s, nombre=%r, grado_id=%r',
                       ajax, accion, list(request.form.keys()), request.form.get('nombre'), request.form.get('grado_id'))
        if accion == 'crear':
            nombre = request.form.get('nombre', '').strip()
            grado_id = request.form.get('grado_id')
            if not nombre or not grado_id:
                if ajax: return jsonify({'success': False, 'error': 'Nombre y grado son obligatorios'})
                flash('Nombre y grado son obligatorios', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            if Seccion.query.filter_by(nombre=nombre, grado_id=int(grado_id)).first():
                if ajax: return jsonify({'success': False, 'error': 'Ya existe una sección con ese nombre en este grado'})
                flash('Ya existe una sección con ese nombre en este grado', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            s = Seccion(nombre=nombre, grado_id=int(grado_id), activo=True)
            db.session.add(s); db.session.commit()
            if ajax:
                return jsonify({'success': True, 'item': {'id': s.id, 'nombre': s.nombre, 'grado_id': s.grado_id, 'grado_nombre': s.grado.nombre if s.grado else '', 'activo': s.activo}})
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
            if ajax:
                return jsonify({'success': True, 'item': {'id': s.id, 'activo': s.activo}})
            flash('Sección actualizada', 'success')
    except Exception as e:
        db.session.rollback()
        logger.exception('Error en secciones_crud: %s', e)
        if request.form.get('ajax') == '1':
            return jsonify({'success': False, 'error': str(e)})
        flash('Error: ' + str(e), 'danger')
    return redirect(url_for('directora.dashboard') + '#academico')

@directora_bp.route('/periodos', methods=['POST'])
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
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/bimestres', methods=['POST'])
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
        flash('Usa el periodo para activar/desactivar', 'info')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/cursos', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def cursos_crud():
    if request.method == 'POST':
        accion = request.form.get('accion', 'crear')
        if accion == 'crear':
            nombre = request.form.get('nombre', '').strip()
            codigo = request.form.get('codigo', '').strip()
            if not nombre or not codigo:
                flash('Nombre y c\u00f3digo son obligatorios', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            if Curso.query.filter_by(codigo=codigo).first():
                flash('El c\u00f3digo ya existe', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            grado_id = request.form.get('grado_id')
            seccion_id = request.form.get('seccion_id')
            docente_id = request.form.get('docente_id')
            if not grado_id or not seccion_id or not docente_id:
                flash('Debes seleccionar grado, secci\u00f3n y docente', 'danger')
                return redirect(url_for('directora.dashboard') + '#academico')
            periodo_id = request.form.get('periodo_academico_id')
            if not periodo_id:
                periodo_activo = PeriodoAcademico.query.filter_by(activo=True).first()
                periodo_id = periodo_activo.id if periodo_activo else None
                if not periodo_id:
                    flash('No hay periodo acad\u00e9mico activo', 'danger')
                    return redirect(url_for('directora.dashboard') + '#academico')
            c = Curso(
                nombre=nombre,
                codigo=codigo,
                descripcion=request.form.get('descripcion', ''),
                docente_id=int(docente_id),
                grado_id=int(grado_id),
                seccion_id=int(seccion_id),
                periodo_academico_id=int(periodo_id)
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
    return redirect(url_for('directora.dashboard') + '#academico')

@directora_bp.route('/api/grados/<int:nivel_id>')
@login_required
@role_required('directora')
def api_grados_por_nivel(nivel_id):
    grados = Grado.query.filter_by(nivel_id=nivel_id).all()
    return jsonify([{
        'id': g.id, 'nombre': g.nombre,
        'secciones': [{'id': s.id, 'nombre': s.nombre} for s in g.secciones if s.activo]
    } for g in grados])

@directora_bp.route('/api/secciones/<int:grado_id>')
@login_required
@role_required('directora')
def api_secciones_por_grado(grado_id):
    secciones = Seccion.query.filter_by(grado_id=grado_id).all()
    return jsonify([{'id': s.id, 'nombre': s.nombre} for s in secciones])

@directora_bp.route('/horarios', methods=['POST'])
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
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/api/horarios/<int:seccion_id>')
@login_required
@role_required('directora')
def api_horarios_por_seccion(seccion_id):
    horarios = Horario.query.filter_by(seccion_id=seccion_id).all()
    return jsonify([{
        'id': h.id,
        'dia_semana': h.dia_semana,
        'hora_inicio': h.hora_inicio.strftime('%H:%M'),
        'hora_fin': h.hora_fin.strftime('%H:%M'),
        'curso_id': h.curso_id,
        'curso_nombre': h.curso.nombre if h.curso else '',
        'docente_id': h.docente_id,
        'docente_nombre': h.docente.nombre_completo if h.docente else ''
    } for h in horarios])

@directora_bp.route('/api/horarios/crear', methods=['POST'])
@login_required
@role_required('directora')
def api_horario_crear():
    data = request.get_json()
    h = Horario(
        curso_id=int(data['curso_id']),
        seccion_id=int(data['seccion_id']),
        docente_id=int(data['docente_id']),
        dia_semana=int(data['dia_semana']),
        hora_inicio=datetime.strptime(data['hora_inicio'], '%H:%M').time(),
        hora_fin=datetime.strptime(data['hora_fin'], '%H:%M').time()
    )
    db.session.add(h); db.session.commit()
    return jsonify({'success': True, 'id': h.id})

@directora_bp.route('/api/horarios/eliminar/<int:id>', methods=['DELETE'])
@login_required
@role_required('directora')
def api_horario_eliminar(id):
    h = Horario.query.get(id)
    if h: db.session.delete(h); db.session.commit()
    return jsonify({'success': True})

# ----- COLABORADORES -----
@directora_bp.route('/colaboradores/crear', methods=['POST'])
@login_required
@role_required('directora')
def crear_colaborador():
    from app import bcrypt, validar_clave
    dni = request.form.get('dni')
    if Colaborador.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora.dashboard'))
    nom = request.form.get('nombres', '').strip()
    apPat = request.form.get('apellido_paterno', '').strip()
    apMat = request.form.get('apellido_materno', '').strip()
    if Colaborador.query.filter_by(nombres=nom, apellido_paterno=apPat, apellido_materno=apMat).first():
        flash('Ya existe un colaborador con ese nombre y apellidos', 'danger')
        return redirect(url_for('directora.dashboard'))
    correo = request.form.get('correo')
    if Colaborador.query.filter_by(correo=correo).first():
        flash('El correo ya existe', 'danger')
        return redirect(url_for('directora.dashboard'))
    clave = request.form.get('clave')
    errores = validar_clave(clave)
    if errores:
        for e in errores: flash(e, 'danger')
        return redirect(url_for('directora.dashboard'))
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
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/colaboradores/editar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def editar_colaborador(id):
    from app import bcrypt, validar_clave
    c = Colaborador.query.get_or_404(id)
    dni = request.form.get('dni')
    if dni != c.dni and Colaborador.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora.dashboard'))
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
            return redirect(url_for('directora.dashboard'))
        c.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
    db.session.commit()
    flash('Colaborador actualizado', 'success')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/colaboradores/toggle/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def toggle_colaborador(id):
    c = Colaborador.query.get_or_404(id)
    c.activo = not c.activo
    db.session.commit()
    flash(f'Colaborador {"activado" if c.activo else "desactivado"}', 'success')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/colaboradores/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def eliminar_colaborador(id):
    c = Colaborador.query.get_or_404(id)
    Horario.query.filter_by(docente_id=c.id).delete()
    db.session.delete(c); db.session.commit()
    flash('Colaborador eliminado', 'success')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/registrar_docente', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def registrar_docente():
    from app import bcrypt, validar_clave
    if request.method == 'POST':
        dni = request.form.get('dni')
        if Colaborador.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('directora.registrar_docente'))
        correo = request.form.get('correo')
        if Colaborador.query.filter_by(correo=correo).first():
            flash('El correo ya existe', 'danger')
            return redirect(url_for('directora.registrar_docente'))
        clave = request.form.get('clave')
        errores = validar_clave(clave)
        if errores:
            for e in errores: flash(e, 'danger')
            return redirect(url_for('directora.registrar_docente'))
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
        return redirect(url_for('directora.listar_docentes'))
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel, 'nivel_id': grado.nivel_id,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('docentes_form.html', grados_data=grados_data, niveles=Nivel.query.all())

@directora_bp.route('/listar_docentes')
@login_required
@role_required('directora')
def listar_docentes():
    docentes = Colaborador.query.filter_by(rol='docente').all()
    return render_template('listar_docentes.html', docentes=docentes)

@directora_bp.route('/listar_alumnos')
@login_required
@role_required('directora')
def listar_alumnos():
    alumnos = Estudiante.query.all()
    return render_template('listar_alumnos.html', alumnos=alumnos)

@directora_bp.route('/registrar_alumno', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def registrar_alumno():
    from app import bcrypt, validar_clave
    if request.method == 'POST':
        dni = request.form.get('dni')
        if Estudiante.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('directora.registrar_alumno'))
        correo = request.form.get('correo')
        if Estudiante.query.filter_by(correo=correo).first():
            flash('El correo ya existe', 'danger')
            return redirect(url_for('directora.registrar_alumno'))
        clave = request.form.get('clave')
        errores = validar_clave(clave)
        if errores:
            for e in errores: flash(e, 'danger')
            return redirect(url_for('directora.registrar_alumno'))
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
        if ap_nombres and 'apoderado_activo' in request.form:
            ap = Apoderado(
                dni=request.form.get('apoderado_dni', ''),
                nombres=ap_nombres,
                apellido_paterno=request.form.get('apoderado_apellido_paterno', ''),
                apellido_materno=request.form.get('apoderado_apellido_materno', ''),
                telefono_principal=request.form.get('apoderado_telefono_principal', ''),
                telefono_secundario=request.form.get('apoderado_telefono_secundario', ''),
                alumno_id=a.id
            )
            db.session.add(ap); db.session.commit()
        flash(f'Estudiante {a.nombre_completo} registrado', 'success')
        return redirect(url_for('directora.listar_alumnos'))
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel, 'nivel_id': grado.nivel_id,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    niveles = Nivel.query.all()
    return render_template('registrar_alumno.html', grados_data=grados_data, niveles=niveles)

@directora_bp.route('/editar_docente/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def editar_docente(id):
    from app import bcrypt, validar_clave
    c = Colaborador.query.get_or_404(id)
    if c.rol != 'docente':
        flash('No es un docente', 'danger')
        return redirect(url_for('directora.listar_docentes'))
    if request.method == 'POST':
        dni = request.form.get('dni')
        if dni != c.dni and Colaborador.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('directora.editar_docente', id=id))
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
                return redirect(url_for('directora.editar_docente', id=id))
            c.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
        seccion_id = request.form.get('seccion_docente_id')
        if seccion_id:
            s = Seccion.query.get(int(seccion_id))
            if s: s.docente_id = c.id
        db.session.commit()
        flash('Docente actualizado', 'success')
        return redirect(url_for('directora.listar_docentes'))
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel, 'nivel_id': grado.nivel_id,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    cursos_asignados = Curso.query.filter_by(docente_id=c.id, activo=True).options(
        joinedload(Curso.grado_rel), joinedload(Curso.seccion_rel)
    ).all()
    cursos_disponibles = Curso.query.filter(
        Curso.docente_id != c.id, Curso.activo == True
    ).options(joinedload(Curso.grado_rel), joinedload(Curso.seccion_rel)).all()
    cursos_data = [{
        'id': c2.id, 'nombre': c2.nombre,
        'grado_id': c2.grado_id, 'seccion_id': c2.seccion_id
    } for c2 in cursos_disponibles]
    niveles = Nivel.query.all()
    return render_template('editar_docente.html', docente=c, grados_data=grados_data,
                           cursos_asignados=cursos_asignados, cursos_disponibles=cursos_disponibles,
                           cursos_data=cursos_data, niveles=niveles)

@directora_bp.route('/api/docente/<int:id>/asignar_curso', methods=['POST'])
@login_required
@role_required('directora')
def asignar_curso_docente(id):
    c = Colaborador.query.get_or_404(id)
    curso_id = request.form.get('curso_id')
    if not curso_id:
        return {'ok': False, 'error': 'Falta curso_id'}, 400
    curso = Curso.query.get(int(curso_id))
    if not curso:
        return {'ok': False, 'error': 'Curso no encontrado'}, 404
    curso.docente_id = c.id
    db.session.commit()
    return {'ok': True, 'curso': curso.nombre}

@directora_bp.route('/api/docente/<int:id>/remover_curso/<int:curso_id>', methods=['POST'])
@login_required
@role_required('directora')
def remover_curso_docente(id, curso_id):
    curso = Curso.query.get_or_404(curso_id)
    curso.docente_id = None
    db.session.commit()
    return {'ok': True}

@directora_bp.route('/editar_alumno/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def editar_alumno(id):
    from app import bcrypt, validar_clave
    a = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        dni = request.form.get('dni')
        if dni != a.dni and Estudiante.query.filter_by(dni=dni).first():
            flash('El DNI ya existe', 'danger')
            return redirect(url_for('directora.editar_alumno', id=id))
        correo = request.form.get('correo')
        if correo != a.correo and Estudiante.query.filter_by(correo=correo).first():
            flash('El correo ya existe', 'danger')
            return redirect(url_for('directora.editar_alumno', id=id))
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
                return redirect(url_for('directora.editar_alumno', id=id))
            a.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
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
        return redirect(url_for('directora.listar_alumnos'))
    apoderado = Apoderado.query.filter_by(alumno_id=a.id).first()
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id, 'nombre': grado.nombre, 'nivel': grado.nivel, 'nivel_id': grado.nivel_id,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('editar_alumno.html', alumno=a, apoderado=apoderado,
                           grados=grados, grados_data=grados_data, niveles=Nivel.query.all())

@directora_bp.route('/eliminar_alumno/<int:id>', methods=['POST'])
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
    return redirect(url_for('directora.listar_alumnos'))

@directora_bp.route('/eliminar_docente/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def eliminar_docente(id):
    c = Colaborador.query.get_or_404(id)
    Horario.query.filter_by(docente_id=c.id).delete()
    db.session.delete(c); db.session.commit()
    flash('Docente eliminado', 'success')
    return redirect(url_for('directora.listar_docentes'))

@directora_bp.route('/estudiantes/crear', methods=['POST'])
@login_required
@role_required('directora')
def crear_estudiante():
    from app import bcrypt, validar_clave
    dni = request.form.get('dni')
    if Estudiante.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora.dashboard'))
    nom = request.form.get('nombres', '').strip()
    apPat = request.form.get('apellido_paterno', '').strip()
    apMat = request.form.get('apellido_materno', '').strip()
    if Estudiante.query.filter_by(nombres=nom, apellido_paterno=apPat, apellido_materno=apMat).first():
        flash('Ya existe un alumno con ese nombre y apellidos', 'danger')
        return redirect(url_for('directora.dashboard'))
    correo = request.form.get('correo')
    if Estudiante.query.filter_by(correo=correo).first():
        flash('El correo ya existe', 'danger')
        return redirect(url_for('directora.dashboard'))
    clave = request.form.get('clave')
    errores = validar_clave(clave)
    if errores:
        for e in errores: flash(e, 'danger')
        return redirect(url_for('directora.dashboard'))
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
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/estudiantes/editar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def editar_estudiante(id):
    from app import bcrypt, validar_clave
    e = Estudiante.query.get_or_404(id)
    dni = request.form.get('dni')
    if dni != e.dni and Estudiante.query.filter_by(dni=dni).first():
        flash('El DNI ya existe', 'danger')
        return redirect(url_for('directora.dashboard'))
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
            return redirect(url_for('directora.dashboard'))
        e.clave = bcrypt.generate_password_hash(clave).decode('utf-8')
    db.session.commit()
    flash('Estudiante actualizado', 'success')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/estudiantes/toggle/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def toggle_estudiante(id):
    e = Estudiante.query.get_or_404(id)
    e.activo = not e.activo
    db.session.commit()
    flash(f'Estudiante {"activado" if e.activo else "desactivado"}', 'success')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/alumnos/exportar_csv')
@login_required
@role_required('directora')
def exportar_alumnos_csv():
    alumnos = Estudiante.query.order_by(Estudiante.apellido_paterno).all()
    si = io.StringIO()
    sw = csv.writer(si)
    sw.writerow(['DNI', 'Nombres', 'Apellido Paterno', 'Apellido Materno', 'Correo', 'Grado', 'Seccion', 'Activo'])
    for a in alumnos:
        sw.writerow([a.dni, a.nombres, a.apellido_paterno, a.apellido_materno, a.correo,
            a.grado_rel.nombre if a.grado_rel else '', a.seccion_rel.nombre if a.seccion_rel else '',
            'Si' if a.activo else 'No'])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=alumnos.csv'})

@directora_bp.route('/alumnos/importar_csv', methods=['POST'])
@login_required
@role_required('directora')
def importar_alumnos_csv():
    from app import bcrypt
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename.endswith('.csv'):
        flash('Debe seleccionar un archivo CSV valido', 'danger')
        return redirect(url_for('directora.dashboard'))
    stream = io.StringIO(archivo.stream.read().decode('utf-8-sig'))
    reader = csv.DictReader(stream)
    importados = 0
    errores = 0
    for row in reader:
        try:
            dni = row.get('DNI', '').strip()
            if not dni or Estudiante.query.filter_by(dni=dni).first():
                errores += 1; continue
            correo = row.get('Correo', '').strip()
            if correo and Estudiante.query.filter_by(correo=correo).first():
                errores += 1; continue
            grado_nombre = row.get('Grado', '').strip()
            seccion_nombre = row.get('Seccion', '').strip()
            grado = Grado.query.filter_by(nombre=grado_nombre).first() if grado_nombre else None
            seccion = Seccion.query.filter_by(nombre=seccion_nombre).first() if seccion_nombre else None
            a = Estudiante(
                dni=dni, nombres=row.get('Nombres', '').strip(),
                apellido_paterno=row.get('Apellido Paterno', '').strip(),
                apellido_materno=row.get('Apellido Materno', '').strip(),
                correo=correo or f'{dni}@colegio.edu.pe',
                clave=bcrypt.generate_password_hash('Default123!').decode('utf-8'),
                grado_id=grado.id if grado else None,
                seccion_id=seccion.id if seccion else None
            )
            db.session.add(a)
            importados += 1
        except Exception:
            errores += 1
    db.session.commit()
    flash(f'Importacion completada: {importados} importados, {errores} errores', 'success')
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/estudiantes/eliminar/<int:id>', methods=['POST'])
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
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/justificaciones', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def justificaciones_revision():
    if request.method == 'POST':
        j = Justificacion.query.get(int(request.form.get('id')))
        if j:
            j.estado = request.form.get('estado')
            j.comentario_revision = request.form.get('comentario_revision', '')
            j.fecha_revision = datetime.utcnow()
            j.revisado_por = session['usuario_id']
            if j.estado == 'aprobado' and j.asistencia:
                j.asistencia.estado = 'justificado'
            db.session.commit()
            flash('Justificación revisada', 'success')
        return redirect(url_for('directora.dashboard'))
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/boletas/generar', methods=['POST'])
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

    evals_idx = {}
    for ev in todas_evals:
        key = (ev.estudiante_id, ev.curso_id)
        if key not in evals_idx: evals_idx[key] = []
        evals_idx[key].append(ev)

    asistencias_idx = {}
    for a in todas_asistencias:
        key = (a.estudiante_id, a.curso_id)
        if key not in asistencias_idx: asistencias_idx[key] = []
        asistencias_idx[key].append(a)

    from app import _calcular_promedio_desde_datos, nota_a_letra
    pesos = {'cuaderno': 0.10, 'libro': 0.10, 'practicas': 0.20, 'exposiciones': 0.10, 'examen': 0.50}
    notas_data = {}
    for estudiante in estudiantes:
        notas_data[estudiante.id] = {}
        for curso in cursos:
            evals = evals_idx.get((estudiante.id, curso.id), [])
            asistencias = asistencias_idx.get((estudiante.id, curso.id), [])
            if not evals: continue
            prom_final, pct_asistencia, total_asistencias = _calcular_promedio_desde_datos(evals, asistencias, pesos)
            notas_data[estudiante.id][curso.id] = {
                'promedio': prom_final, 'letra': nota_a_letra(prom_final),
                'asistencia': round(pct_asistencia, 1), 'total_asistencias': total_asistencias
            }

    return render_template('boleta_pdf.html',
        estudiantes=estudiantes, cursos=cursos,
        notas=notas_data, seccion=seccion, bimestre=bimestre)

@directora_bp.route('/pagos', methods=['GET', 'POST'])
@login_required
@role_required('directora')
def pagos():
    from app import sincronizar_mora
    sincronizar_mora()
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
                metodo_pago=request.form.get('metodo_pago', 'efectivo'),
                fecha_vencimiento=datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d')
            )
            db.session.add(p); db.session.commit()
            if request.form.get('auto_asignar') and p.grado_id:
                estudiantes = Estudiante.query.filter_by(grado_id=p.grado_id).all()
                for est in estudiantes:
                    existente = PagoRealizado.query.filter_by(estudiante_id=est.id, pago_plan_id=p.id).first()
                    if not existente:
                        r = PagoRealizado(
                            estudiante_id=est.id, pago_plan_id=p.id,
                            monto_pagado=p.monto, estado='pendiente',
                            metodo_pago=p.metodo_pago
                        )
                        db.session.add(r)
                db.session.commit()
                flash(f'Plan de pago creado y asignado a {len(estudiantes)} estudiantes', 'success')
            else:
                flash('Plan de pago creado', 'success')
        elif accion == 'registrar_pago':
            r = PagoRealizado(
                estudiante_id=int(request.form.get('estudiante_id')),
                pago_plan_id=int(request.form.get('pago_plan_id')),
                monto_pagado=request.form.get('monto_pagado'),
                estado='pagado',
                metodo_pago=request.form.get('metodo_pago', 'efectivo')
            )
            db.session.add(r); db.session.commit()
            flash('Pago registrado', 'success')
        elif accion == 'asignar_plan':
            plan_id = int(request.form.get('plan_id'))
            plan = PagoPlan.query.get(plan_id)
            if not plan:
                flash('Plan no encontrado', 'danger')
                return redirect(url_for('directora.dashboard'))
            query = Estudiante.query
            if plan.grado_id:
                query = query.filter_by(grado_id=plan.grado_id)
            estudiantes = query.all()
            for est in estudiantes:
                existente = PagoRealizado.query.filter_by(estudiante_id=est.id, pago_plan_id=plan_id).first()
                if not existente:
                    r = PagoRealizado(
                        estudiante_id=est.id, pago_plan_id=plan_id,
                        monto_pagado=plan.monto, estado='pendiente',
                        metodo_pago=plan.metodo_pago
                    )
                    db.session.add(r)
            db.session.commit()
            flash(f'Plan asignado a {len(estudiantes)} estudiantes', 'success')
        return redirect(url_for('directora.dashboard'))
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/api/pago/actualizar_metodo', methods=['POST'])
@login_required
@role_required('directora')
def api_actualizar_metodo_pago():
    data = request.get_json()
    pago = PagoRealizado.query.get(int(data['pago_id']))
    if not pago:
        return jsonify({'success': False, 'error': 'Pago no encontrado'}), 404
    pago.metodo_pago = data['metodo_pago']
    db.session.commit()
    return jsonify({'success': True})

@directora_bp.route('/carpetas', methods=['GET', 'POST'])
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
        return redirect(url_for('directora.dashboard'))
    return redirect(url_for('directora.dashboard'))

@directora_bp.route('/documentos/revisar/<int:id>', methods=['POST'])
@login_required
@role_required('directora')
def revisar_documento(id):
    doc = DocumentoDocente.query.get_or_404(id)
    doc.estado = request.form.get('accion', 'aprobado')
    doc.comentario_revision = request.form.get('comentario', '')
    doc.fecha_revision = datetime.utcnow()
    db.session.commit()
    flash(f'Documento {"aprobado" if doc.estado == "aprobado" else "rechazado"}', 'success')
    return redirect(url_for('directora.dashboard'))

# ----- EVENTOS CRUD -----
@directora_bp.route('/eventos', methods=['POST'])
@login_required
@role_required('directora')
def eventos_crud():
    accion = request.form.get('accion')
    if accion == 'crear':
        e = Evento(
            titulo=request.form.get('titulo'),
            descripcion=request.form.get('descripcion', ''),
            imagen_url=request.form.get('imagen_url', ''),
            orden=int(request.form.get('orden', 0))
        )
        db.session.add(e); db.session.commit()
        flash('Evento creado', 'success')
    elif accion == 'eliminar':
        e = Evento.query.get(int(request.form.get('id')))
        if e: db.session.delete(e); db.session.commit()
        flash('Evento eliminado', 'success')
    elif accion == 'toggle':
        e = Evento.query.get(int(request.form.get('id')))
        if e: e.activo = not e.activo; db.session.commit()
    return redirect(url_for('directora.dashboard'))

# ----- SOLICITUDES DE REPORTE -----
@directora_bp.route('/solicitar_reporte', methods=['POST'])
@login_required
@role_required('directora')
def solicitar_reporte():
    s = SolicitudReporte(
        nivel_id=int(request.form.get('nivel_id')) if request.form.get('nivel_id') else None,
        grado_id=int(request.form.get('grado_id')) if request.form.get('grado_id') else None,
        seccion_id=int(request.form.get('seccion_id')) if request.form.get('seccion_id') else None,
        titulo=request.form.get('titulo'),
        descripcion=request.form.get('descripcion', ''),
        fecha_maxima=datetime.strptime(request.form.get('fecha_maxima'), '%Y-%m-%dT%H:%M'),
        creado_por=session['usuario_id']
    )
    db.session.add(s); db.session.commit()
    flash('Solicitud de reporte creada', 'success')
    return redirect(url_for('directora.dashboard'))

# ----- API: estudiantes por curso -----
@directora_bp.route('/api/estudiantes_por_curso/<int:curso_id>')
@login_required
@role_required('directora', 'docente')
def api_estudiantes_por_curso(curso_id):
    curso = Curso.query.get_or_404(curso_id)
    inscripciones = Inscripcion.query.filter_by(curso_id=curso_id).all()
    estudiantes = [{'id': ins.alumno.id, 'nombre': ins.alumno.nombre_completo} for ins in inscripciones]
    return jsonify(estudiantes)

@directora_bp.route('/api/alumnos')
@login_required
@role_required('directora')
def api_alumnos():
    nivel_id = request.args.get('nivel_id', type=int)
    grado_id = request.args.get('grado_id', type=int)
    seccion_id = request.args.get('seccion_id', type=int)
    query = Estudiante.query.filter_by(activo=True)
    if seccion_id:
        query = query.filter_by(seccion_id=seccion_id)
    elif grado_id:
        query = query.filter_by(grado_id=grado_id)
    elif nivel_id:
        grados_ids = [g.id for g in Grado.query.filter_by(nivel_id=nivel_id).all()]
        query = query.filter(Estudiante.grado_id.in_(grados_ids))
    estudiantes = query.order_by(Estudiante.apellido_paterno, Estudiante.nombres).all()
    return jsonify([{
        'id': e.id, 'nombre': e.nombre_completo, 'dni': e.dni,
        'grado': e.grado_rel.nombre if e.grado_rel else '',
        'seccion': e.seccion_rel.nombre if e.seccion_rel else '',
        'nivel': e.grado_rel.nivel_rel.nombre if e.grado_rel and e.grado_rel.nivel_rel else ''
    } for e in estudiantes])

@directora_bp.route('/api/cursos/<int:seccion_id>')
@login_required
@role_required('directora')
def api_cursos_por_seccion(seccion_id):
    cursos = Curso.query.filter_by(seccion_id=seccion_id, activo=True).all()
    return jsonify([{'id': c.id, 'nombre': c.nombre} for c in cursos])

@directora_bp.route('/api/notas')
@login_required
@role_required('directora')
def api_notas_por_curso():
    curso_id = request.args.get('curso_id', type=int)
    bimestre_id = request.args.get('bimestre_id', type=int)
    if not curso_id or not bimestre_id:
        return jsonify({'estudiantes': []})
    curso = Curso.query.get(curso_id)
    if not curso:
        return jsonify({'estudiantes': []})
    estudiantes = Estudiante.query.filter_by(seccion_id=curso.seccion_id, activo=True).order_by(Estudiante.apellido_paterno).all()
    evaluaciones = Evaluacion.query.filter_by(curso_id=curso_id, bimestre_id=bimestre_id).all()
    evals_idx = {}
    for ev in evaluaciones:
        evals_idx.setdefault(ev.estudiante_id, {})[ev.tipo] = float(ev.calificacion)
    result = []
    for e in estudiantes:
        notas = evals_idx.get(e.id, {})
        result.append({
            'id': e.id,
            'nombre': e.nombre_completo,
            'notas': {
                'cuaderno': notas.get('cuaderno'),
                'libro': notas.get('libro'),
                'practicas': notas.get('practicas'),
                'exposiciones': notas.get('exposiciones'),
                'examen': notas.get('examen')
            }
        })
    return jsonify({'estudiantes': result})

@directora_bp.route('/api/notas/guardar', methods=['POST'])
@login_required
@role_required('directora')
def api_notas_guardar():
    data = request.get_json()
    curso_id = data.get('curso_id')
    bimestre_id = data.get('bimestre_id')
    estudiantes_data = data.get('estudiantes', [])
    if not curso_id or not bimestre_id:
        return jsonify({'success': False, 'error': 'Faltan parámetros'}), 400
    existing = Evaluacion.query.filter_by(curso_id=curso_id, bimestre_id=bimestre_id).all()
    evals_key = {}
    for ev in existing:
        evals_key[(ev.estudiante_id, ev.tipo)] = ev
    for ed in estudiantes_data:
        est_id = ed.get('estudiante_id')
        for tipo in ['cuaderno', 'libro', 'practicas', 'exposiciones', 'examen']:
            val = ed.get(tipo)
            if val is not None and val != '':
                key = (est_id, tipo)
                if key in evals_key:
                    evals_key[key].calificacion = float(val)
                else:
                    ev = Evaluacion(
                        curso_id=curso_id, estudiante_id=est_id,
                        bimestre_id=bimestre_id, tipo=tipo,
                        calificacion=float(val), fecha=datetime.now().date()
                    )
                    db.session.add(ev)
    db.session.commit()
    return jsonify({'success': True})

@directora_bp.route('/api/verificar_email')
@login_required
@role_required('directora')
def api_verificar_email():
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'disponible': False})
    col = Colaborador.query.filter_by(correo=email).first()
    est = Estudiante.query.filter_by(correo=email).first()
    return jsonify({'disponible': col is None and est is None})
