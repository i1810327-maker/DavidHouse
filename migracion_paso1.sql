-- ============================================================
-- PASO 1: CREAR TABLAS NUEVAS (SIN FK AÚN)
-- Ejecuta todo este bloque en phpMyAdmin
-- ============================================================

-- 1.1 NIVELES
CREATE TABLE niveles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO niveles (nombre) VALUES ('Inicial'), ('Primaria'), ('Secundaria');

-- 1.2 PERIODOS ACADEMICOS
CREATE TABLE periodos_academicos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO periodos_academicos (nombre, fecha_inicio, fecha_fin)
VALUES ('2026', '2026-01-01', '2026-12-31'),
       ('2025', '2025-01-01', '2025-12-31');

-- 1.3 BIMESTRES
CREATE TABLE bimestres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo_academico_id INT NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    numero TINYINT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO bimestres (periodo_academico_id, nombre, numero, fecha_inicio, fecha_fin) VALUES
(1, '1er Bimestre', 1, '2026-01-01', '2026-03-31'),
(1, '2do Bimestre', 2, '2026-04-01', '2026-06-30'),
(1, '3er Bimestre', 3, '2026-07-01', '2026-09-30'),
(1, '4to Bimestre', 4, '2026-10-01', '2026-12-31');

-- 1.4 COLABORADORES
CREATE TABLE colaboradores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(20) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(80) NOT NULL,
    apellido_materno VARCHAR(80) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    rol ENUM('directora','docente') NOT NULL,
    telefono_principal VARCHAR(20),
    telefono_secundario VARCHAR(20),
    profesion VARCHAR(100),
    tiene_especialidad BOOLEAN DEFAULT FALSE,
    descripcion_especialidad TEXT,
    seccion_id INT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.5 ESTUDIANTES
CREATE TABLE estudiantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dni VARCHAR(20) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(80) NOT NULL,
    apellido_materno VARCHAR(80) NOT NULL,
    correo VARCHAR(120) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    grado_id INT NULL,
    seccion_id INT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.6 CURSOS (nueva versión)
CREATE TABLE cursos_nuevos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    descripcion TEXT,
    docente_id INT NOT NULL,
    grado_id INT NOT NULL,
    seccion_id INT NOT NULL,
    periodo_academico_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.7 HORARIOS
CREATE TABLE horarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    curso_id INT NOT NULL,
    seccion_id INT NOT NULL,
    docente_id INT NOT NULL,
    dia_semana TINYINT NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    bimestre_id INT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.8 EVALUACIONES
CREATE TABLE evaluaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    curso_id INT NOT NULL,
    estudiante_id INT NOT NULL,
    bimestre_id INT NOT NULL,
    tipo ENUM('cuaderno','libro','practicas','exposiciones','examen') NOT NULL,
    calificacion DECIMAL(4,2) NOT NULL,
    fecha DATE NOT NULL,
    observaciones TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.9 ASISTENCIAS
CREATE TABLE asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    curso_id INT NOT NULL,
    estudiante_id INT NOT NULL,
    bimestre_id INT NOT NULL,
    fecha DATE NOT NULL,
    estado ENUM('presente','tarde','falta','justificado') NOT NULL DEFAULT 'presente',
    marcado_por INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.10 JUSTIFICACIONES
CREATE TABLE justificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asistencia_id INT NOT NULL,
    estudiante_id INT NOT NULL,
    motivo TEXT NOT NULL,
    archivo_ruta VARCHAR(500),
    estado ENUM('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
    revisado_por INT NULL,
    comentario_revision TEXT,
    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_revision DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.11 COMENTARIOS
CREATE TABLE comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    docente_id INT NOT NULL,
    estudiante_id INT NOT NULL,
    tipo ENUM('positivo','negativo','neutral','informativo') NOT NULL,
    contenido TEXT NOT NULL,
    bimestre_id INT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.12 PAGO PLANES
CREATE TABLE pago_planes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo_academico_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    monto DECIMAL(8,2) NOT NULL,
    nivel_id INT NULL,
    grado_id INT NULL,
    tipo ENUM('matricula','mensualidad','otro') NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.13 PAGO REALIZADOS
CREATE TABLE pago_realizados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    pago_plan_id INT NOT NULL,
    monto_pagado DECIMAL(8,2) NOT NULL,
    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pagado','pendiente','atrasado') DEFAULT 'pendiente',
    observaciones TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.14 CARPETAS DOCENTES
CREATE TABLE carpetas_docentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    bimestre_id INT NULL,
    fecha_inicio_entrega DATETIME NOT NULL,
    fecha_fin_entrega DATETIME NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_por INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.15 DOCUMENTOS DOCENTES
CREATE TABLE documentos_docentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    carpeta_id INT NOT NULL,
    docente_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    archivo_nombre VARCHAR(255) NOT NULL,
    archivo_ruta VARCHAR(500) NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
    comentario_revision TEXT,
    fecha_revision DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 1.16 APODERADO USUARIOS
CREATE TABLE apoderado_usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    apoderado_id INT NOT NULL UNIQUE,
    correo VARCHAR(120) UNIQUE NOT NULL,
    clave VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT 'PASO 1 COMPLETADO: todas las tablas nuevas creadas' AS resultado;
