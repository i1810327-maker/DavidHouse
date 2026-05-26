-- Fix FK constraints pointing to old `usuarios` table
-- These were executed programmatically via Python/mysql.connector

ALTER TABLE inscripciones DROP FOREIGN KEY inscripciones_ibfk_1;
ALTER TABLE inscripciones DROP FOREIGN KEY inscripciones_ibfk_2;
ALTER TABLE inscripciones ADD CONSTRAINT inscripciones_ibfk_1 FOREIGN KEY (alumno_id) REFERENCES estudiantes(id);
ALTER TABLE inscripciones ADD CONSTRAINT inscripciones_ibfk_2 FOREIGN KEY (curso_id) REFERENCES cursos_nuevos(id);

ALTER TABLE apoderados DROP FOREIGN KEY apoderados_ibfk_1;
ALTER TABLE apoderados ADD CONSTRAINT apoderados_ibfk_1 FOREIGN KEY (alumno_id) REFERENCES estudiantes(id);

ALTER TABLE secciones DROP FOREIGN KEY fk_secciones_docente;
ALTER TABLE secciones ADD CONSTRAINT fk_secciones_docente FOREIGN KEY (docente_id) REFERENCES colaboradores(id);

ALTER TABLE logs_acceso DROP FOREIGN KEY logs_acceso_ibfk_1;

ALTER TABLE cursos DROP FOREIGN KEY cursos_ibfk_1;
ALTER TABLE cursos DROP FOREIGN KEY cursos_ibfk_2;
