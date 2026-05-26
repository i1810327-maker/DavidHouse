## ADDED Requirements

### Requirement: Student/parent dashboard layout
The dashboard SHALL show the student name, grade/section info, summary cards (Cursos, Promedio General, Pagos Pendientes, Atrasados), course cards with averages, and action links for each module.

#### Scenario: Student dashboard loads
- **WHEN** a student (alumno) logs in
- **THEN** the dashboard SHALL display their info, summary stats, course cards with averages and letter grades, and action links

### Requirement: Notas module (view only)
The Notas module SHALL display per-course and per-bimestre grades showing: Cuaderno, Libro, Prácticas, Exposición, Examen scores, the computed average, letter grade (AD/A/B/C), and attendance percentage.

#### Scenario: Grades displayed
- **WHEN** student selects a bimestre
- **THEN** all enrolled courses SHALL display with detailed scores per evaluation type, average, letter grade, and attendance %

### Requirement: Asistencia module with Justificación
The Asistencia module SHALL display all attendance records with date, course, status (Presente/Tarde/Falta/Justificado). Each "Falta" record SHALL have a "Justificar" button that opens a form with title, description, and required file upload.

#### Scenario: Attendance records displayed
- **WHEN** student opens Asistencia
- **THEN** all attendance records SHALL be displayed sorted by date desc with status badges

#### Scenario: Justification submitted
- **WHEN** student clicks "Justificar" on a Falta record, fills title, description, and uploads a file
- **THEN** a Justificacion record SHALL be created with estado='pendiente'

#### Scenario: Justification without file rejected
- **WHEN** student tries to submit a justification without a file
- **THEN** the form SHALL show an error "El archivo es obligatorio"

### Requirement: Comentarios module (view only)
The Comentarios module SHALL display all comments from teachers about the student, showing teacher name, comment type badge, content, and date.

#### Scenario: Comments displayed
- **WHEN** student opens Comentarios
- **THEN** all teacher comments SHALL be listed chronologically with teacher name, type, content, and date

### Requirement: Pagos module
The Pagos module SHALL display all payment records (plan name, amount, due date, status: Pendiente/Pagado/Retrasado, late fee). Each unpaid record SHALL have a "Pagar" button (placeholder, no QR yet).

#### Scenario: Payment records displayed
- **WHEN** student opens Pagos
- **THEN** all payment records SHALL be displayed with plan name, amount, due date, status badge, and late fee if applicable

#### Scenario: Pay button shown
- **WHEN** a payment record has status Pendiente or Retrasado
- **THEN** a "Pagar" button SHALL be displayed (placeholder - no payment gateway yet)
