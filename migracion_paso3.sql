-- ============================================================
-- PASO 3 (VERSIÓN SIMPLIFICADA - sin DROP de FK)
-- Saltamos el DROP de FK viejas. Las tablas existentes
-- conservan sus FK a usuarios (siguen funcionando).
-- Solo agregamos lo nuevo.
-- ============================================================

-- 3.1 AGREGAR nivel_id A grados
ALTER TABLE grados ADD COLUMN nivel_id INT NULL;
UPDATE grados SET nivel_id = CASE nivel
    WHEN 'inicial' THEN 1
    WHEN 'primaria' THEN 2
    ELSE NULL
END;
ALTER TABLE grados MODIFY COLUMN nivel_id INT NOT NULL;
ALTER TABLE grados ADD FOREIGN KEY (nivel_id) REFERENCES niveles(id);

-- 3.2 FK DE COLABORADORES Y ESTUDIANTES
ALTER TABLE colaboradores ADD FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE SET NULL;
ALTER TABLE estudiantes ADD FOREIGN KEY (grado_id) REFERENCES grados(id) ON DELETE SET NULL;
ALTER TABLE estudiantes ADD FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE SET NULL;

-- 3.3 FK TABLAS NUEVAS
ALTER TABLE bimestres ADD FOREIGN KEY (periodo_academico_id) REFERENCES periodos_academicos(id);

ALTER TABLE cursos_nuevos ADD FOREIGN KEY (docente_id) REFERENCES colaboradores(id);
ALTER TABLE cursos_nuevos ADD FOREIGN KEY (grado_id) REFERENCES grados(id);
ALTER TABLE cursos_nuevos ADD FOREIGN KEY (seccion_id) REFERENCES secciones(id);
ALTER TABLE cursos_nuevos ADD FOREIGN KEY (periodo_academico_id) REFERENCES periodos_academicos(id);

ALTER TABLE horarios ADD FOREIGN KEY (curso_id) REFERENCES cursos_nuevos(id);
ALTER TABLE horarios ADD FOREIGN KEY (seccion_id) REFERENCES secciones(id);
ALTER TABLE horarios ADD FOREIGN KEY (docente_id) REFERENCES colaboradores(id);
ALTER TABLE horarios ADD FOREIGN KEY (bimestre_id) REFERENCES bimestres(id);

ALTER TABLE evaluaciones ADD FOREIGN KEY (curso_id) REFERENCES cursos_nuevos(id);
ALTER TABLE evaluaciones ADD FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE evaluaciones ADD FOREIGN KEY (bimestre_id) REFERENCES bimestres(id);

ALTER TABLE asistencias ADD FOREIGN KEY (curso_id) REFERENCES cursos_nuevos(id);
ALTER TABLE asistencias ADD FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE asistencias ADD FOREIGN KEY (bimestre_id) REFERENCES bimestres(id);
ALTER TABLE asistencias ADD FOREIGN KEY (marcado_por) REFERENCES colaboradores(id);

ALTER TABLE justificaciones ADD FOREIGN KEY (asistencia_id) REFERENCES asistencias(id);
ALTER TABLE justificaciones ADD FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE justificaciones ADD FOREIGN KEY (revisado_por) REFERENCES colaboradores(id);

ALTER TABLE comentarios ADD FOREIGN KEY (docente_id) REFERENCES colaboradores(id);
ALTER TABLE comentarios ADD FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE comentarios ADD FOREIGN KEY (bimestre_id) REFERENCES bimestres(id);

ALTER TABLE pago_planes ADD FOREIGN KEY (periodo_academico_id) REFERENCES periodos_academicos(id);
ALTER TABLE pago_planes ADD FOREIGN KEY (nivel_id) REFERENCES niveles(id);
ALTER TABLE pago_planes ADD FOREIGN KEY (grado_id) REFERENCES grados(id);

ALTER TABLE pago_realizados ADD FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id);
ALTER TABLE pago_realizados ADD FOREIGN KEY (pago_plan_id) REFERENCES pago_planes(id);

ALTER TABLE carpetas_docentes ADD FOREIGN KEY (bimestre_id) REFERENCES bimestres(id);
ALTER TABLE carpetas_docentes ADD FOREIGN KEY (creado_por) REFERENCES colaboradores(id);

ALTER TABLE documentos_docentes ADD FOREIGN KEY (carpeta_id) REFERENCES carpetas_docentes(id);
ALTER TABLE documentos_docentes ADD FOREIGN KEY (docente_id) REFERENCES colaboradores(id);

ALTER TABLE apoderado_usuarios ADD FOREIGN KEY (apoderado_id) REFERENCES apoderados(id);

SELECT '✅ PASO 3 COMPLETADO' AS resultado;
