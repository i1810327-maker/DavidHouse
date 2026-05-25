## ADDED Requirements

### Requirement: Teacher dashboard layout
The teacher dashboard SHALL show a welcome message, summary cards (Mis Cursos, Estudiantes Totales), a course card grid, and action cards for Comentarios and Subir Documentos.

#### Scenario: Teacher dashboard loads
- **WHEN** a docente logs in
- **THEN** the dashboard SHALL display their assigned courses as cards with "Notas" and "Asistencia" links, plus action cards for Comentarios and Documentos

### Requirement: Asistencia module
The Asistencia module SHALL show a list of students per course with radio buttons for Presente, Tarde, Falta and a "Marcar Todos" button to set all students to the same state. Date picker to select the attendance date.

#### Scenario: Attendance form displays
- **WHEN** teacher selects a course and date
- **THEN** all enrolled students SHALL be listed with Presente/Tarde/Falta radio buttons

#### Scenario: Mark all present
- **WHEN** teacher clicks "Marcar Todos"
- **THEN** all students SHALL be set to "Presente"

#### Scenario: Attendance saved
- **WHEN** teacher clicks "Guardar Asistencia"
- **THEN** attendance records SHALL be saved to the Asistencia table

### Requirement: Notas module
The Notas module SHALL show a per-course form with fields: Cuaderno, Libro, Prácticas, Exposición, Examen for each student. It SHALL also display the attendance percentage for each student.

#### Scenario: Grade form displays
- **WHEN** teacher selects a course and bimestre
- **THEN** all students SHALL be listed with 5 editable grade fields plus attendance %

#### Scenario: Grade saved
- **WHEN** teacher enters grades and saves
- **THEN** grades SHALL be stored in the Evaluacion table per student, course, bimestre, and type

### Requirement: Comentarios module
The Comentarios module SHALL have filters (Nivel, Grado, Sección, Estudiante), a comment type dropdown (Comportamiento, Recomendación, Otro), a large textarea for the comment, and an "Enviar" button.

#### Scenario: Comment form displayed
- **WHEN** teacher opens Comentarios
- **THEN** filters, tipo dropdown, textarea, and submit button SHALL be visible

#### Scenario: Comment sent
- **WHEN** teacher fills all fields and clicks "Enviar"
- **THEN** the comment SHALL be saved to the Comentario table and associated with the selected student

### Requirement: Subir Reportes module
The Subir Reportes module SHALL display a list of report requests from the director (title, description, deadline). For each active request (before deadline), a form SHALL allow the teacher to upload a file (PDF or Word) with title and description. Past deadlines SHALL disable the upload.

#### Scenario: Report requests displayed
- **WHEN** teacher opens Subir Reportes
- **THEN** all active report requests from the director SHALL be listed with title, description, and deadline

#### Scenario: File uploaded successfully
- **WHEN** teacher uploads a valid PDF or Word file before the deadline
- **THEN** the file SHALL be saved and a DocumentoDocente record created with estado='pendiente'

#### Scenario: Upload blocked after deadline
- **WHEN** teacher tries to upload after the deadline
- **THEN** the upload form SHALL be disabled and a message "Fecha límite pasada" SHALL display

### Requirement: Horario module
The Horario module SHALL display the teacher's schedule filtered by assigned grades, showing course, section, day, and time in a weekly grid format.

#### Scenario: Schedule displayed
- **WHEN** teacher opens Horario
- **THEN** a weekly schedule grid SHALL display their classes (Mon-Fri) with course, section, and time
