# ==========================================
# SCRIPT DE INICIALIZACIÓN DE BASE DE DATOS
# ==========================================
# Este script crea las tablas e inserta datos de prueba en la base de datos.
# Uso: python init_db.py
# Credenciales creadas:
#   - Diretora: admin@colegio.edu.pe / Admin2026
#   - Docente: docente@colegio.edu.pe / Docente2026
#   - Alumno: alumno@colegio.edu.pe / Alumno2026

from app import app, db, bcrypt
from models import Usuario, Grado, Seccion, Curso, Inscripcion

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

        # Crear Usuario Directora
        print("👩‍💼 Creando usuario Directora...")
        directora = Usuario(
            dni="12345678",
            nombres="María",
            apellido_paterno="García",
            apellido_materno="López",
            correo="admin@colegio.edu.pe",
            clave=bcrypt.generate_password_hash("Admin2026").decode('utf-8'),
            rol="directora",
            activo=True
        )
        db.session.add(directora)
        db.session.commit()
        print("✅ Directora creada")
        print("   📧 Correo: admin@colegio.edu.pe")
        print("   🔑 Contraseña: Admin2026\n")

        # Crear Usuario Docente de Prueba
        print("👨‍🏫 Creando usuario Docente...")
        docente = Usuario(
            dni="87654321",
            nombres="Juan",
            apellido_paterno="Pérez",
            apellido_materno="Martínez",
            correo="docente@colegio.edu.pe",
            clave=bcrypt.generate_password_hash("Docente2026").decode('utf-8'),
            rol="docente",
            profesion="Licenciado en Educación Primaria",
            tiene_especialidad=True,
            descripcion_especialidad="Especialista en Matemáticas y Ciencias",
            seccion_id=1,
            activo=True
        )
        db.session.add(docente)
        db.session.commit()
        print("✅ Docente creado")
        print("   📧 Correo: docente@colegio.edu.pe")
        print("   🔑 Contraseña: Docente2026\n")

        # Crear Usuario Alumno de Prueba
        print("👨‍🎓 Creando usuario Alumno...")
        alumno = Usuario(
            dni="11111111",
            nombres="Carlos",
            apellido_paterno="Sánchez",
            apellido_materno="Rodríguez",
            correo="alumno@colegio.edu.pe",
            clave=bcrypt.generate_password_hash("Alumno2026").decode('utf-8'),
            rol="alumno",
            grado_id=1,
            seccion_id=1,
            activo=True
        )
        db.session.add(alumno)
        db.session.commit()
        print("✅ Alumno creado")
        print("   📧 Correo: alumno@colegio.edu.pe")
        print("   🔑 Contraseña: Alumno2026\n")

        # Crear Cursos de Prueba
        print("📕 Creando cursos...")
        cursos = [
            Curso(
                nombre="Matemáticas",
                codigo="MAT101",
                descripcion="Matemáticas básicas",
                docente_id=docente.id,
                grado_id=1,
                seccion_id=1
            ),
            Curso(
                nombre="Lenguaje",
                codigo="LEN101",
                descripcion="Lenguaje y comunicación",
                docente_id=docente.id,
                grado_id=1,
                seccion_id=1
            ),
        ]
        for curso in cursos:
            db.session.add(curso)
        db.session.commit()
        print("✅ Cursos creados\n")

        # Inscribir alumno en cursos
        print("📝 Inscribiendo alumno en cursos...")
        for curso in cursos:
            inscripcion = Inscripcion(alumno_id=alumno.id, curso_id=curso.id)
            db.session.add(inscripcion)
        db.session.commit()
        print("✅ Alumno inscrito en cursos\n")

        print("=" * 50)
        print("🎉 ¡Base de datos inicializada correctamente!")
        print("=" * 50)
        print("\n📝 USUARIOS DE PRUEBA:\n")
        print("1️⃣  DIRECTORA (Administrador)")
        print("   • Correo: admin@colegio.edu.pe")
        print("   • Contraseña: Admin2026")
        print("   • Rol: Directora\n")
        print("2️⃣  DOCENTE")
        print("   • Correo: docente@colegio.edu.pe")
        print("   • Contraseña: Docente2026")
        print("   • Rol: Docente\n")
        print("3️⃣  ALUMNO")
        print("   • Correo: alumno@colegio.edu.pe")
        print("   • Contraseña: Alumno2026")
        print("   • Rol: Alumno\n")
        print("=" * 50)

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
