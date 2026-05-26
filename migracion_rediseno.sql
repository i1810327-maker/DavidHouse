-- Migration for full-system-redesign
-- Run this after deploying the updated models.py

-- New tables
CREATE TABLE IF NOT EXISTS eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    imagen_url VARCHAR(500),
    activo BOOLEAN DEFAULT TRUE,
    fecha_publicacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    `orden` INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS solicitudes_reportes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nivel_id INT,
    grado_id INT,
    seccion_id INT,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    fecha_maxima DATETIME NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    creado_por INT NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nivel_id) REFERENCES niveles(id),
    FOREIGN KEY (grado_id) REFERENCES grados(id),
    FOREIGN KEY (seccion_id) REFERENCES secciones(id),
    FOREIGN KEY (creado_por) REFERENCES colaboradores(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- New columns on existing tables
ALTER TABLE pago_realizados ADD COLUMN IF NOT EXISTS mora_acumulada DECIMAL(8,2) DEFAULT 0;
ALTER TABLE justificaciones ADD COLUMN IF NOT EXISTS titulo VARCHAR(200) DEFAULT '';
ALTER TABLE justificaciones ADD COLUMN IF NOT EXISTS archivo_nombre VARCHAR(255);
ALTER TABLE documentos_docentes ADD COLUMN IF NOT EXISTS solicitud_reporte_id INT;
ALTER TABLE documentos_docentes ADD COLUMN IF NOT EXISTS carpeta_id INT;
ALTER TABLE documentos_docentes ADD FOREIGN KEY (solicitud_reporte_id) REFERENCES solicitudes_reportes(id);

-- Alter comentarios tipo ENUM
ALTER TABLE comentarios MODIFY COLUMN tipo ENUM('positivo','negativo','neutral','informativo','comportamiento','recomendacion','otro') NOT NULL;

-- Fix intentos_login table (model expects tipo_usuario column)
ALTER TABLE intentos_login ADD COLUMN IF NOT EXISTS tipo_usuario VARCHAR(11) DEFAULT 'colaborador';
