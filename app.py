from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
import os, re
from dotenv import load_dotenv

load_dotenv()
from db import db, init_db
from models import (
    MensajeContacto, Colaborador, Rol, Usuario, UsuarioRol,
    LogAcceso, IntentoLogin, Baneo, Estudiante, Familiar,
    EstudianteFamiliar, PeriodoAcademico, Nivel, Grado, Seccion,
    Curso, AulaAsignada, Matricula, Inscripcion, AsignacionDocente,
    Asistencia, Justificacion, Evaluacion, Calificacion,
    SeguimientoEstudiante, CarpetaDocente, DocumentoDocente,
    PagoPlan, Pago
)
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave_super_segura_2026_ColegioSys')

MAX_INTENTOS_USUARIO = 3
TIEMPO_BANEO_MINUTOS = 5
VENTANA_TIEMPO_MINUTOS = 5

init_db(app)
bcrypt = Bcrypt(app)

def obtener_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

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

def log_login(nombre_usuario, ip, exitoso):
    try:
        log = LogAcceso(
            nombre_usuario_intentado=nombre_usuario,
            ip_direccion=ip,
            exitoso=exitoso
        )
        if exitoso:
            usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
            if usuario:
                log.id_colaborador = usuario.id_colaborador
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

def nota_a_letra(nota):
    if nota is None: return '-'
    if nota >= 18: return 'AD'
    if nota >= 16: return 'A'
    if nota >= 12: return 'B'
    return 'C'

app.jinja_env.globals.update(nota_a_letra=nota_a_letra)
app.jinja_env.globals.update(now=datetime.now)

@app.route('/')
def index():
    if 'usuario_id' in session:
        r = session.get('rol')
        if r == 'director': return redirect(url_for('directora.dashboard'))
        if r in ('docente', 'coordinador'): return redirect(url_for('docente.dashboard'))
        if r == 'alumno': return redirect(url_for('estudiante.dashboard'))
    return render_template('home.html')

@app.route('/contacto', methods=['POST'])
def contacto():
    try:
        msg = MensajeContacto(
            nombre_remitente=request.form.get('nombre', ''),
            correo_remitente=request.form.get('correo', ''),
            telefono_remitente=request.form.get('telefono', ''),
            asunto=request.form.get('asunto', ''),
            mensaje=request.form.get('mensaje', '')
        )
        db.session.add(msg)
        db.session.commit()
        flash('Gracias por contactarnos, te responderemos pronto.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error al enviar el mensaje. Intenta nuevamente.', 'danger')
    return redirect(url_for('index') + '#contacto')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre_usuario = request.form.get('usuario', '').strip()
        clave = request.form.get('clave', '')
        ip = obtener_ip()
        ahora = datetime.utcnow()

        baneo = Baneo.query.filter(
            db.or_(
                Baneo.id_colaborador == None,
                Baneo.ip_direccion == ip
            ),
            db.or_(
                Baneo.fecha_expiracion == None,
                Baneo.fecha_expiracion > ahora
            )
        ).first()
        if baneo:
            flash('Cuenta bloqueada. Intente más tarde.', 'danger')
            return render_template('login.html')

        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        if usuario and usuario.estado_activo and bcrypt.check_password_hash(usuario.contrasena_hash, clave):
            IntentoLogin.query.filter_by(ip_direccion=ip).delete()
            session.clear()

            roles = UsuarioRol.query.filter_by(id_colaborador=usuario.id_colaborador).join(Rol).all()
            session['usuario_id'] = str(usuario.id_colaborador)
            session['nombres'] = usuario.colaborador.nombre_completo
            session['roles'] = [r.rol.nombre_rol for r in roles]
            session['rol'] = session['roles'][0] if roles else 'alumno'

            log_login(nombre_usuario, ip, True)

            r = session['rol']
            if r == 'director': return redirect(url_for('directora.dashboard'))
            if r in ('docente', 'coordinador'): return redirect(url_for('docente.dashboard'))
            return redirect(url_for('estudiante.dashboard'))

        intento = IntentoLogin(
            ip_direccion=ip,
            intentos_fallidos=1,
            ultima_falla=ahora
        )
        db.session.merge(intento)
        db.session.commit()
        log_login(nombre_usuario, ip, False)

        desde = ahora - timedelta(minutes=VENTANA_TIEMPO_MINUTOS)
        intentos_recientes = IntentoLogin.query.filter(
            IntentoLogin.ip_direccion == ip,
            IntentoLogin.ultima_falla > desde
        ).count()
        if intentos_recientes >= MAX_INTENTOS_USUARIO:
            ban = Baneo(
                ip_direccion=ip,
                razon_baneo=f'Demasiados intentos fallidos desde {ip}',
                fecha_expiracion=ahora + timedelta(minutes=TIEMPO_BANEO_MINUTOS)
            )
            db.session.add(ban)
            db.session.commit()
            flash('Demasiados intentos. IP bloqueada por 5 minutos.', 'danger')
            return render_template('login.html')

        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.after_request
def add_cache_headers(response):
    if 'usuario_id' in session:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/recuperar_contrasena')
def recuperar_contrasena():
    return render_template('recuperar_contrasena.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada', 'success')
    resp = redirect(url_for('login'))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/perfil')
@login_required
def perfil():
    uid = request.args.get('id') or session.get('usuario_id')
    colaborador = Colaborador.query.get(uid)
    if not colaborador:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('index'))
    return render_template('perfil.html', usuario=colaborador)

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
    usuario = Usuario.query.get(uid)
    if not usuario or not bcrypt.check_password_hash(usuario.contrasena_hash, actual):
        flash('Contraseña actual incorrecta', 'danger')
        return redirect(url_for('perfil'))
    if len(nueva) < 8:
        flash('La contraseña debe tener al menos 8 caracteres', 'danger')
        return redirect(url_for('perfil'))
    usuario.contrasena_hash = bcrypt.generate_password_hash(nueva).decode('utf-8')
    db.session.commit()
    flash('Contraseña cambiada exitosamente', 'success')
    return redirect(url_for('perfil'))

from routes.routes_directora import directora_bp
from routes.routes_docente import docente_bp
from routes.routes_estudiante import estudiante_bp

app.register_blueprint(directora_bp)
app.register_blueprint(docente_bp)
app.register_blueprint(estudiante_bp)

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Error interno del servidor'), 500

if __name__ == '__main__':
    app.run(debug=True)
