from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    # Configuración para Alwaysdata
    # Reemplaza estos valores con tus credenciales de Alwaysdata
    db_user = "colegiodh"  # Tu usuario de BD
    db_password = "Alex123456."       # Tu contraseña de BD
    db_host = "mysql-colegiodh.alwaysdata.net"  # Host de Alwaysdata
    db_name = "colegiodh_colegio_sys"            # Nombre de tu BD
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,      # Verifica conexión antes de usarla
        'pool_recycle': 1800,       # Recicla conexiones cada 30 min
        'pool_size': 5,             # Máximo conexiones en el pool
        'max_overflow': 5,          # Conexiones extra si el pool está lleno
    }
    db.init_app(app)