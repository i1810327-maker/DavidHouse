## ADDED Requirements

### Requirement: Estudiante dashboard with four-tab navigation
The system SHALL provide an estudiante (padre/estudiante) dashboard with tabs: Notas, Asistencia, Comentarios, Pagos. The sidebar SHALL show the estudiante's name, "Estudiante" role badge, and avatar. The top bar SHALL show "Panel de Control - Estudiante" and the current date.

#### Scenario: Estudiante sees four tabs
- **WHEN** a student/parent user navigates to `/estudiante`
- **THEN** the system SHALL display tabs: Notas, Asistencia, Comentarios, Pagos in that order
- **AND** the first tab (Notas) SHALL be selected by default
- **AND** the sidebar SHALL show the student's name, "Estudiante" role badge, and avatar

### Requirement: Notas tab for student
The Notas tab SHALL display the student's grades in a card-per-subject layout. Each card SHALL show: subject name, examen grade, tarea grade, proyecto grade, promedio. The overall average SHALL be shown at the top.

#### Scenario: View grades
- **WHEN** the Notas tab is active
- **THEN** the system SHALL display grade cards for each subject
- **AND** the overall average SHALL be shown in a highlighted card at the top

### Requirement: Asistencia tab for student
The Asistencia tab SHALL display the student's attendance records in a table with columns: Fecha, Estado (Presente/Ausente/Tardanza). A summary SHALL show total classes, present, absent, tardy counts.

#### Scenario: View attendance
- **WHEN** the Asistencia tab is active
- **THEN** the system SHALL display the attendance table ordered by date (most recent first)
- **AND** a summary row SHALL show totals

### Requirement: Comentarios tab for student
The Comentarios tab SHALL display all comments written by docentes about this student, in reverse chronological order. Each comment SHALL show: date, docente name, comment text. The student SHALL be able to submit a justificación (título required, motivo required, archivo PDF mandatory).

#### Scenario: View teacher comments
- **WHEN** the Comentarios tab is active
- **THEN** the system SHALL display all comments from teachers, ordered newest first
- **AND** each comment SHALL show the date, teacher name, and text

#### Scenario: Submit justificación
- **WHEN** the student clicks "Justificarse" button
- **THEN** a form SHALL open with fields: título (text), motivo (textarea), archivo (file upload, PDF required)
- **AND** submitting without any of the three fields SHALL show validation errors
- **AND** after successful submission, the system SHALL display a success message

### Requirement: Pagos tab for student
The Pagos tab SHALL display the student's payment history in a table: Mes, Monto Base, Mora (S/5/day late fee), Total, Estado (Pagado/Pendiente/Vencido). The system SHALL calculate mora automatically based on days past due.

#### Scenario: View payment history
- **WHEN** the Pagos tab is active
- **THEN** the system SHALL display a payment table with columns: Mes, Monto Base, Mora, Total, Estado
- **AND** the mora column SHALL show S/5 for each day past the due date
- **AND** overdue payments SHALL be highlighted in red

#### Scenario: Pay pending amount
- **WHEN** the student clicks "Pagar" on a pending payment
- **THEN** the system SHALL mark the payment as "Pagado" and set the current date as payment date
