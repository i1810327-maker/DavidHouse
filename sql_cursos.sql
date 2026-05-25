-- ============================================================
-- SCRIPT: CURSOS - colegio_sys
-- Tabla: cursos_nuevos
-- Base de datos: MySQL (Alwaysdata)
-- ============================================================

-- Ver estructura actual de la tabla
DESCRIBE cursos_nuevos;

-- Ver cursos existentes
SELECT cn.id, cn.nombre, cn.codigo, c.nombres AS docente, 
       g.nombre AS grado, s.nombre AS seccion,
       pa.nombre AS periodo, cn.activo
FROM cursos_nuevos cn
LEFT JOIN colaboradores c ON c.id = cn.docente_id
LEFT JOIN grados g ON g.id = cn.grado_id
LEFT JOIN secciones s ON s.id = cn.seccion_id
LEFT JOIN periodos_academicos pa ON pa.id = cn.periodo_academico_id
ORDER BY cn.id;

-- Ver cursos por docente
SELECT c.id, c.nombres, c.apellido_paterno, COUNT(cn.id) AS total_cursos
FROM colaboradores c
LEFT JOIN cursos_nuevos cn ON cn.docente_id = c.id
WHERE c.rol = 'docente'
GROUP BY c.id
ORDER BY c.nombres;

-- Insertar curso de ejemplo (ajustar IDs según base de datos real)
-- INSERT INTO cursos_nuevos (nombre, codigo, descripcion, docente_id, grado_id, seccion_id, periodo_academico_id, activo)
-- VALUES ('Matemática Básica', 'MAT-01', 'Curso de matemáticas para primaria', 1, 1, 1, 1, 1);

-- Asignar curso a docente (vía API)
-- POST /directora/api/docente/<docente_id>/asignar_curso
-- Body: {"curso_id": <id>}

-- Remover curso de docente (vía API)
-- POST /directora/api/docente/<docente_id>/remover_curso/<curso_id>
