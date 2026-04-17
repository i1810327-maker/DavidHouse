# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
# Este archivo configura la conexión a MySQL usando SQLAlchemy

from flask_sqlalchemy import SQLAlchemy

# Instancia global de SQLAlchemy - se usará en todos los modelos
db = SQLAlchemy()

def init_db(app):
    """
    Inicializa la conexión a la base de datos MySQL
    - URI: mysql+mysqlconnector://root@localhost/colegio_sys
    - Desactiva track_modifications para mejorar rendimiento
    """
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost/colegio_sys'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)