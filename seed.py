"""Seed data: roles + admin user for Supabase."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app import app, bcrypt
from db import db
from models import Colaborador, Rol, Usuario, UsuarioRol

def seed():
    with app.app_context():
        if Rol.query.first():
            print("Roles ya existen, saltando seed")
            return

        roles_data = [
            ('directora', 'Directora del colegio - acceso total'),
            ('docente', 'Docente - gestiona cursos, notas y asistencia'),
            ('alumno', 'Alumno - visualiza notas, asistencia y pagos'),
        ]
        for nombre, desc in roles_data:
            r = Rol(nombre_rol=nombre, descripcion_rol=desc)
            db.session.add(r)
        db.session.flush()

        admin = Colaborador(
            tipo_documento='DNI',
            numero_documento='00000000',
            nombres='Admin',
            apellidos='Sistema',
            fecha_nacimiento='1990-01-01',
            genero='M',
            telefono_principal='999999999',
            direccion_fisica='Oficina Central',
        )
        db.session.add(admin)
        db.session.flush()

        usuario = Usuario(
            id_colaborador=admin.id,
            nombre_usuario='admin',
            contrasena_hash=bcrypt.generate_password_hash('Admin123!').decode('utf-8'),
            estado_activo=True,
        )
        db.session.add(usuario)

        rol_directora = Rol.query.filter_by(nombre_rol='directora').first()
        ur = UsuarioRol(id_colaborador=admin.id, id_rol=rol_directora.id)
        db.session.add(ur)

        db.session.commit()
        print("Seed completado: roles + admin creados")
        print("  Usuario: admin")
        print("  Clave: Admin123!")

if __name__ == '__main__':
    seed()
