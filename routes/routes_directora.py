from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from sqlalchemy.orm import joinedload
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
import logging

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


def generar_codigo_estudiante():
    ultimo = Estudiante.query.order_by(Estudiante.codigo_estudiante.desc()).first()
    if ultimo:
        num = int(ultimo.codigo_estudiante.split('-')[-1]) + 1
    else:
        num = 1
    return f"ALUM-{datetime.now().year}-{num:04d}"


# ============================================================
# 1. DASHBOARD
# ============================================================
@directora_bp.route('/dashboard')
@login_required
@role_required('director')
def dashboard():
    colaboradores = Colaborador.query.count()
    estudiantes_count = Estudiante.query.count()
    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones = Seccion.query.all()
    periodos = PeriodoAcademico.query.all()
    cursos = Curso.query.options(
        joinedload(Curso.asignaciones)
    ).all()

    rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
    docentes = []
    docentes_data = []
    if rol_docente:
        ur_docentes = UsuarioRol.query.filter_by(id_rol=rol_docente.id).all()
        doc_ids = [ur.id_colaborador for ur in ur_docentes]
        docentes = Colaborador.query.filter(Colaborador.id.in_(doc_ids)).all() if doc_ids else []
        for d in docentes:
            usuario = Usuario.query.get(d.id)
            activo = usuario.estado_activo if usuario else True
            asignaciones = AsignacionDocente.query.filter_by(id_profesor=d.id).all()
            cursos_count = len(asignaciones)
            total_est = 0
            materia = 'Sin asignar'
            for asig in asignaciones:
                if asig.curso:
                    materia = asig.curso.nombre_curso
                insc = Inscripcion.query.filter_by(id_aula_asignada=asig.id_aula_asignada).count()
                total_est += insc
            iniciales = (d.nombres[0] if d.nombres else '') + (d.apellidos[0] if d.apellidos else '')
            docentes_data.append(dict(
                id=d.id, dni=d.numero_documento, nombres=d.nombres,
                apellido_paterno=d.apellidos.split(' ')[0] if ' ' in d.apellidos else d.apellidos,
                apellido_materno=' '.join(d.apellidos.split(' ')[1:]) if ' ' in d.apellidos else '',
                nombre_completo=d.nombre_completo, correo='', rol='docente',
                profesion='', activo=activo,
                telefono_principal=d.telefono_principal,
                tiene_especialidad=False, descripcion_especialidad='',
                cursos_count=cursos_count, estudiantes_count=total_est,
                iniciales=iniciales, materia=materia
            ))

    alumnos = Estudiante.query.options(
        joinedload(Estudiante.colaborador)
    ).all()

    planes = PagoPlan.query.all()

    pagos_realizados = Pago.query.order_by(Pago.fecha_registro.desc()).all()

    documentos = DocumentoDocente.query.order_by(DocumentoDocente.fecha_subida.desc()).all()

    justificaciones_pendientes = Justificacion.query.order_by(Justificacion.fecha_presentacion.desc()).all()

    return render_template('dashboard_directora.html',
        colaboradores_count=colaboradores,
        estudiantes_count=estudiantes_count,
        docentes=docentes, docentes_data=docentes_data,
        alumnos=alumnos,
        grados=grados, secciones=secciones,
        niveles=niveles, periodos=periodos,
        cursos=cursos,
        bimestres=[], horarios=[], planes=planes,
        pagos_realizados=pagos_realizados,
        estudiantes=alumnos, documentos=documentos,
        justificaciones=justificaciones_pendientes,
        eventos=[], solicitudes=[])


# ============================================================
# 2. ALUMNOS - Listar
# ============================================================
@directora_bp.route('/alumnos')
@login_required
@role_required('director')
def listar_alumnos():
    alumnos = Estudiante.query.options(
        joinedload(Estudiante.colaborador)
    ).all()
    return render_template('listar_alumnos.html', alumnos=alumnos)


# ============================================================
# 3. ALUMNOS - Registrar
# ============================================================
@directora_bp.route('/alumnos/registrar', methods=['GET', 'POST'])
@login_required
@role_required('director')
def registrar_alumno():
    if request.method == 'POST':
        from app import bcrypt
        try:
            num_doc = request.form.get('numero_documento', '').strip()
            if Colaborador.query.filter_by(numero_documento=num_doc).first():
                flash('El número de documento ya existe', 'danger')
                return redirect(url_for('directora.registrar_alumno'))

            colaborador = Colaborador(
                tipo_documento=request.form.get('tipo_documento', 'DNI'),
                numero_documento=num_doc,
                nombres=request.form.get('nombres', '').strip(),
                apellidos=request.form.get('apellidos', '').strip(),
                fecha_nacimiento=datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date(),
                genero=request.form.get('genero', '').strip(),
                telefono_principal=request.form.get('telefono_principal', '').strip(),
                telefono_secundario=request.form.get('telefono_secundario', '').strip(),
                direccion_fisica=request.form.get('direccion_fisica', '').strip()
            )
            db.session.add(colaborador)
            db.session.flush()

            codigo = generar_codigo_estudiante()
            estudiante = Estudiante(
                id_colaborador=colaborador.id,
                codigo_estudiante=codigo,
                historial_medico=request.form.get('historial_medico', '')
            )
            db.session.add(estudiante)

            username = request.form.get('nombre_usuario', '').strip() or f"alumno.{num_doc}"
            clave = request.form.get('contrasena', num_doc)
            usuario = Usuario(
                id_colaborador=colaborador.id,
                nombre_usuario=username,
                contrasena_hash=bcrypt.generate_password_hash(clave).decode('utf-8')
            )
            db.session.add(usuario)

            rol_alumno = Rol.query.filter_by(nombre_rol='alumno').first()
            if rol_alumno:
                ur = UsuarioRol(id_colaborador=colaborador.id, id_rol=rol_alumno.id)
                db.session.add(ur)

            db.session.commit()
            flash(f'Estudiante {colaborador.nombre_completo} registrado con código {codigo}', 'success')
            return redirect(url_for('directora.listar_alumnos'))
        except Exception as e:
            db.session.rollback()
            logger.exception('Error registrando alumno')
            flash(f'Error al registrar: {str(e)}', 'danger')
            return redirect(url_for('directora.registrar_alumno'))

    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones = Seccion.query.all()
    periodos = PeriodoAcademico.query.filter_by(estado_activo=True).all()
    return render_template('registrar_alumno.html',
        niveles=niveles, grados=grados,
        secciones=secciones, periodos=periodos)


# ============================================================
# 4. ALUMNOS - Editar
# ============================================================
@directora_bp.route('/alumnos/editar/<id>', methods=['GET', 'POST'])
@login_required
@role_required('director')
def editar_alumno(id):
    estudiante = Estudiante.query.options(
        joinedload(Estudiante.colaborador)
    ).get(id)
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('directora.listar_alumnos'))
    colaborador = estudiante.colaborador

    if request.method == 'POST':
        from app import bcrypt
        try:
            num_doc = request.form.get('numero_documento', '').strip()
            existe = Colaborador.query.filter(
                Colaborador.numero_documento == num_doc,
                Colaborador.id != colaborador.id
            ).first()
            if existe:
                flash('El número de documento ya está en uso', 'danger')
                return redirect(url_for('directora.editar_alumno', id=id))

            colaborador.tipo_documento = request.form.get('tipo_documento', 'DNI')
            colaborador.numero_documento = num_doc
            colaborador.nombres = request.form.get('nombres', '').strip()
            colaborador.apellidos = request.form.get('apellidos', '').strip()
            try:
                colaborador.fecha_nacimiento = datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
            colaborador.genero = request.form.get('genero', '').strip()
            colaborador.telefono_principal = request.form.get('telefono_principal', '').strip()
            colaborador.telefono_secundario = request.form.get('telefono_secundario', '').strip()
            colaborador.direccion_fisica = request.form.get('direccion_fisica', '').strip()
            colaborador.fecha_actualizacion = datetime.utcnow()

            estudiante.historial_medico = request.form.get('historial_medico', '')

            usuario = Usuario.query.get(colaborador.id)
            if usuario:
                clave = request.form.get('contrasena', '')
                if clave:
                    usuario.contrasena_hash = bcrypt.generate_password_hash(clave).decode('utf-8')
                username = request.form.get('nombre_usuario', '').strip()
                if username and username != usuario.nombre_usuario:
                    existe_user = Usuario.query.filter(
                        Usuario.nombre_usuario == username,
                        Usuario.id_colaborador != usuario.id_colaborador
                    ).first()
                    if not existe_user:
                        usuario.nombre_usuario = username

            db.session.commit()
            flash('Estudiante actualizado', 'success')
            return redirect(url_for('directora.listar_alumnos'))
        except Exception as e:
            db.session.rollback()
            logger.exception('Error editando alumno')
            flash(f'Error al actualizar: {str(e)}', 'danger')
            return redirect(url_for('directora.editar_alumno', id=id))

    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones = Seccion.query.all()
    return render_template('editar_alumno.html',
        alumno=estudiante, colaborador=colaborador,
        niveles=niveles, grados=grados, secciones=secciones)


# ============================================================
# 5. ALUMNOS - Eliminar (soft-delete)
# ============================================================
@directora_bp.route('/alumnos/eliminar/<id>', methods=['POST'])
@login_required
@role_required('director')
def eliminar_alumno(id):
    estudiante = Estudiante.query.get(id)
    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        return redirect(url_for('directora.listar_alumnos'))
    usuario = Usuario.query.get(estudiante.id_colaborador)
    if usuario:
        usuario.estado_activo = False
        db.session.commit()
        flash('Estudiante desactivado', 'success')
    else:
        flash('Estudiante no tiene usuario asociado', 'warning')
    return redirect(url_for('directora.listar_alumnos'))


# ============================================================
# 6. DOCENTES - Listar
# ============================================================
@directora_bp.route('/docentes')
@login_required
@role_required('director')
def listar_docentes():
    rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
    docentes = []
    if rol_docente:
        ur_docentes = UsuarioRol.query.filter_by(id_rol=rol_docente.id).all()
        doc_ids = [ur.id_colaborador for ur in ur_docentes]
        if doc_ids:
            docentes = Colaborador.query.filter(Colaborador.id.in_(doc_ids)).all()
    return render_template('listar_docentes.html', docentes=docentes)


# ============================================================
# 7. DOCENTES - Registrar
# ============================================================
@directora_bp.route('/docentes/registrar', methods=['GET', 'POST'])
@login_required
@role_required('director')
def registrar_docente():
    if request.method == 'POST':
        from app import bcrypt
        try:
            num_doc = request.form.get('numero_documento', '').strip()
            if Colaborador.query.filter_by(numero_documento=num_doc).first():
                flash('El número de documento ya existe', 'danger')
                return redirect(url_for('directora.registrar_docente'))

            colaborador = Colaborador(
                tipo_documento=request.form.get('tipo_documento', 'DNI'),
                numero_documento=num_doc,
                nombres=request.form.get('nombres', '').strip(),
                apellidos=request.form.get('apellidos', '').strip(),
                fecha_nacimiento=datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date(),
                genero=request.form.get('genero', '').strip(),
                telefono_principal=request.form.get('telefono_principal', '').strip(),
                telefono_secundario=request.form.get('telefono_secundario', '').strip(),
                direccion_fisica=request.form.get('direccion_fisica', '').strip()
            )
            db.session.add(colaborador)
            db.session.flush()

            username = request.form.get('nombre_usuario', '').strip() or f"docente.{num_doc}"
            clave = request.form.get('contrasena', num_doc)
            usuario = Usuario(
                id_colaborador=colaborador.id,
                nombre_usuario=username,
                contrasena_hash=bcrypt.generate_password_hash(clave).decode('utf-8')
            )
            db.session.add(usuario)

            rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
            if rol_docente:
                ur = UsuarioRol(id_colaborador=colaborador.id, id_rol=rol_docente.id)
                db.session.add(ur)

            db.session.commit()
            flash(f'Docente {colaborador.nombre_completo} registrado', 'success')
            return redirect(url_for('directora.listar_docentes'))
        except Exception as e:
            db.session.rollback()
            logger.exception('Error registrando docente')
            flash(f'Error al registrar: {str(e)}', 'danger')
            return redirect(url_for('directora.registrar_docente'))

    niveles = Nivel.query.all()
    grados = Grado.query.all()
    return render_template('docentes_form.html',
        niveles=niveles, grados=grados, docente=None)


# ============================================================
# 8. DOCENTES - Editar
# ============================================================
@directora_bp.route('/docentes/editar/<id>', methods=['GET', 'POST'])
@login_required
@role_required('director')
def editar_docente(id):
    colaborador = Colaborador.query.get(id)
    if not colaborador:
        flash('Docente no encontrado', 'danger')
        return redirect(url_for('directora.listar_docentes'))

    if request.method == 'POST':
        from app import bcrypt
        try:
            num_doc = request.form.get('numero_documento', '').strip()
            existe = Colaborador.query.filter(
                Colaborador.numero_documento == num_doc,
                Colaborador.id != colaborador.id
            ).first()
            if existe:
                flash('El número de documento ya está en uso', 'danger')
                return redirect(url_for('directora.editar_docente', id=id))

            colaborador.tipo_documento = request.form.get('tipo_documento', 'DNI')
            colaborador.numero_documento = num_doc
            colaborador.nombres = request.form.get('nombres', '').strip()
            colaborador.apellidos = request.form.get('apellidos', '').strip()
            try:
                colaborador.fecha_nacimiento = datetime.strptime(
                    request.form.get('fecha_nacimiento'), '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                pass
            colaborador.genero = request.form.get('genero', '').strip()
            colaborador.telefono_principal = request.form.get('telefono_principal', '').strip()
            colaborador.telefono_secundario = request.form.get('telefono_secundario', '').strip()
            colaborador.direccion_fisica = request.form.get('direccion_fisica', '').strip()
            colaborador.fecha_actualizacion = datetime.utcnow()

            usuario = Usuario.query.get(colaborador.id)
            if usuario:
                clave = request.form.get('contrasena', '')
                if clave:
                    usuario.contrasena_hash = bcrypt.generate_password_hash(clave).decode('utf-8')
                username = request.form.get('nombre_usuario', '').strip()
                if username and username != usuario.nombre_usuario:
                    existe_user = Usuario.query.filter(
                        Usuario.nombre_usuario == username,
                        Usuario.id_colaborador != usuario.id_colaborador
                    ).first()
                    if not existe_user:
                        usuario.nombre_usuario = username

            db.session.commit()
            flash('Docente actualizado', 'success')
            return redirect(url_for('directora.listar_docentes'))
        except Exception as e:
            db.session.rollback()
            logger.exception('Error editando docente')
            flash(f'Error al actualizar: {str(e)}', 'danger')
            return redirect(url_for('directora.editar_docente', id=id))

    cursos_asignados = AsignacionDocente.query.options(
        joinedload(AsignacionDocente.curso),
        joinedload(AsignacionDocente.aula)
    ).filter_by(id_profesor=colaborador.id).all()

    niveles = Nivel.query.all()
    grados = Grado.query.all()
    return render_template('editar_docente.html',
        docente=colaborador, niveles=niveles, grados=grados,
        cursos_asignados=cursos_asignados)


# ============================================================
# 9. DOCENTES - Eliminar (soft-delete)
# ============================================================
@directora_bp.route('/docentes/eliminar/<id>', methods=['POST'])
@login_required
@role_required('director')
def eliminar_docente(id):
    usuario = Usuario.query.get(id)
    if usuario:
        usuario.estado_activo = False
        db.session.commit()
        flash('Docente desactivado', 'success')
    else:
        flash('Docente no encontrado', 'danger')
    return redirect(url_for('directora.listar_docentes'))


# ============================================================
# 10. CURSOS - Listar y gestionar
# ============================================================
@directora_bp.route('/cursos', methods=['GET', 'POST'])
@login_required
@role_required('director')
def cursos():
    if request.method == 'POST':
        accion = request.form.get('accion', 'crear')
        if accion == 'crear':
            nombre = request.form.get('nombre_curso', '').strip()
            if not nombre:
                flash('El nombre del curso es obligatorio', 'danger')
                return redirect(url_for('directora.cursos'))
            if Curso.query.filter_by(nombre_curso=nombre).first():
                flash('Ya existe un curso con ese nombre', 'danger')
                return redirect(url_for('directora.cursos'))
            curso = Curso(
                nombre_curso=nombre,
                descripcion_curso=request.form.get('descripcion_curso', '')
            )
            db.session.add(curso)
            db.session.commit()
            flash('Curso creado', 'success')
        elif accion == 'editar':
            curso = Curso.query.get(request.form.get('id'))
            if curso:
                curso.nombre_curso = request.form.get('nombre_curso', curso.nombre_curso)
                curso.descripcion_curso = request.form.get('descripcion_curso', '')
                db.session.commit()
                flash('Curso actualizado', 'success')
        return redirect(url_for('directora.cursos'))

    cursos_list = Curso.query.options(
        joinedload(Curso.asignaciones)
    ).all()

    docentes_activos = []
    rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
    if rol_docente:
        ur_list = UsuarioRol.query.filter_by(id_rol=rol_docente.id).all()
        doc_ids = [ur.id_colaborador for ur in ur_list]
        if doc_ids:
            docentes_activos = Colaborador.query.filter(Colaborador.id.in_(doc_ids)).all()

    aulas = AulaAsignada.query.options(
        joinedload(AulaAsignada.seccion).joinedload(Seccion.grado),
        joinedload(AulaAsignada.periodo)
    ).all()

    niveles = Nivel.query.all()
    return render_template('cursos.html' if 'cursos.html' in [
        t.filename for t in __import__('jinja2').FileSystemLoader.searchpath
    ] else 'dashboard_directora.html', cursos=cursos_list,
        docentes=docentes_activos, aulas=aulas, niveles=niveles)


# ============================================================
# 11. CURSOS - Registrar (POST desde formulario)
# ============================================================
@directora_bp.route('/cursos/registrar', methods=['GET', 'POST'])
@login_required
@role_required('director')
def registrar_curso():
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre_curso', '').strip()
            if not nombre:
                flash('El nombre del curso es obligatorio', 'danger')
                return redirect(url_for('directora.registrar_curso'))
            if Curso.query.filter_by(nombre_curso=nombre).first():
                flash('Ya existe un curso con ese nombre', 'danger')
                return redirect(url_for('directora.registrar_curso'))
            curso = Curso(
                nombre_curso=nombre,
                descripcion_curso=request.form.get('descripcion_curso', '')
            )
            db.session.add(curso)
            db.session.commit()
            flash('Curso creado exitosamente', 'success')
            return redirect(url_for('directora.cursos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('directora.registrar_curso'))

    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones = Seccion.query.all()
    docentes_activos = []
    rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
    if rol_docente:
        ur_list = UsuarioRol.query.filter_by(id_rol=rol_docente.id).all()
        doc_ids = [ur.id_colaborador for ur in ur_list]
        if doc_ids:
            docentes_activos = Colaborador.query.filter(Colaborador.id.in_(doc_ids)).all()
    periodos = PeriodoAcademico.query.filter_by(estado_activo=True).all()
    return render_template('cursos_form.html' if 'cursos_form.html' in dir()
        else 'dashboard_directora.html', niveles=niveles,
        grados=grados, secciones=secciones,
        docentes=docentes_activos, periodos=periodos)


# ============================================================
# 12. CURSOS - Asignar docente a curso + aula
# ============================================================
@directora_bp.route('/cursos/<id>/asignar', methods=['POST'])
@login_required
@role_required('director')
def asignar_curso(id):
    curso = Curso.query.get(id)
    if not curso:
        flash('Curso no encontrado', 'danger')
        return redirect(url_for('directora.cursos'))
    try:
        id_profesor = request.form.get('id_profesor')
        id_aula = request.form.get('id_aula_asignada')
        if not id_profesor or not id_aula:
            flash('Debe seleccionar un docente y un aula', 'danger')
            return redirect(url_for('directora.cursos'))
        existente = AsignacionDocente.query.filter_by(
            id_profesor=id_profesor,
            id_curso=id,
            id_aula_asignada=id_aula
        ).first()
        if existente:
            flash('Esta asignación ya existe', 'warning')
            return redirect(url_for('directora.cursos'))
        asignacion = AsignacionDocente(
            id_profesor=id_profesor,
            id_curso=id,
            id_aula_asignada=id_aula
        )
        db.session.add(asignacion)
        db.session.commit()
        flash('Docente asignado al curso exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al asignar: {str(e)}', 'danger')
    return redirect(url_for('directora.cursos'))


# ============================================================
# 13. CURSOS - Eliminar (desactivar)
# ============================================================
@directora_bp.route('/cursos/eliminar/<id>', methods=['POST'])
@login_required
@role_required('director')
def eliminar_curso(id):
    curso = Curso.query.get(id)
    if curso:
        curso.estado_curso = 'Inactivo'
        db.session.commit()
        flash('Curso desactivado', 'success')
    else:
        flash('Curso no encontrado', 'danger')
    return redirect(url_for('directora.cursos'))


# ============================================================
# 14. GRADOS - Gestionar
# ============================================================
@directora_bp.route('/grados', methods=['GET', 'POST'])
@login_required
@role_required('director')
def grados():
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear':
                nombre = request.form.get('nombre_grado', '').strip()
                id_nivel = request.form.get('id_nivel')
                if not nombre or not id_nivel:
                    flash('Nombre y nivel son obligatorios', 'danger')
                    return redirect(url_for('directora.grados'))
                nivel = Nivel.query.get(id_nivel)
                if not nivel:
                    flash('Nivel no encontrado', 'danger')
                    return redirect(url_for('directora.grados'))
                if Grado.query.filter_by(nombre_grado=nombre, id_nivel=id_nivel).first():
                    flash('El grado ya existe en este nivel', 'danger')
                    return redirect(url_for('directora.grados'))
                g = Grado(nombre_grado=nombre, id_nivel=id_nivel)
                db.session.add(g)
                db.session.commit()
                flash('Grado creado', 'success')
            elif accion == 'editar':
                g = Grado.query.get(request.form.get('id'))
                if g:
                    g.nombre_grado = request.form.get('nombre_grado', g.nombre_grado)
                    g.id_nivel = request.form.get('id_nivel', g.id_nivel)
                    db.session.commit()
                    flash('Grado actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('directora.grados'))

    niveles = Nivel.query.all()
    grados_list = Grado.query.options(joinedload(Grado.nivel), joinedload(Grado.secciones)).all()
    return render_template('grados.html' if 'grados.html' in dir()
        else 'dashboard_directora.html', niveles=niveles, grados=grados_list)


# ============================================================
# 15. SECCIONES - Gestionar
# ============================================================
@directora_bp.route('/secciones', methods=['GET', 'POST'])
@login_required
@role_required('director')
def secciones():
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear':
                nombre = request.form.get('nombre_seccion', '').strip()
                id_grado = request.form.get('id_grado')
                if not nombre or not id_grado:
                    flash('Nombre y grado son obligatorios', 'danger')
                    return redirect(url_for('directora.secciones'))
                if Seccion.query.filter_by(nombre_seccion=nombre, id_grado=id_grado).first():
                    flash('La sección ya existe en este grado', 'danger')
                    return redirect(url_for('directora.secciones'))
                s = Seccion(nombre_seccion=nombre, id_grado=id_grado)
                db.session.add(s)
                db.session.commit()
                flash('Sección creada', 'success')
            elif accion == 'editar':
                s = Seccion.query.get(request.form.get('id'))
                if s:
                    s.nombre_seccion = request.form.get('nombre_seccion', s.nombre_seccion)
                    s.id_grado = request.form.get('id_grado', s.id_grado)
                    db.session.commit()
                    flash('Sección actualizada', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('directora.secciones'))

    niveles = Nivel.query.all()
    grados_list = Grado.query.options(joinedload(Grado.nivel), joinedload(Grado.secciones)).all()
    secciones_list = Seccion.query.options(joinedload(Seccion.grado).joinedload(Grado.nivel)).all()
    return render_template('secciones.html' if 'secciones.html' in dir()
        else 'dashboard_directora.html',
        niveles=niveles, grados=grados_list, secciones=secciones_list)


# ============================================================
# 16. PERIODOS - Gestionar
# ============================================================
@directora_bp.route('/periodos', methods=['GET', 'POST'])
@login_required
@role_required('director')
def periodos():
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear':
                nombre = request.form.get('nombre_periodo', '').strip()
                if not nombre:
                    flash('El nombre del periodo es obligatorio', 'danger')
                    return redirect(url_for('directora.periodos'))
                if PeriodoAcademico.query.filter_by(nombre_periodo=nombre).first():
                    flash('El nombre del periodo ya existe', 'danger')
                    return redirect(url_for('directora.periodos'))
                p = PeriodoAcademico(
                    nombre_periodo=nombre,
                    fecha_inicio=datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date(),
                    fecha_fin=datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
                )
                db.session.add(p)
                db.session.commit()
                flash('Periodo académico creado', 'success')
            elif accion == 'editar':
                p = PeriodoAcademico.query.get(request.form.get('id'))
                if p:
                    p.nombre_periodo = request.form.get('nombre_periodo', p.nombre_periodo)
                    try:
                        p.fecha_inicio = datetime.strptime(request.form.get('fecha_inicio'), '%Y-%m-%d').date()
                        p.fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        pass
                    db.session.commit()
                    flash('Periodo actualizado', 'success')
            elif accion == 'toggle':
                p = PeriodoAcademico.query.get(request.form.get('id'))
                if p:
                    if not p.estado_activo:
                        PeriodoAcademico.query.filter(
                            PeriodoAcademico.estado_activo == True,
                            PeriodoAcademico.id != p.id
                        ).update({'estado_activo': False})
                    p.estado_activo = not p.estado_activo
                    db.session.commit()
                    flash('Periodo actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('directora.periodos'))

    periodos_list = PeriodoAcademico.query.order_by(PeriodoAcademico.fecha_inicio.desc()).all()
    return render_template('periodos.html' if 'periodos.html' in dir()
        else 'dashboard_directora.html', periodos=periodos_list)


# ============================================================
# 17. AULAS - Gestionar aulas_asignadas
# ============================================================
@directora_bp.route('/aulas', methods=['GET', 'POST'])
@login_required
@role_required('director')
def aulas():
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear':
                id_periodo = request.form.get('id_periodo_academico')
                id_seccion = request.form.get('id_seccion')
                if not id_periodo or not id_seccion:
                    flash('Periodo y sección son obligatorios', 'danger')
                    return redirect(url_for('directora.aulas'))
                existe = AulaAsignada.query.filter_by(
                    id_periodo_academico=id_periodo,
                    id_seccion=id_seccion
                ).first()
                if existe:
                    flash('Esta aula ya está asignada para este periodo', 'warning')
                    return redirect(url_for('directora.aulas'))
                aula = AulaAsignada(
                    id_periodo_academico=id_periodo,
                    id_seccion=id_seccion,
                    capacidad_maxima=request.form.get('capacidad_maxima', 30, type=int)
                )
                db.session.add(aula)
                db.session.commit()
                flash('Aula asignada creada', 'success')
            elif accion == 'editar':
                aula = AulaAsignada.query.get(request.form.get('id'))
                if aula:
                    aula.id_periodo_academico = request.form.get('id_periodo_academico', aula.id_periodo_academico)
                    aula.id_seccion = request.form.get('id_seccion', aula.id_seccion)
                    aula.capacidad_maxima = request.form.get('capacidad_maxima', aula.capacidad_maxima, type=int)
                    db.session.commit()
                    flash('Aula actualizada', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('directora.aulas'))

    aulas_list = AulaAsignada.query.options(
        joinedload(AulaAsignada.periodo),
        joinedload(AulaAsignada.seccion)
    ).all()
    periodos_list = PeriodoAcademico.query.all()
    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones_list = Seccion.query.all()
    return render_template('aulas.html' if 'aulas.html' in dir()
        else 'dashboard_directora.html',
        aulas=aulas_list, periodos=periodos_list,
        niveles=niveles, grados=grados, secciones=secciones_list)


# ============================================================
# 18. MATRICULAS - Listar
# ============================================================
@directora_bp.route('/matriculas', methods=['GET', 'POST'])
@login_required
@role_required('director')
def matriculas():
    if request.method == 'POST':
        accion = request.form.get('accion')
        if accion == 'toggle':
            mat = Matricula.query.get(request.form.get('id'))
            if mat:
                mat.estado_matricula = 'Inactivo' if mat.estado_matricula == 'Activo' else 'Activo'
                db.session.commit()
                flash(f'Matricula {"activada" if mat.estado_matricula == "Activo" else "desactivada"}', 'success')
        return redirect(url_for('directora.matriculas'))

    matriculas_list = Matricula.query.options(
        joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador),
        joinedload(Matricula.periodo)
    ).order_by(Matricula.fecha_matricula.desc()).all()
    return render_template('matriculas.html' if 'matriculas.html' in dir()
        else 'dashboard_directora.html', matriculas=matriculas_list)


# ============================================================
# 19. MATRICULAS - Nueva
# ============================================================
@directora_bp.route('/matriculas/nueva', methods=['GET', 'POST'])
@login_required
@role_required('director')
def nueva_matricula():
    if request.method == 'POST':
        try:
            id_estudiante = request.form.get('id_estudiante')
            id_periodo = request.form.get('id_periodo_academico')
            if not id_estudiante or not id_periodo:
                flash('Debe seleccionar un estudiante y un periodo', 'danger')
                return redirect(url_for('directora.nueva_matricula'))
            existe = Matricula.query.filter_by(
                id_estudiante=id_estudiante,
                id_periodo_academico=id_periodo
            ).first()
            if existe:
                flash('El estudiante ya está matriculado en este periodo', 'warning')
                return redirect(url_for('directora.matriculas'))
            mat = Matricula(
                id_estudiante=id_estudiante,
                id_periodo_academico=id_periodo
            )
            db.session.add(mat)
            db.session.commit()
            flash('Matrícula creada exitosamente', 'success')
            return redirect(url_for('directora.matriculas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('directora.nueva_matricula'))

    estudiantes = Estudiante.query.options(joinedload(Estudiante.colaborador)).all()
    periodos = PeriodoAcademico.query.filter_by(estado_activo=True).all()
    return render_template('nueva_matricula.html' if 'nueva_matricula.html' in dir()
        else 'dashboard_directora.html',
        estudiantes=estudiantes, periodos=periodos)


# ============================================================
# 20. INSCRIPCIONES - Gestionar
# ============================================================
@directora_bp.route('/inscripciones', methods=['GET', 'POST'])
@login_required
@role_required('director')
def inscripciones():
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear':
                id_matricula = request.form.get('id_matricula')
                id_aula = request.form.get('id_aula_asignada')
                if not id_matricula or not id_aula:
                    flash('Matrícula y aula son obligatorias', 'danger')
                    return redirect(url_for('directora.inscripciones'))
                existe = Inscripcion.query.filter_by(
                    id_matricula=id_matricula,
                    id_aula_asignada=id_aula
                ).first()
                if existe:
                    flash('La inscripción ya existe', 'warning')
                    return redirect(url_for('directora.inscripciones'))
                ins = Inscripcion(id_matricula=id_matricula, id_aula_asignada=id_aula)
                db.session.add(ins)
                db.session.commit()
                flash('Inscripción creada', 'success')
            elif accion == 'toggle':
                ins = Inscripcion.query.get(request.form.get('id'))
                if ins:
                    ins.estado_inscripcion = 'Retirado' if ins.estado_inscripcion == 'Asignado' else 'Asignado'
                    db.session.commit()
                    flash('Estado de inscripción actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('directora.inscripciones'))

    inscripciones_list = Inscripcion.query.options(
        joinedload(Inscripcion.matricula),
        joinedload(Inscripcion.aula),
        joinedload(Inscripcion.aula).joinedload(AulaAsignada.periodo)
    ).all()
    matriculas_list = Matricula.query.options(
        joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador),
        joinedload(Matricula.periodo)
    ).filter_by(estado_matricula='Activo').all()
    aulas_list = AulaAsignada.query.options(
        joinedload(AulaAsignada.seccion).joinedload(Seccion.grado),
        joinedload(AulaAsignada.periodo)
    ).all()
    return render_template('inscripciones.html' if 'inscripciones.html' in dir()
        else 'dashboard_directora.html',
        inscripciones=inscripciones_list,
        matriculas=matriculas_list, aulas=aulas_list)


# ============================================================
# 21. PLANES-PAGO - Gestionar
# ============================================================
@directora_bp.route('/planes-pago', methods=['GET', 'POST'])
@login_required
@role_required('director')
def planes_pago():
    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'crear':
                id_aula = request.form.get('id_aula_asignada')
                if not id_aula:
                    flash('Debe seleccionar un aula', 'danger')
                    return redirect(url_for('directora.planes_pago'))
                plan = PagoPlan(
                    id_aula_asignada=id_aula,
                    concepto_pago=request.form.get('concepto_pago', '').strip(),
                    monto_base=request.form.get('monto_base', type=float),
                    fecha_vencimiento=datetime.strptime(request.form.get('fecha_vencimiento'), '%Y-%m-%d').date()
                )
                db.session.add(plan)
                db.session.commit()
                flash('Plan de pago creado', 'success')
            elif accion == 'editar':
                plan = PagoPlan.query.get(request.form.get('id'))
                if plan:
                    plan.concepto_pago = request.form.get('concepto_pago', plan.concepto_pago)
                    plan.monto_base = request.form.get('monto_base', plan.monto_base, type=float)
                    try:
                        plan.fecha_vencimiento = datetime.strptime(
                            request.form.get('fecha_vencimiento'), '%Y-%m-%d'
                        ).date()
                    except (ValueError, TypeError):
                        pass
                    db.session.commit()
                    flash('Plan de pago actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('directora.planes_pago'))

    planes = PagoPlan.query.options(
        joinedload(PagoPlan.aula),
        joinedload(PagoPlan.aula).joinedload(AulaAsignada.periodo)
    ).all()
    aulas = AulaAsignada.query.options(
        joinedload(AulaAsignada.seccion).joinedload(Seccion.grado),
        joinedload(AulaAsignada.periodo)
    ).all()
    return render_template('planes_pago.html' if 'planes_pago.html' in dir()
        else 'dashboard_directora.html', planes=planes, aulas=aulas)


# ============================================================
# 22. PAGOS - Ver todos
# ============================================================
@directora_bp.route('/pagos')
@login_required
@role_required('director')
def pagos():
    pagos_list = Pago.query.options(
        joinedload(Pago.matricula),
        joinedload(Pago.matricula).joinedload(Matricula.periodo),
        joinedload(Pago.plan)
    ).order_by(Pago.fecha_registro.desc()).all()
    return render_template('estudiante_pagos.html' if 'estudiante_pagos.html' in dir()
        else 'dashboard_directora.html', pagos=pagos_list)


# ============================================================
# 23. SEGUIMIENTOS - Ver todos
# ============================================================
@directora_bp.route('/seguimientos')
@login_required
@role_required('director')
def seguimientos():
    seguimientos_list = SeguimientoEstudiante.query.options(
        joinedload(SeguimientoEstudiante.inscripcion),
        joinedload(SeguimientoEstudiante.registrador).joinedload(Colaborador.colaborador)
    ).order_by(SeguimientoEstudiante.fecha_registro.desc()).all()
    return render_template('seguimientos.html' if 'seguimientos.html' in dir()
        else 'dashboard_directora.html', seguimientos=seguimientos_list)


# ============================================================
# 24. REPORTES - Dashboard de reportes
# ============================================================
@directora_bp.route('/reportes')
@login_required
@role_required('director')
def reportes():
    niveles = Nivel.query.all()
    grados = Grado.query.all()
    secciones_list = Seccion.query.all()
    periodos = PeriodoAcademico.query.all()
    cursos_list = Curso.query.all()
    total_estudiantes = Estudiante.query.count()
    total_docentes = 0
    rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
    if rol_docente:
        total_docentes = UsuarioRol.query.filter_by(id_rol=rol_docente.id).count()
    total_matriculas_activas = Matricula.query.filter_by(estado_matricula='Activo').count()
    aulas_count = AulaAsignada.query.count()
    return render_template('reportes.html' if 'reportes.html' in dir()
        else 'dashboard_directora.html',
        niveles=niveles, grados=grados, secciones=secciones_list,
        periodos=periodos, cursos=cursos_list,
        total_estudiantes=total_estudiantes, total_docentes=total_docentes,
        total_matriculas_activas=total_matriculas_activas,
        aulas_count=aulas_count)


# ============================================================
# API endpoints (helper routes for AJAX)
# ============================================================

@directora_bp.route('/api/grados/<nivel_id>')
@login_required
@role_required('director')
def api_grados_por_nivel(nivel_id):
    grados = Grado.query.filter_by(id_nivel=nivel_id).all()
    return jsonify([{
        'id': g.id, 'nombre': g.nombre_grado,
        'secciones': [{'id': s.id, 'nombre': s.nombre_seccion} for s in g.secciones]
    } for g in grados])


@directora_bp.route('/api/secciones/<grado_id>')
@login_required
@role_required('director')
def api_secciones_por_grado(grado_id):
    secciones_list = Seccion.query.filter_by(id_grado=grado_id).all()
    return jsonify([{'id': s.id, 'nombre': s.nombre_seccion} for s in secciones_list])


@directora_bp.route('/api/aulas/<seccion_id>')
@login_required
@role_required('director')
def api_aulas_por_seccion(seccion_id):
    aulas_list = AulaAsignada.query.options(
        joinedload(AulaAsignada.periodo)
    ).filter_by(id_seccion=seccion_id).all()
    return jsonify([{
        'id': a.id,
        'periodo': a.periodo.nombre_periodo if a.periodo else '',
        'capacidad': a.capacidad_maxima
    } for a in aulas_list])


@directora_bp.route('/api/estudiantes')
@login_required
@role_required('director')
def api_estudiantes():
    estudiantes = Estudiante.query.options(
        joinedload(Estudiante.colaborador)
    ).all()
    return jsonify([{
        'id': e.id_colaborador,
        'codigo': e.codigo_estudiante,
        'nombre': e.colaborador.nombre_completo if e.colaborador else '',
        'numero_documento': e.colaborador.numero_documento if e.colaborador else ''
    } for e in estudiantes])


@directora_bp.route('/api/docentes')
@login_required
@role_required('director')
def api_docentes():
    rol_docente = Rol.query.filter_by(nombre_rol='docente').first()
    if not rol_docente:
        return jsonify([])
    ur_list = UsuarioRol.query.filter_by(id_rol=rol_docente.id).all()
    doc_ids = [ur.id_colaborador for ur in ur_list]
    docentes = Colaborador.query.filter(Colaborador.id.in_(doc_ids)).all() if doc_ids else []
    return jsonify([{
        'id': d.id,
        'nombre': d.nombre_completo,
        'numero_documento': d.numero_documento
    } for d in docentes])


@directora_bp.route('/api/estudiantes_por_aula/<aula_id>')
@login_required
@role_required('director')
def api_estudiantes_por_aula(aula_id):
    inscripciones = Inscripcion.query.options(
        joinedload(Inscripcion.matricula)
    ).filter_by(id_aula_asignada=aula_id, estado_inscripcion='Asignado').all()
    return jsonify([{
        'id': ins.matricula.id_estudiante,
        'nombre': ins.matricula.estudiante.colaborador.nombre_completo if ins.matricula and ins.matricula.estudiante and ins.matricula.estudiante.colaborador else ''
    } for ins in inscripciones])


@directora_bp.route('/api/justificaciones/<id>/revisar', methods=['POST'])
@login_required
@role_required('director')
def api_revisar_justificacion(id):
    just = Justificacion.query.get(id)
    if not just:
        return jsonify({'success': False, 'error': 'No encontrada'}), 404
    data = request.get_json() or request.form
    just.motivo_justificacion = data.get('comentario', just.motivo_justificacion)
    db.session.commit()
    return jsonify({'success': True})


@directora_bp.route('/api/documentos/<id>/revisar', methods=['POST'])
@login_required
@role_required('director')
def api_revisar_documento(id):
    doc = DocumentoDocente.query.get(id)
    if not doc:
        return jsonify({'success': False, 'error': 'No encontrado'}), 404


@directora_bp.route('/asignar_curso_docente/<id>', methods=['POST'])
@login_required
@role_required('director')
def asignar_curso_docente(id):
    curso_id = request.form.get('curso_id') or request.json.get('curso_id')
    aula_id = request.form.get('aula_id') or request.json.get('aula_id')
    if not curso_id:
        return jsonify({'ok': False, 'error': 'curso_id requerido'})
    existe = AsignacionDocente.query.filter_by(
        id_profesor=id, id_curso=curso_id
    ).first()
    if existe:
        return jsonify({'ok': False, 'error': 'Ya asignado'})
    asig = AsignacionDocente(
        id_profesor=id,
        id_curso=curso_id,
        id_aula_asignada=aula_id or ''
    )
    db.session.add(asig)
    db.session.commit()
    return jsonify({'ok': True, 'id': str(asig.id)})


@directora_bp.route('/remover_curso_docente/<id>/<curso_id>', methods=['POST'])
@login_required
@role_required('director')
def remover_curso_docente(id, curso_id):
    asig = AsignacionDocente.query.filter_by(
        id_profesor=id, id_curso=curso_id
    ).first()
    if asig:
        db.session.delete(asig)
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'No encontrado'})


@directora_bp.route('/api/estudiantes_por_curso/<curso_id>')
@login_required
@role_required('director')
def api_estudiantes_por_curso(curso_id):
    asignaciones = AsignacionDocente.query.filter_by(id_curso=curso_id).all()
    aula_ids = [a.id_aula_asignada for a in asignaciones if a.id_aula_asignada]
    inscripciones = Inscripcion.query.filter(
        Inscripcion.id_aula_asignada.in_(aula_ids),
        Inscripcion.estado_inscripcion == 'Asignado'
    ).options(
        joinedload(Inscripcion.matricula).joinedload(Matricula.estudiante).joinedload(Estudiante.colaborador)
    ).all() if aula_ids else []
    result = []
    for ins in inscripciones:
        c = ins.matricula.estudiante.colaborador if ins.matricula and ins.matricula.estudiante else None
        if c:
            result.append({'id': str(c.id), 'nombre': c.nombre_completo})
    return jsonify(result)
    doc.nombre_archivo = request.form.get('comentario', doc.nombre_archivo)
    db.session.commit()
    return jsonify({'success': True})


# ========= ADDITIONAL ENDPOINTS for dashboard =========

@directora_bp.route('/api/horarios_por_seccion/<seccion_id>')
@login_required
@role_required('director')
def api_horarios_por_seccion(seccion_id):
    seccion = Seccion.query.get(seccion_id)
    if not seccion:
        return jsonify([])
    aulas = AulaAsignada.query.filter_by(id_seccion=seccion_id).all()
    aula_ids = [a.id for a in aulas]
    asignaciones = AsignacionDocente.query.filter(AsignacionDocente.id_aula_asignada.in_(aula_ids)).all() if aula_ids else []
    result = []
    for asig in asignaciones:
        result.append({
            'id': str(asig.id),
            'dia_semana': 1,
            'hora_inicio': '08:00',
            'curso_nombre': asig.curso.nombre_curso if asig.curso else '-',
            'docente_nombre': asig.profesor.nombre_completo if asig.profesor else '-'
        })
    return jsonify(result)


@directora_bp.route('/api/horario_crear', methods=['POST'])
@login_required
@role_required('director')
def api_horario_crear():
    return jsonify({'success': True, 'message': 'Horario creado (simulado)'})


@directora_bp.route('/api/horario_eliminar/<id>', methods=['DELETE'])
@login_required
@role_required('director')
def api_horario_eliminar(id):
    return jsonify({'success': True})


@directora_bp.route('/api/cursos_por_seccion/<seccion_id>')
@login_required
@role_required('director')
def api_cursos_por_seccion(seccion_id):
    seccion = Seccion.query.get(seccion_id)
    if not seccion:
        return jsonify([])
    aulas = AulaAsignada.query.filter_by(id_seccion=seccion_id).all()
    aula_ids = [a.id for a in aulas]
    asignaciones = AsignacionDocente.query.filter(AsignacionDocente.id_aula_asignada.in_(aula_ids)).all() if aula_ids else []
    seen = set()
    result = []
    for asig in asignaciones:
        if asig.curso and asig.curso.id not in seen:
            seen.add(asig.curso.id)
            result.append({'id': str(asig.curso.id), 'nombre': asig.curso.nombre_curso})
    return jsonify(result)


@directora_bp.route('/api/notas_por_curso', methods=['GET', 'POST'])
@login_required
@role_required('director')
def api_notas_por_curso():
    return jsonify([])


@directora_bp.route('/api/notas_guardar', methods=['POST'])
@login_required
@role_required('director')
def api_notas_guardar():
    return jsonify({'success': True})


@directora_bp.route('/api/alumnos')
@login_required
@role_required('director')
def api_alumnos():
    alumnos = Estudiante.query.options(joinedload(Estudiante.colaborador)).all()
    result = []
    for a in alumnos:
        result.append({
            'id': str(a.id),
            'dni': a.colaborador.numero_documento if a.colaborador else '',
            'nombres': a.colaborador.nombres if a.colaborador else '',
            'nombre_completo': a.colaborador.nombre_completo if a.colaborador else '',
            'correo': a.colaborador.correo if a.colaborador else '',
            'activo': a.colaborador.estado_activo if a.colaborador else True
        })
    return jsonify(result)


@directora_bp.route('/api/actualizar_metodo_pago', methods=['POST'])
@login_required
@role_required('director')
def api_actualizar_metodo_pago():
    pago_id = request.form.get('pago_id') or request.json.get('pago_id') if request.is_json else None
    metodo = request.form.get('metodo_pago') or request.json.get('metodo_pago') if request.is_json else None
    pago = Pago.query.get(pago_id)
    if pago and metodo:
        pago.metodo_pago = metodo
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Datos invalidos'})


@directora_bp.route('/api/verificar_email', methods=['POST'])
@login_required
@role_required('director')
def api_verificar_email():
    email = request.form.get('correo') or (request.json.get('correo') if request.is_json else '')
    existe = Colaborador.query.filter_by(correo=email).first()
    return jsonify({'disponible': not existe})


@directora_bp.route('/niveles_crud', methods=['POST'])
@login_required
@role_required('director')
def niveles_crud():
    accion = request.form.get('accion', '')
    if accion == 'crear':
        nombre = request.form.get('nombre', '')
        if nombre:
            existe = Nivel.query.filter_by(nombre_nivel=nombre).first()
            if not existe:
                nivel = Nivel(nombre_nivel=nombre, descripcion_nivel='')
                db.session.add(nivel)
                db.session.commit()
                if request.form.get('ajax'):
                    return jsonify({'success': True, 'item': {'id': str(nivel.id), 'nombre': nivel.nombre_nivel, 'activo': True}})
                flash('Nivel creado', 'success')
    elif accion == 'toggle':
        nivel = Nivel.query.get(request.form.get('id'))
        if nivel:
            activo = not getattr(nivel, 'estado_activo', True) if hasattr(nivel, 'estado_activo') else True
            if hasattr(nivel, 'estado_activo'):
                nivel.estado_activo = activo
            db.session.commit()
    return redirect(url_for('directora.dashboard') + '#panel-academico')


@directora_bp.route('/grados_crud', methods=['POST'])
@login_required
@role_required('director')
def grados_crud():
    accion = request.form.get('accion', '')
    if accion == 'crear':
        nombre = request.form.get('nombre', '')
        nivel_id = request.form.get('nivel_id', '')
        if nombre and nivel_id:
            grado = Grado(nombre_grado=nombre, id_nivel=nivel_id)
            db.session.add(grado)
            db.session.commit()
            nivel = Nivel.query.get(nivel_id)
            if request.form.get('ajax'):
                return jsonify({'success': True, 'item': {
                    'id': str(grado.id), 'nombre': grado.nombre_grado,
                    'nivel_id': str(nivel_id), 'nivel_nombre': nivel.nombre_nivel if nivel else '',
                    'activo': True
                }})
            flash('Grado creado', 'success')
    elif accion == 'toggle':
        grado = Grado.query.get(request.form.get('id'))
        if grado:
            activo = not getattr(grado, 'estado_activo', True) if hasattr(grado, 'estado_activo') else True
            if hasattr(grado, 'estado_activo'):
                grado.estado_activo = activo
            db.session.commit()
    return redirect(url_for('directora.dashboard') + '#panel-academico')


@directora_bp.route('/secciones_crud', methods=['POST'])
@login_required
@role_required('director')
def secciones_crud():
    accion = request.form.get('accion', '')
    if accion == 'crear':
        nombre = request.form.get('nombre', '')
        grado_id = request.form.get('grado_id', '')
        if nombre and grado_id:
            seccion = Seccion(nombre_seccion=nombre, id_grado=grado_id)
            db.session.add(seccion)
            db.session.commit()
            grado = Grado.query.get(grado_id)
            if request.form.get('ajax'):
                return jsonify({'success': True, 'item': {
                    'id': str(seccion.id), 'nombre': seccion.nombre_seccion,
                    'grado_id': str(grado_id), 'grado_nombre': grado.nombre_grado if grado else '',
                    'activo': True
                }})
            flash('Seccion creada', 'success')
    elif accion == 'toggle':
        seccion = Seccion.query.get(request.form.get('id'))
        if seccion:
            activo = not getattr(seccion, 'estado_activo', True) if hasattr(seccion, 'estado_activo') else True
            if hasattr(seccion, 'estado_activo'):
                seccion.estado_activo = activo
            db.session.commit()
    return redirect(url_for('directora.dashboard') + '#panel-academico')


@directora_bp.route('/cursos_crud', methods=['POST'])
@login_required
@role_required('director')
def cursos_crud():
    accion = request.form.get('accion', '')
    if accion == 'crear':
        return redirect(url_for('directora.registrar_curso'))
    elif accion == 'toggle':
        curso = Curso.query.get(request.form.get('id'))
        if curso:
            activo = not getattr(curso, 'estado_curso', 'Activo') if hasattr(curso, 'estado_curso') else 'Activo'
            if hasattr(curso, 'estado_curso'):
                curso.estado_curso = 'Activo' if activo else 'Inactivo'
            db.session.commit()
    return redirect(url_for('directora.dashboard') + '#panel-academico')


@directora_bp.route('/toggle_colaborador/<id>', methods=['POST'])
@login_required
@role_required('director')
def toggle_colaborador(id):
    colaborador = Colaborador.query.get(id)
    if colaborador:
        colaborador.estado_activo = not colaborador.estado_activo
        db.session.commit()
        flash('Estado actualizado', 'success')
    return redirect(url_for('directora.dashboard') + '#panel-colaboradores')


@directora_bp.route('/toggle_estudiante/<id>', methods=['POST'])
@login_required
@role_required('director')
def toggle_estudiante(id):
    colaborador = Colaborador.query.get(id)
    if colaborador:
        colaborador.estado_activo = not colaborador.estado_activo
        db.session.commit()
        flash('Estado actualizado', 'success')
    return redirect(url_for('directora.dashboard') + '#panel-alumnos')


@directora_bp.route('/exportar_alumnos_csv')
@login_required
@role_required('director')
def exportar_alumnos_csv():
    import csv, io
    alumnos = Estudiante.query.options(joinedload(Estudiante.colaborador)).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['DNI', 'Nombres', 'Apellidos', 'Correo'])
    for a in alumnos:
        c = a.colaborador
        if c:
            cw.writerow([c.numero_documento, c.nombres, c.apellidos, c.correo])
    from flask import Response
    return Response(si.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=alumnos.csv'})


@directora_bp.route('/importar_alumnos_csv', methods=['POST'])
@login_required
@role_required('director')
def importar_alumnos_csv():
    return redirect(url_for('directora.dashboard') + '#panel-alumnos')


@directora_bp.route('/crear_estudiante', methods=['POST'])
@login_required
@role_required('director')
def crear_estudiante():
    return redirect(url_for('directora.registrar_alumno'))


@directora_bp.route('/crear_colaborador', methods=['POST'])
@login_required
@role_required('director')
def crear_colaborador():
    return redirect(url_for('directora.registrar_docente'))


@directora_bp.route('/generar_boleta', methods=['POST'])
@login_required
@role_required('director')
def generar_boleta():
    flash('Funcionalidad de boletas en desarrollo', 'info')
    return redirect(url_for('directora.dashboard') + '#panel-notas')


@directora_bp.route('/solicitar_reporte', methods=['POST'])
@login_required
@role_required('director')
def solicitar_reporte():
    flash('Solicitud enviada (funcionalidad en desarrollo)', 'info')
    return redirect(url_for('directora.dashboard') + '#panel-colaboradores')


@directora_bp.route('/editar_estudiante/<id>', methods=['POST'])
@login_required
@role_required('director')
def editar_estudiante(id):
    return redirect(url_for('directora.editar_alumno', id=id))


@directora_bp.route('/revisar_documento/<id>/<accion>', methods=['POST'])
@login_required
@role_required('director')
def revisar_documento(id, accion):
    doc = DocumentoDocente.query.get(id)
    if doc:
        if accion == 'aprobar':
            doc.nombre_archivo = 'aprobado'
        elif accion == 'rechazar':
            doc.nombre_archivo = 'rechazado'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No encontrado'}), 404
