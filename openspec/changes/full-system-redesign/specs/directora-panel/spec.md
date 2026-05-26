## ADDED Requirements

### Requirement: Director dashboard layout
The director dashboard SHALL have a summary row (Total Docentes, Total Estudiantes, Ingresos Mensuales, Promedio Institucional) followed by 5 tabbed modules in order: Colaboradores, Alumnos, Pagos, Académico, Notas.

#### Scenario: Dashboard loads with summary
- **WHEN** directora logs in
- **THEN** the dashboard SHALL display 4 summary cards with real counts and a tab bar with 5 module tabs

### Requirement: Colaboradores module - Gestión
The Gestión sub-tab SHALL display a "Registrar nuevo docente" button, filters (Nivel, Grado, Sección) with default "Todos", and a column-style list of teacher cards with avatar, name, subject, student count, active/inactive badge, and "Ver Detalle" button.

#### Scenario: Teacher list displayed
- **WHEN** directora views the Gestión sub-tab
- **THEN** all teachers SHALL be displayed as cards with avatar initials, name, materia, course/student counts, status badge, and action buttons

#### Scenario: Filter teachers by level
- **WHEN** directora selects a Nivel filter
- **THEN** the teacher list SHALL filter to show only teachers assigned to that level

### Requirement: Colaboradores module - Reportes
The Reportes sub-tab SHALL have a "Solicitar Reportes" button, filters (Nivel, Grado, Sección), and a list of documents submitted by teachers (PDF/Word). Director can set a deadline when requesting reports. Past deadline blocks teacher uploads.

#### Scenario: Report list displays
- **WHEN** directora views the Reportes sub-tab
- **THEN** all submitted documents SHALL be listed with teacher name, title, folder, upload date, and status

#### Scenario: Director requests report
- **WHEN** directora clicks "Solicitar Reportes"
- **THEN** a form SHALL open to set title, description, target (nivel/grado/sección), and maximum delivery date

### Requirement: Alumnos module
The Alumnos tab SHALL display a student table with DNI, name, email, grade, section, active/inactive status, edit and toggle buttons.

#### Scenario: Student list displayed
- **WHEN** directora views the Alumnos tab
- **THEN** all students SHALL be listed in a table with search/filter and CRUD actions

### Requirement: Pagos module
The Pagos tab SHALL show payment plans, a "Nuevo Plan" button, and a "Registrar Pago" form. Filters by Nivel, Grado, Sección. Plans SHALL have states: Pendiente, Retrasado, Pagado.

#### Scenario: Payment plans displayed
- **WHEN** directora views the Pagos tab
- **THEN** all active payment plans SHALL be listed with name, amount, type, due date, status

### Requirement: Pagos - auto late fee
The system SHALL automatically calculate a late fee of S/5 per day for each day past the due date for unpaid/overdue payment plans.

#### Scenario: Late fee calculated
- **WHEN** a payment plan's due date has passed and the plan is unpaid
- **THEN** the system SHALL calculate mora = (days past due) * 5 and display the accumulated fee

### Requirement: Académico module - Estructura
The Estructura sub-tab SHALL display 3 cards for Niveles, Grados, and Secciones CRUD with Activo/Inactivo toggle buttons.

#### Scenario: Structure CRUD displayed
- **WHEN** directora views the Estructura sub-tab
- **THEN** 3 cards SHALL show Niveles, Grados, and Secciones tables with create forms and toggle buttons

#### Scenario: Toggle active state
- **WHEN** directora clicks a toggle button on any Nivel/Grado/Seccion
- **THEN** the item's active state SHALL flip and the badge SHALL update immediately

### Requirement: Académico module - Cursos
The Cursos sub-tab SHALL display a course table (name, code, grade, section, teacher, active status) and a "Nuevo Curso" button with creation form.

#### Scenario: Course CRUD displayed
- **WHEN** directora views the Cursos sub-tab
- **THEN** all courses SHALL be listed in a table with create/edit/toggle actions

### Requirement: Académico module - Horarios
The Horarios sub-tab SHALL display a schedule table (course, section, teacher, day, start time, end time) and "Nuevo Horario" button. Standard schedule Monday-Friday 8:00-13:30.

#### Scenario: Schedule displayed
- **WHEN** directora views the Horarios sub-tab
- **THEN** all schedules SHALL be listed with course, section, teacher, day, time

#### Scenario: New schedule created
- **WHEN** directora creates a new schedule entry
- **THEN** the schedule SHALL be saved with day (1-5 for Mon-Fri) and time within 8:00-13:30 range

### Requirement: Notas module (Excel-style)
The Notas tab SHALL display an Excel-like grid for entering grades. It SHALL show students as rows and evaluation types (Cuaderno, Libro, Prácticas, Exposición, Examen) as columns with inline editable cells. A "Generar Boleta" button SHALL produce the academic report card.

#### Scenario: Grade grid displayed
- **WHEN** directora selects a course and bimestre in the Notas tab
- **THEN** a grid SHALL display with students as rows and 5 evaluation type columns with editable input fields

#### Scenario: Grades saved
- **WHEN** directora enters grades in the grid and clicks "Guardar"
- **THEN** all grades SHALL be saved to the Evaluacion table
