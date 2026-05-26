## ADDED Requirements

### Requirement: Docente dashboard with five-tab navigation
The system SHALL provide a docente dashboard with tabs: Asistencia, Notas, Comentarios, Subir Reportes, Horario. Each tab SHALL display a card-based content panel. The sidebar SHALL show the docente's name, role, and avatar. The top bar SHALL show "Panel de Control - Docente" and the current date.

#### Scenario: Docente sees all five tabs
- **WHEN** a docente user navigates to `/docente`
- **THEN** the system SHALL display tabs: Asistencia, Notas, Comentarios, Subir Reportes, Horario in that order
- **AND** the first tab (Asistencia) SHALL be selected by default
- **AND** the sidebar SHALL show the docente's name, "Docente" role badge, and avatar

### Requirement: Asistencia tab for docente
The Asistencia tab SHALL show a date picker and a student roster with present/ausente/tardanza toggle for each student. The docente SHALL filter by Nivel/Grado/Sección. Attendance SHALL be saved with a "Guardar Asistencia" button.

#### Scenario: Mark attendance
- **WHEN** the Asistencia tab is active
- **AND** the docente selects a date, Nivel, Grado, Sección
- **THEN** the system SHALL display the student roster for that section
- **AND** each student SHALL have radio buttons: Presente, Ausente, Tardanza
- **AND** clicking "Guardar Asistencia" SHALL persist the attendance records

#### Scenario: Attendance saved notification
- **WHEN** attendance is saved successfully
- **THEN** the system SHALL show a green toast: "Asistencia guardada correctamente"

### Requirement: Notas tab for docente
The Notas tab SHALL show the docente's assigned subjects with their sections. Selecting a subject/section SHALL display a grade grid. The docente SHALL enter notas (examen, tarea, proyecto) per student. A "Calcular Promedio" button SHALL compute the final grade.

#### Scenario: Enter grades
- **WHEN** the Notas tab is active
- **AND** the docente selects a subject and section
- **THEN** the system SHALL display a grid with students and columns for Examen, Tarea, Proyecto, Promedio
- **AND** the docente SHALL be able to type numeric grades in each cell
- **AND** clicking "Calcular Promedio" SHALL compute and display the average

### Requirement: Comentarios tab for docente
The Comentarios tab SHALL display a form to write comments about students. The docente SHALL select a student, write a comment, and submit. Previous comments for that student SHALL be displayed in a scrollable history.

#### Scenario: Write a comment
- **WHEN** the Comentarios tab is active
- **AND** the docente selects a student from the dropdown
- **THEN** the comment history for that student SHALL be displayed below
- **AND** the docente SHALL write text in a textarea and click "Enviar Comentario"
- **AND** the new comment SHALL appear in the history immediately

### Requirement: Subir Reportes tab
The Subir Reportes tab SHALL display a table of report requests from the director. Each row SHALL show: título, fecha_máxima (deadline), estado (pendiente/entregado). Past-deadline requests SHALL have the upload button disabled and show "Fecha límite pasada". The docente SHALL upload a PDF file for pending requests.

#### Scenario: Upload report before deadline
- **WHEN** the Subir Reportes tab is active
- **AND** the current date is before fecha_máxima
- **THEN** the "Subir Reporte" button SHALL be enabled
- **AND** clicking it SHALL prompt a file upload (PDF only)
- **AND** after upload, estado SHALL change to "entregado"

#### Scenario: Block upload after deadline
- **WHEN** the current date is after fecha_máxima
- **THEN** the "Subir Reporte" button SHALL be disabled
- **AND** the row SHALL show "Fecha límite pasada" in red text
- **AND** the server SHALL reject any upload attempt with a 400 error

### Requirement: Horario tab
The Horario tab SHALL display the docente's class schedule in a weekly grid format (Monday-Friday, time slots). Each slot SHALL show: subject name, section, room.

#### Scenario: Display schedule
- **WHEN** the Horario tab is active
- **THEN** the system SHALL display a 5-column (lunes-viernes) grid with time rows
- **AND** each assigned slot SHALL show the subject, section, and aula
