from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    # Configuración para Alwaysdata
    # Reemplaza estos valores con tus credenciales de Alwaysdata
    db_user = "colegiodh_"  # Tu usuario de BD
    db_password = "DavidHouse1004"       # Tu contraseña de BD
    db_host = "mysql-colegiodh.alwaysdata.net"  # Host de Alwaysdata
    db_name = "colegiodh_colegio_sys"            # Nombre de tu BD
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)