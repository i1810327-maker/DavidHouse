## ADDED Requirements

### Requirement: Student registration with CSV import
The Alumnos module SHALL allow the director to register students individually via a form (nombre, apellido, correo, contraseña, nivel, grado, sección, fecha_nacimiento) or via CSV import. The CSV import SHALL support bulk upload with validation and error reporting.

#### Scenario: Register individual student
- **WHEN** the director fills the student registration form
- **AND** submits
- **THEN** the system SHALL create the student record
- **AND** SHALL show a success message
- **AND** SHALL refresh the student table

#### Scenario: CSV import students
- **WHEN** the director clicks "Importar CSV"
- **AND** selects a CSV file with columns: nombre, apellido, correo, nivel, grado, sección
- **THEN** the system SHALL validate each row
- **AND** SHALL create valid student records
- **AND** SHALL display a summary: N registros importados, X errores

### Requirement: Student listing with filters
The Alumnos module SHALL display students in a table with columns: Nombre, Apellido, Correo, Nivel, Grado, Sección, Estado. The table SHALL be filterable by Nivel, Grado, Sección dropdowns and searchable by nombre/apellido.

#### Scenario: List and filter students
- **WHEN** the Alumnos module is active
- **THEN** the system SHALL display all students in a paginated table
- **AND** SHALL show filter dropdowns for Nivel, Grado, Sección
- **AND** SHALL show a search input for nombre/apellido
- **AND** changing any filter SHALL update the table without page reload

### Requirement: Student detail and edit
Clicking a student row SHALL open a detail/edit view showing all student info. The director SHALL be able to edit fields and toggle the student between activo/inactivo.

#### Scenario: View and edit student
- **WHEN** the director clicks a student row
- **THEN** a detail panel SHALL open with all student fields editable
- **AND** a toggle switch SHALL allow changing estado between activo/inactivo
- **AND** saving SHALL persist changes

### Requirement: CSV export
The Alumnos module SHALL allow exporting the current filtered student list as a CSV file.

#### Scenario: Export students to CSV
- **WHEN** the director clicks "Exportar CSV"
- **THEN** the system SHALL download a CSV file with the filtered student data
