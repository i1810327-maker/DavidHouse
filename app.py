from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from db import init_db, db
from models import Usuario, Grado, Seccion, Curso, Inscripcion, LogAcceso, Apoderado

# ====================== CONFIGURACIÓN ======================
app = Flask(__name__)
app.secret_key = "clave_super_segura_2026_ColegioSys"

bcrypt = Bcrypt(app)
init_db(app)

# ====================== DECORADORES ======================

def login_required(f):
    """Verifica que el usuario esté autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión primero', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def usuario_activo(f):
    """Verifica que el usuario esté activo"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = Usuario.query.get(session.get('usuario_id'))
        if not usuario or not usuario.activo:
            session.clear()
            flash('El usuario ha sido desactivado', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Verifica que el usuario tenga uno de los roles especificados"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('rol') not in roles:
                flash('No tienes permisos para acceder aquí', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_accion(accion):
    """Registra una acción en los logs"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resultado = f(*args, **kwargs)
            usuario_id = session.get('usuario_id')
            if usuario_id:
                log = LogAcceso(usuario_id=usuario_id, accion=accion)
                db.session.add(log)
                db.session.commit()
            return resultado
        return decorated_function
    return decorator

def verificar_permisos(f):
    """Decorador que combina login_required, usuario_activo"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión', 'danger')
            return redirect(url_for('login'))
        
        usuario = Usuario.query.get(session.get('usuario_id'))
        if not usuario or not usuario.activo:
            session.clear()
            flash('Usuario no válido', 'danger')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# ====================== FUNCIONES AUXILIARES ======================

def crear_usuario_desde_form(form_data, rol):
    """Crea un objeto Usuario desde datos de formulario"""
    return Usuario(
        dni=form_data.get('dni'),
        nombres=form_data.get('nombres'),
        apellido_paterno=form_data.get('apellido_paterno'),
        apellido_materno=form_data.get('apellido_materno'),
        correo=form_data.get('correo'),
        telefono_principal=form_data.get('telefono_principal') if rol == 'docente' else None,
        telefono_secundario=form_data.get('telefono_secundario') if rol == 'docente' else None,
        clave=bcrypt.generate_password_hash(form_data.get('clave')).decode('utf-8'),
        rol=rol,
        grado_id=form_data.get('grado_id') if rol == 'alumno' else None,
        seccion_id=form_data.get('seccion_id') if rol == 'alumno' else None,
        profesion=form_data.get('profesion') if rol == 'docente' else None,
        tiene_especialidad=bool(form_data.get('tiene_especialidad')) if rol == 'docente' else False,
        descripcion_especialidad=form_data.get('descripcion_especialidad') if rol == 'docente' and form_data.get('tiene_especialidad') else None
    )

# ====================== RUTAS PÚBLICAS ======================

@app.route('/')
def index():
    """Redirige al dashboard o login según autenticación"""
    if 'usuario_id' in session:
        rol = session.get('rol')
        if rol == 'directora':
            return redirect(url_for('directora_dashboard'))
        elif rol == 'docente':
            return redirect(url_for('docente_dashboard'))
        elif rol == 'alumno':
            return redirect(url_for('alumno_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Autenticación de usuarios"""
    if request.method == 'POST':
        correo = request.form.get('correo')
        clave = request.form.get('clave')

        try:
            usuario = Usuario.query.filter_by(correo=correo).first()
        except SQLAlchemyError:
            flash('Error interno en el inicio de sesión. Intenta nuevamente.', 'danger')
            return render_template('login.html')

        if usuario and bcrypt.check_password_hash(usuario.clave, clave):
            if not usuario.activo:
                flash('Usuario inactivo', 'danger')
                return redirect(url_for('login'))
            
            session['usuario_id'] = usuario.id
            session['rol'] = usuario.rol
            session['nombres'] = usuario.nombres
            
            # Registrar acceso
            log = LogAcceso(usuario_id=usuario.id, accion='Inicio de sesión')
            db.session.add(log)
            db.session.commit()

            if usuario.rol == 'directora':
                return redirect(url_for('directora_dashboard'))
            elif usuario.rol == 'docente':
                return redirect(url_for('docente_dashboard'))
            elif usuario.rol == 'alumno':
                return redirect(url_for('alumno_dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Cierra sesión del usuario"""
    usuario_id = session.get('usuario_id')
    if usuario_id:
        log = LogAcceso(usuario_id=usuario_id, accion='Cierre de sesión')
        db.session.add(log)
        db.session.commit()
    
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))

@app.route('/perfil')
@login_required
def perfil():
    """Muestra el perfil del usuario"""
    usuario = Usuario.query.get(session.get('usuario_id'))
    return render_template('perfil.html', usuario=usuario)

@app.route('/directora/colaboradores')
@verificar_permisos
@role_required('directora')
def colaboradores():
    """Lista todos los docentes (colaboradores)"""
    docentes = Usuario.query.filter_by(rol='docente').all()
    return render_template('colaboradores.html', docentes=docentes)

@app.route('/directora/estudiantes')
@verificar_permisos
@role_required('directora')
def estudiantes():
    """Lista todos los alumnos (estudiantes)"""
    alumnos = Usuario.query.filter_by(rol='alumno').all()
    return render_template('estudiantes.html', alumnos=alumnos)

# ====================== RUTAS DIRECTORA ======================

@app.route('/directora/dashboard')
@verificar_permisos
@role_required('directora')
def directora_dashboard():
    """Dashboard de directora"""
    alumnos = Usuario.query.filter_by(rol='alumno').count()
    docentes_list = Usuario.query.filter_by(rol='docente').all()
    docentes = len(docentes_list)
    
    return render_template('dashboard_directora.html', 
                         usuarios_totales=alumnos + docentes,
                         alumnos=alumnos,
                         docentes=docentes_list,
                         docentes_count=docentes)

@app.route('/directora/registrar_alumno', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Registrar alumno')
def registrar_alumno():
    """Registra un nuevo alumno"""
    if request.method == 'POST':
        try:
            nuevo_alumno = crear_usuario_desde_form(request.form, 'alumno')
            if nuevo_alumno.seccion_id:
                seccion = Seccion.query.get(nuevo_alumno.seccion_id)
                nuevo_alumno.grado_id = seccion.grado_id if seccion else None
            db.session.add(nuevo_alumno)
            db.session.flush()
            
            # Crear apoderado
            nuevo_apoderado = Apoderado(
                alumno_id=nuevo_alumno.id,
                nombres=request.form.get('apoderado_nombres'),
                apellido_paterno=request.form.get('apoderado_apellido_paterno'),
                apellido_materno=request.form.get('apoderado_apellido_materno'),
                telefono_principal=request.form.get('apoderado_telefono_principal'),
                telefono_secundario=request.form.get('apoderado_telefono_secundario'),
                es_apoderado=bool(request.form.get('es_apoderado'))
            )
            db.session.add(nuevo_apoderado)
            
            db.session.commit()
            flash(f'Alumno {nuevo_alumno.nombres} y su apoderado registrados exitosamente', 'success')
            return redirect(url_for('directora_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'danger')
    
    secciones = Seccion.query.filter_by(activo=True).all()
    grados = Grado.query.filter_by(activo=True).all()
    
    # Convertir grados a formato serializable para JavaScript
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id,
            'nombre': grado.nombre,
            'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones]
        }
        grados_data.append(grado_dict)
    
    return render_template('usuarios_form.html', 
                           secciones=secciones, 
                           grados=grados,
                           grados_data=grados_data)

@app.route('/directora/registrar_docente', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Registrar docente')
def registrar_docente():
    """Registra un nuevo docente"""
    if request.method == 'POST':
        try:
            nuevo_docente = crear_usuario_desde_form(request.form, 'docente')
            db.session.add(nuevo_docente)
            db.session.commit()
            flash(f'Docente {nuevo_docente.nombres} registrado exitosamente', 'success')
            return redirect(url_for('directora_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'danger')
    
    return render_template('docentes_form.html')

@app.route('/directora/listar_alumnos')
@verificar_permisos
@role_required('directora')
def listar_alumnos():
    """Lista todos los alumnos"""
    alumnos = Usuario.query.filter_by(rol='alumno').all()
    return render_template('listar_alumnos.html', alumnos=alumnos)

@app.route('/directora/listar_docentes')
@verificar_permisos
@role_required('directora')
def listar_docentes():
    """Lista todos los docentes"""
    docentes = Usuario.query.filter_by(rol='docente').all()
    return render_template('listar_docentes.html', docentes=docentes)

@app.route('/directora/editar_alumno/<int:id>', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Editar alumno')
def editar_alumno(id):
    """Editar alumno"""
    alumno = Usuario.query.get_or_404(id)
    if alumno.rol != 'alumno':
        flash('Usuario no es alumno', 'danger')
        return redirect(url_for('listar_alumnos'))
    
    if request.method == 'POST':
        try:
            alumno.dni = request.form.get('dni')
            alumno.nombres = request.form.get('nombres')
            alumno.apellido_paterno = request.form.get('apellido_paterno')
            alumno.apellido_materno = request.form.get('apellido_materno')
            alumno.correo = request.form.get('correo')
            alumno.seccion_id = request.form.get('seccion_id')
            if alumno.seccion_id:
                seccion = Seccion.query.get(alumno.seccion_id)
                alumno.grado_id = seccion.grado_id if seccion else None
            
            # Actualizar o crear apoderado
            apoderado = Apoderado.query.filter_by(alumno_id=alumno.id).first()
            if apoderado:
                apoderado.nombres = request.form.get('apoderado_nombres')
                apoderado.apellido_paterno = request.form.get('apoderado_apellido_paterno')
                apoderado.apellido_materno = request.form.get('apoderado_apellido_materno')
                apoderado.telefono_principal = request.form.get('apoderado_telefono_principal')
                apoderado.telefono_secundario = request.form.get('apoderado_telefono_secundario')
                apoderado.es_apoderado = bool(request.form.get('es_apoderado'))
            else:
                # Crear nuevo apoderado si no existe
                nuevo_apoderado = Apoderado(
                    alumno_id=alumno.id,
                    nombres=request.form.get('apoderado_nombres'),
                    apellido_paterno=request.form.get('apoderado_apellido_paterno'),
                    apellido_materno=request.form.get('apoderado_apellido_materno'),
                    telefono_principal=request.form.get('apoderado_telefono_principal'),
                    telefono_secundario=request.form.get('apoderado_telefono_secundario'),
                    es_apoderado=bool(request.form.get('es_apoderado'))
                )
                db.session.add(nuevo_apoderado)
            
            db.session.commit()
            flash('Alumno y apoderado actualizados exitosamente', 'success')
            return redirect(url_for('listar_alumnos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    grados = Grado.query.filter_by(activo=True).all()
    secciones = Seccion.query.filter_by(activo=True).all()
    apoderado = Apoderado.query.filter_by(alumno_id=alumno.id).first()
    return render_template('editar_alumno.html', alumno=alumno, grados=grados, secciones=secciones, apoderado=apoderado)

@app.route('/directora/editar_docente/<int:id>', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Editar docente')
def editar_docente(id):
    """Editar docente"""
    docente = Usuario.query.get_or_404(id)
    if docente.rol != 'docente':
        flash('Usuario no es docente', 'danger')
        return redirect(url_for('listar_docentes'))
    
    if request.method == 'POST':
        try:
            docente.dni = request.form.get('dni')
            docente.nombres = request.form.get('nombres')
            docente.apellido_paterno = request.form.get('apellido_paterno')
            docente.apellido_materno = request.form.get('apellido_materno')
            docente.correo = request.form.get('correo')
            docente.telefono_principal = request.form.get('telefono_principal')
            docente.telefono_secundario = request.form.get('telefono_secundario')
            docente.profesion = request.form.get('profesion')
            docente.tiene_especialidad = bool(request.form.get('tiene_especialidad'))
            docente.descripcion_especialidad = request.form.get('descripcion_especialidad') if request.form.get('tiene_especialidad') else None
            db.session.commit()
            flash('Docente actualizado exitosamente', 'success')
            return redirect(url_for('listar_docentes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    return render_template('editar_docente.html', docente=docente)

@app.route('/directora/eliminar_alumno/<int:id>', methods=['POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Eliminar alumno')
def eliminar_alumno(id):
    """Eliminar alumno"""
    alumno = Usuario.query.get_or_404(id)
    if alumno.rol != 'alumno':
        flash('Usuario no es alumno', 'danger')
        return redirect(url_for('listar_alumnos'))
    
    try:
        # Eliminar apoderados relacionados primero (por la foreign key)
        Apoderado.query.filter_by(alumno_id=alumno.id).delete()
        db.session.delete(alumno)
        db.session.commit()
        flash('Alumno y apoderado eliminados exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('listar_alumnos'))

@app.route('/directora/eliminar_docente/<int:id>', methods=['POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Eliminar docente')
def eliminar_docente(id):
    """Eliminar docente"""
    docente = Usuario.query.get_or_404(id)
    if docente.rol != 'docente':
        flash('Usuario no es docente', 'danger')
        return redirect(url_for('listar_docentes'))
    
    try:
        db.session.delete(docente)
        db.session.commit()
        flash('Docente eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('listar_docentes'))

@app.route('/directora/cambiar_clave', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
def directora_cambiar_clave():
    """Cambiar contraseña de directora"""
    if request.method == 'POST':
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')
        actual = request.form.get('actual')

        usuario = Usuario.query.get(session['usuario_id'])

        if not bcrypt.check_password_hash(usuario.clave, actual):
            flash('Contraseña actual incorrecta', 'danger')
            return redirect(url_for('directora_cambiar_clave'))

        if nueva != confirmar:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('directora_cambiar_clave'))

        usuario.clave = bcrypt.generate_password_hash(nueva).decode('utf-8')
        db.session.commit()
        
        log = LogAcceso(usuario_id=usuario.id, accion='Cambio de contraseña')
        db.session.add(log)
        db.session.commit()
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('directora_dashboard'))
    
    return render_template('cambiar_clave.html')

# ====================== RUTAS DOCENTE ======================

@app.route('/docente/dashboard')
@verificar_permisos
@role_required('docente')
def docente_dashboard():
    """Dashboard de docente"""
    usuario = Usuario.query.get(session.get('usuario_id'))
    cursos = Curso.query.filter_by(docente_id=usuario.id).all()
    
    estudiante_ids = set()
    seccion_nombres = set()
    for curso in cursos:
        if curso.seccion_rel:
            seccion_nombres.add(curso.seccion_rel.nombre)
        for ins in curso.inscripciones:
            estudiante_ids.add(ins.alumno_id)

    estudiantes = Usuario.query.filter(Usuario.id.in_(list(estudiante_ids))).all() if estudiante_ids else []
    total_estudiantes = len(estudiantes)
    secciones = ', '.join(sorted(seccion_nombres)) if seccion_nombres else 'No asignado'

    return render_template('dashboard_docente.html', 
                         usuario=usuario,
                         cursos=cursos,
                         estudiantes=estudiantes,
                         total_cursos=len(cursos),
                         total_estudiantes=total_estudiantes,
                         secciones=secciones)

@app.route('/docente/cambiar_clave', methods=['GET', 'POST'])
@verificar_permisos
@role_required('docente')
def docente_cambiar_clave():
    """Cambiar contraseña de docente"""
    if request.method == 'POST':
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')
        actual = request.form.get('actual')

        usuario = Usuario.query.get(session['usuario_id'])

        if not bcrypt.check_password_hash(usuario.clave, actual):
            flash('Contraseña actual incorrecta', 'danger')
            return redirect(url_for('docente_cambiar_clave'))

        if nueva != confirmar:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('docente_cambiar_clave'))

        usuario.clave = bcrypt.generate_password_hash(nueva).decode('utf-8')
        db.session.commit()
        
        log = LogAcceso(usuario_id=usuario.id, accion='Cambio de contraseña')
        db.session.add(log)
        db.session.commit()
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('docente_dashboard'))
    
    return render_template('cambiar_clave.html')

# ====================== RUTAS ALUMNO ======================

@app.route('/alumno/dashboard')
@verificar_permisos
@role_required('alumno')
def alumno_dashboard():
    """Dashboard de alumno"""
    usuario = Usuario.query.get(session.get('usuario_id'))
    inscripciones = Inscripcion.query.filter_by(alumno_id=usuario.id).all()
    calificaciones = [ins.calificacion for ins in inscripciones if ins.calificacion is not None]
    promedio = sum(calificaciones) / len(calificaciones) if calificaciones else None
    
    # Calcular asistencia promedio
    asistencias = [ins.asistencias for ins in inscripciones if ins.asistencias is not None]
    asistencia_promedio = sum(asistencias) / len(asistencias) if asistencias else 0
    
    apoderado = Apoderado.query.filter_by(alumno_id=usuario.id).first()
    
    return render_template('dashboard_alumno.html',
                         usuario=usuario,
                         inscripciones=inscripciones,
                         total_cursos=len(inscripciones),
                         promedio=promedio,
                         asistencia_promedio=int(asistencia_promedio),
                         apoderado=apoderado)


@app.route('/alumno/cambiar_clave', methods=['GET', 'POST'])
@verificar_permisos
@role_required('alumno')
def alumno_cambiar_clave():
    """Cambiar contraseña de alumno"""
    if request.method == 'POST':
        nueva = request.form.get('nueva')
        confirmar = request.form.get('confirmar')
        actual = request.form.get('actual')

        usuario = Usuario.query.get(session['usuario_id'])

        if not bcrypt.check_password_hash(usuario.clave, actual):
            flash('Contraseña actual incorrecta', 'danger')
            return redirect(url_for('alumno_cambiar_clave'))

        if nueva != confirmar:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('alumno_cambiar_clave'))

        usuario.clave = bcrypt.generate_password_hash(nueva).decode('utf-8')
        db.session.commit()
        
        log = LogAcceso(usuario_id=usuario.id, accion='Cambio de contraseña')
        db.session.add(log)
        db.session.commit()
        
        flash('Contraseña actualizada correctamente', 'success')
        return redirect(url_for('alumno_dashboard'))
    
    return render_template('cambiar_clave.html')

# ====================== MANEJO DE ERRORES ======================

@app.errorhandler(404)
def not_found(error):
    """Página no encontrada"""
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def server_error(error):
    """Error interno del servidor"""
    return render_template('error.html', error='Error interno del servidor'), 500

# ====================== EJECUCIÓN ======================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)