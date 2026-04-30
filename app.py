# ==========================================
# APLICACIÓN PRINCIPAL - SISTEMA DE GESTIÓN ESCOLAR
# ==========================================
# Este archivo contiene todas las rutas, configuración y lógica del servidor Flask

# --- IMPORTACIONES ---
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt  # Para encriptar contraseñas
from functools import wraps       # Para crear decoradores
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from db import db, init_db        # Configuración de base de datos
from models import Usuario, Grado, Seccion, Curso, LogAcceso, Apoderado  # Modelos ORM

# ====================== CONFIGURACIÓN ======================
app = Flask(__name__)
app.secret_key = "clave_super_segura_2026_ColegioSys"  # Clave para sesiones Flask

# Inicializar conexión a base de datos (Alwaysdata o local)
init_db(app)

bcrypt = Bcrypt(app)  # Inicializar encriptador de contraseñas

# ====================== DECORADORES (CONTROL DE ACCESO) ======================

# --- login_required ---
# Función: Obliga a iniciar sesión para acceder a una ruta protegida
# Uso: @login_required antes de una función de ruta
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión primero', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- usuario_activo ---
# Función: Verifica que el usuario no esté desactivado
# Uso: @usuario_activo antes de una función de ruta
def usuario_activo(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = Usuario.query.get(session.get('usuario_id'))
        if not usuario or not usuario.activo:
            session.clear()
            flash('El usuario ha sido desactivado', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- role_required ---
# Función: Limita el acceso según el rol del usuario (directora, docente, alumno)
# Uso: @role_required('directora', 'docente')
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('rol') not in roles:
                flash('No tienes permisos para acceder aquí', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- log_accion ---
# Función: Registra cada acción del usuario en la tabla LogAcceso (auditoría)
# Uso: @log_accion('Crear usuario')
def log_accion(accion):
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

# --- verificar_permisos ---
# Función: Decorador que combina login_required + usuario_activo
# Uso: @verificar_permisos antes de una función de ruta
def verificar_permisos(f):
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

# --- crear_usuario_desde_form ---
# Función: Crea un objeto Usuario desde datos de formulario
# Parámetros: form_data (datos del formulario), rol (directora, docente, alumno)
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
# Rutas accesibles sin autenticación

# --- / (raíz) ---
# Redirige al dashboard según el rol del usuario o al login si no está autenticado
@app.route('/')
def index():
    if 'usuario_id' in session:
        rol = session.get('rol')
        if rol == 'directora':
            return redirect(url_for('directora_dashboard'))
        elif rol == 'docente':
            return redirect(url_for('docente_dashboard'))
        elif rol == 'alumno':
            return redirect(url_for('alumno_dashboard'))
    return redirect(url_for('login'))

# --- /login ---
# Formulario de inicio de sesión. Verifica credenciales y crea sesión.
@app.route('/login', methods=['GET', 'POST'])
def login():
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
            
            # Registrar acceso en logs
            log = LogAcceso(usuario_id=usuario.id, accion='Inicio de sesión')
            db.session.add(log)
            db.session.commit()

            # Redirigir según rol
            if usuario.rol == 'directora':
                return redirect(url_for('directora_dashboard'))
            elif usuario.rol == 'docente':
                return redirect(url_for('docente_dashboard'))
            elif usuario.rol == 'alumno':
                return redirect(url_for('alumno_dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

# --- /logout ---
# Cierra la sesión del usuario y registra el cierre en logs
@app.route('/logout')
@login_required
def logout():
    usuario_id = session.get('usuario_id')
    if usuario_id:
        log = LogAcceso(usuario_id=usuario_id, accion='Cierre de sesión')
        db.session.add(log)
        db.session.commit()
    
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))

# --- /api/consultar-dni ---
# API para consultar datos de una persona por su DNI (RENIEC)
@app.route('/api/consultar-dni/<dni>', methods=['GET'])
def api_consultar_dni(dni):
    """
    Endpoint JSON que consulta datos por DNI usando la API de RENIEC
    
    Parámetro: dni (8 dígitos)
    Retorna: JSON con nombres, apellido_paterno, apellido_materno o error
    """
    try:
        # Consultar datos mediante el módulo ConsultaAPI
        resultado = ConsultaAPI.consultar_dni(dni)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({
            'error': f'Error al procesar la solicitud: {str(e)}',
            'nombres': '',
            'apellido_paterno': '',
            'apellido_materno': ''
        }), 500

# --- /perfil ---
# Muestra el perfil del usuario autenticado
@app.route('/perfil')
@login_required
def perfil():
    usuario = Usuario.query.get(session.get('usuario_id'))
    return render_template('perfil.html', usuario=usuario)

# --- /directora/colaboradores ---
# Lista todos los docentes del sistema (solo директор)
@app.route('/directora/colaboradores')
@verificar_permisos
@role_required('directora')
def colaboradores():
    docentes = Usuario.query.filter_by(rol='docente').all()
    return render_template('colaboradores.html', docentes=docentes)

# --- /directora/estudiantes ---
# Lista todos los alumnos del sistema (solo директор)
@app.route('/directora/estudiantes')
@verificar_permisos
@role_required('directora')
def estudiantes():
    alumnos = Usuario.query.filter_by(rol='alumno').all()
    return render_template('estudiantes.html', alumnos=alumnos)

# ====================== RUTAS DIRECTORA ======================
# Rutas exclusivas para la директор (administradora)

# --- /directora/dashboard ---
# Panel principal de la директор: muestra estadísticas de alumnos y docentes
@app.route('/directora/dashboard')
@verificar_permisos
@role_required('directora')
def directora_dashboard():
    alumnos = Usuario.query.filter_by(rol='alumno').count()
    docentes_list = Usuario.query.filter_by(rol='docente').all()
    docentes = len(docentes_list)
    
    return render_template('dashboard_directora.html', 
                         usuarios_totales=alumnos + docentes,
                         alumnos=alumnos,
                         docentes=docentes_list,
                         docentes_count=docentes)

# --- /directora/registrar_alumno ---
# Formulario para registrar un nuevo alumno con su apoderado
@app.route('/directora/registrar_alumno', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Registrar alumno')
def registrar_alumno():
    if request.method == 'POST':
        try:
            nuevo_alumno = crear_usuario_desde_form(request.form, 'alumno')
            if nuevo_alumno.seccion_id:
                seccion = Seccion.query.get(nuevo_alumno.seccion_id)
                nuevo_alumno.grado_id = seccion.grado_id if seccion else None
            db.session.add(nuevo_alumno)
            db.session.flush()
            
            # Crear apoderado linked al alumno
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
    
    # Convertir grados a JSON para JavaScript (selects dinámicos)
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

# --- /directora/registrar_docente ---
# Formulario para registrar un nuevo docente
@app.route('/directora/registrar_docente', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Registrar docente')
def registrar_docente():
    if request.method == 'POST':
        try:
            nuevo_docente = crear_usuario_desde_form(request.form, 'docente')
            db.session.add(nuevo_docente)
            db.session.flush()
            
            # Asignar docente como tutor de la sección seleccionada
            seccion_id = request.form.get('seccion_docente_id')
            if seccion_id:
                seccion = Seccion.query.get(seccion_id)
                if seccion:
                    seccion.docente_id = nuevo_docente.id
            
            db.session.commit()
            flash(f'Docente {nuevo_docente.nombres} registrado exitosamente', 'success')
            return redirect(url_for('directora_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'danger')
    
    # Obtener grados para el formulario
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id,
            'nombre': grado.nombre,
            'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    
    return render_template('docentes_form.html', grados_data=grados_data)

# --- /directora/listar_alumnos ---
# Lista todos los alumnos registrados (solo директор)
@app.route('/directora/listar_alumnos')
@verificar_permisos
@role_required('directora')
def listar_alumnos():
    alumnos = Usuario.query.filter_by(rol='alumno').all()
    return render_template('listar_alumnos.html', alumnos=alumnos)

# --- /directora/listar_docentes ---
# Lista todos los docentes registrados (solo директор)
@app.route('/directora/listar_docentes')
@verificar_permisos
@role_required('directora')
def listar_docentes():
    docentes = Usuario.query.filter_by(rol='docente').all()
    return render_template('listar_docentes.html', docentes=docentes)

# --- /directora/editar_alumno/<id> ---
# Formulario para editar los datos de un alumno y su apoderado
@app.route('/directora/editar_alumno/<int:id>', methods=['GET', 'POST'])
@verificar_permisos
@role_required('directora')
@log_accion('Editar alumno')
def editar_alumno(id):
    alumno = Usuario.query.get_or_404(id)
    if alumno.rol != 'alumno':
        flash('Usuario no es alumno', 'danger')
        return redirect(url_for('listar_alumnos'))
    
    if request.method == 'POST':
        try:
            # Actualizar datos del alumno
            alumno.dni = request.form.get('dni')
            alumno.nombres = request.form.get('nombres')
            alumno.apellido_paterno = request.form.get('apellido_paterno')
            alumno.apellido_materno = request.form.get('apellido_materno')
            alumno.correo = request.form.get('correo')
            alumno.seccion_id = request.form.get('seccion_id')
            if alumno.seccion_id:
                seccion = Seccion.query.get(alumno.seccion_id)
                alumno.grado_id = seccion.grado_id if seccion else None
            
            # Actualizar o crear apoderado linked al alumno
            apoderado = Apoderado.query.filter_by(alumno_id=alumno.id).first()
            if apoderado:
                apoderado.nombres = request.form.get('apoderado_nombres')
                apoderaApellido_paterno = request.form.get('apoderado_apellido_paterno')
                apoderaApellido_materno = request.form.get('apoderado_apellido_materno')
                apoderaTelefono_principal = request.form.get('apoderado_telefono_principal')
                apoderaTelefono_secundario = request.form.get('apoderado_telefono_secundario')
                apoderaEs_apoderado = bool(request.form.get('es_apoderado'))
            else:
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
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id,
            'nombre': grado.nombre,
            'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    return render_template('editar_alumno.html', alumno=alumno, grados=grados, secciones=secciones, apoderado=apoderado, grados_data=grados_data)

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
            
            # Actualizar sección/tutoría del docente
            seccion_id = request.form.get('seccion_docente_id')
            if seccion_id:
                seccion = Seccion.query.get(seccion_id)
                if seccion:
                    # Quitar al docente anterior de esa sección si existía
                    if docente.seccion_id:
                        seccion_anterior = Seccion.query.get(docente.seccion_id)
                        if seccion_anterior and seccion_anterior.docente_id == docente.id:
                            seccion_anterior.docente_id = None
                    # Asignar nuevo tutor
                    docente.seccion_id = seccion_id
                    seccion.docente_id = docente.id
            
            db.session.commit()
            flash('Docente actualizado exitosamente', 'success')
            return redirect(url_for('listar_docentes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    # Obtener grados para el formulario
    grados = Grado.query.filter_by(activo=True).all()
    grados_data = []
    for grado in grados:
        grado_dict = {
            'id': grado.id,
            'nombre': grado.nombre,
            'nivel': grado.nivel,
            'secciones': [{'id': s.id, 'nombre': s.nombre} for s in grado.secciones if s.activo]
        }
        grados_data.append(grado_dict)
    
    return render_template('editar_docente.html', docente=docente, grados_data=grados_data)

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
    docente = Usuario.query.get_or_400(id)
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
    estudiantes_por_seccion = {}
    for curso in cursos:
        if curso.seccion_rel:
            seccion_nombres.add(curso.seccion_rel.nombre)
            # Contar estudiantes por sección
            seccion_id = curso.seccion_rel.id
            if seccion_id not in estudiantes_por_seccion:
                estudiantes_por_seccion[seccion_id] = {
                    'nombre': curso.seccion_rel.nombre,
                    'grado': curso.seccion_rel.grado.nombre if curso.seccion_rel.grado else 'N/A',
                    'cantidad': 0
                }
            estudiantes_por_seccion[seccion_id]['cantidad'] += len(curso.inscripciones)
        for ins in curso.inscripciones:
            estudiante_ids.add(ins.alumno_id)

    estudiantes = Usuario.query.filter(Usuario.id.in_(list(estudiante_ids))).all() if estudiante_ids else []
    total_estudiantes = len(estudiantes)
    secciones = ', '.join(sorted(seccion_nombres)) if seccion_nombres else 'No asignado'

    # Datos de sección donde el docente es tutor
    seccion_tutor = Seccion.query.get(usuario.seccion_id) if usuario.seccion_id else None
    seccion_tutor_nombre = seccion_tutor.nombre if seccion_tutor else 'No asignado'
    seccion_tutor_grado = seccion_tutor.grado.nombre if seccion_tutor and seccion_tutor.grado else 'No asignado'
    seccion_tutor_cantidad = len(seccion_tutor.usuarios) if seccion_tutor else 0

    return render_template('dashboard_docente.html', 
                         usuario=usuario,
                         cursos=cursos,
                         estudiantes=estudiantes,
                         total_cursos=len(cursos),
                         total_estudiantes=total_estudiantes,
                         secciones=secciones,
                         estudiantes_por_seccion=estudiantes_por_seccion,
                         seccion_tutor_nombre=seccion_tutor_nombre,
                         seccion_tutor_grado=seccion_tutor_grado,
                         seccion_tutor_cantidad=seccion_tutor_cantidad)

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
    inscripciones = []  # Lista vacía ya que no se utiliza Inscripcion
    calificaciones = [ins.calificacion for ins in inscripciones if ins.calificacion is not None]
    promedio = sum(calificaciones) / len(calificaciones) if calificaciones else None
    
    # Calcular asistencia promedio
    asistencia = [ins.asistencia for ins in inscripciones if ins.asistencia is not None]
    asistencia_promedio = sum(asistencia) / len(asistencia) if asistencia else 0
    
    # Apoderado del alumno
    apoderado = Apoderado.query.filter_by(alumno_id=usuario.id).first()

    # Sección, docente tutor y compañeros de sección
    # Usar relaciones definidas en models.py: usuario.seccion_rel -> Seccion
    seccion = None
    docente_seccion = None
    cantidad_estudiantes_seccion = 0
    seccion_nombre = None
    grado_nombre = None
    
    if usuario.seccion_id:
        seccion = Seccion.query.get(usuario.seccion_id)
        if seccion:
            seccion_nombre = seccion.nombre
            if seccion.grado:
                grado_nombre = seccion.grado.nombre
            if seccion.docente:
                docente_seccion = seccion.docente.nombres
            # Contar estudiantes en la misma sección
            cantidad_estudiantes_seccion = Usuario.query.filter_by(
                seccion_id=seccion.id, 
                rol='alumno',
                activo=True
            ).count()

    return render_template('dashboard_alumno.html',
                         usuario=usuario,
                         inscripciones=inscripciones,
                         total_cursos=len(inscripciones),
                         promedio=promedio,
                         asistencia_promedio=int(asistencia_promedio),
                         apoderado=apoderado,
                         docente_seccion=docente_seccion,
                         cantidad_estudiantes_seccion=cantidad_estudiantes_seccion,
                         seccion_nombre=seccion_nombre,
                         grado_nombre=grado_nombre)


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
    app.run(debug=True)