-- ============================================================
-- PASO 2: MIGRAR USUARIOS EXISTENTES A COLABORADORES/ESTUDIANTES
-- Antes de ejecutar, VERIFICA tus datos:
--   SELECT id, dni, nombres, correo, rol FROM usuarios;
-- Luego ejecuta todo este bloque
-- ============================================================

-- 2.1 Migrar directora y docentes a colaboradores
INSERT INTO colaboradores (id, dni, nombres, apellido_paterno, apellido_materno,
                           correo, clave, rol, telefono_principal, telefono_secundario,
                           profesion, tiene_especialidad, descripcion_especialidad,
                           seccion_id, activo, fecha_registro)
SELECT id, dni, nombres, apellido_paterno, apellido_materno,
       correo, clave, rol, telefono_principal, telefono_secundario,
       profesion, tiene_especialidad, descripcion_especialidad,
       seccion_id, activo, fecha_registro
FROM usuarios
WHERE rol IN ('directora', 'docente');

SELECT CONCAT('Migrados: ', ROW_COUNT(), ' colaboradores') AS resultado;

-- 2.2 Migrar alumnos a estudiantes
INSERT INTO estudiantes (id, dni, nombres, apellido_paterno, apellido_materno,
                         correo, clave, grado_id, seccion_id, activo, fecha_registro)
SELECT id, dni, nombres, apellido_paterno, apellido_materno,
       correo, clave, grado_id, seccion_id, activo, fecha_registro
FROM usuarios
WHERE rol = 'alumno';

SELECT CONCAT('Migrados: ', ROW_COUNT(), ' estudiantes') AS resultado;

-- 2.3 Verificar que la migración fue correcta
SELECT 'COLABORADORES:' AS tipo;
SELECT id, dni, nombres, apellido_paterno, rol FROM colaboradores;

SELECT 'ESTUDIANTES:' AS tipo;
SELECT id, dni, nombres, apellido_paterno FROM estudiantes;

SELECT 'USUARIOS ORIGINAL (deberían estar todos):' AS info;
SELECT id, dni, nombres, rol FROM usuarios;
