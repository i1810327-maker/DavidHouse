# ==========================================
# SCRIPT DE INICIALIZACIÓN DE BASE DE DATOS
# ==========================================
# Este script crea las tablas e inserta datos de prueba en la base de datos.
# Uso: python init_db.py
# Credenciales creadas:
#   - Directora: admin@colegio.edu.pe / Admin2026
#   - Docente: docente@colegio.edu.pe / Docente2026
#   - Alumno: alumno@colegio.edu.pe / Alumno2026

from app import app, db, bcrypt
from models import Usuario, Grado, Seccion, Curso

def init_database():
    """Inicializa la BD con tablas y datos de prueba"""
    
    with app.app_context():
        # Crear todas las tablas
        print("🔧 Creando tablas...")
        db.create_all()
        print("✅ Tablas creadas correctamente\n")

        # Verificar si ya existen datos
        if Usuario.query.first():
            print("⚠️  La base de datos ya tiene datos. Abortando...")
            return

        # Crear Grados
        print("📖 Creando grados...")
        grados = [
            Grado(nombre="1º Primaria", nivel="primaria", descripcion="Primer grado de primaria"),
            Grado(nombre="2º Primaria", nivel="primaria", descripcion="Segundo grado de primaria"),
            Grado(nombre="3º Primaria", nivel="primaria", descripcion="Tercer grado de primaria"),
            Grado(nombre="Inicial 3", nivel="inicial", descripcion="Educación inicial 3 años"),
            Grado(nombre="Inicial 4", nivel="inicial", descripcion="Educación inicial 4 años"),
        ]
        for grado in grados:
            db.session.add(grado)
        db.session.commit()
        print("✅ Grados creados\n")

        # Crear Secciones
        print("📚 Creando secciones...")
        secciones = [
            Seccion(nombre="A", grado_id=1, capacidad=30),
            Seccion(nombre="B", grado_id=1, capacidad=30),
            Seccion(nombre="A", grado_id=2, capacidad=30),
            Seccion(nombre="B", grado_id=2, capacidad=30),
        ]
        for seccion in secciones:
            db.session.add(seccion)
        db.session.commit()
        print("✅ Secciones creadas\n")

        # Crear Usuarios (Admin, Docente, Alumno)
        print("👤 Creando usuarios...")
        usuarios = [
            Usuario(
                dni="12345678",
                nombres="Admin",
                apellido_paterno="Sistema",
                apellido_materno="Colegio",
                correo="admin@colegio.edu.pe",
                clave=bcrypt.generate_password_hash("Admin2026").decode('utf-8'),
                rol="directora",
                activo=True
            ),
            Usuario(
                dni="87654321",
                nombres="Juan",
                apellido_paterno="Pérez",
                apellido_materno="García",
                correo="docente@colegio.edu.pe",
                telefono_principal="999888777",
                telefono_secundario="988777666",
                clave=bcrypt.generate_password_hash("Docente2026").decode('utf-8'),
                rol="docente",
                profesion="Educación Primaria",
                tiene_especialidad=True,
                descripcion_especialidad="Especialista en Lengua y Literatura",
                activo=True
            ),
            Usuario(
                dni="11111111",
                nombres="Carlos",
                apellido_paterno="López",
                apellido_materno="Rodríguez",
                correo="alumno@colegio.edu.pe",
                clave=bcrypt.generate_password_hash("Alumno2026").decode('utf-8'),
                rol="alumno",
                grado_id=1,
                seccion_id=1,
                activo=True
            ),
        ]
        for usuario in usuarios:
            db.session.add(usuario)
        db.session.commit()
        print("✅ Usuarios creados\n")

        # Crear Cursos
        print("📚 Creando cursos...")
        cursos = [
            Curso(nombre="Matemática", grado_id=1, docente_id=2),
            Curso(nombre="Comunicación", grado_id=1, docente_id=2),
            Curso(nombre="Ciencia y Ambiente", grado_id=1, docente_id=2),
        ]
        for curso in cursos:
            db.session.add(curso)
        db.session.commit()
        print("✅ Cursos creados\n")

        print("=" * 50)
        print("✅ ¡Base de datos inicializada correctamente!")
        print("=" * 50)
        print("\nCredenciales de prueba:")
        print("  📌 Directora: admin@colegio.edu.pe / Admin2026")
        print("  📌 Docente: docente@colegio.edu.pe / Docente2026")
        print("  📌 Alumno: alumno@colegio.edu.pe / Alumno2026")

if __name__ == '__main__':
    init_database()
