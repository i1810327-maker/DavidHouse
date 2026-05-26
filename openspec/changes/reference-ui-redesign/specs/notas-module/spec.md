## ADDED Requirements

### Requirement: Excel-style grade grid for director
The director SHALL view and edit all students' grades in a spreadsheet-style grid. Rows are students, columns are subjects. Each cell contains the student's promedio for that subject. The director SHALL be able to edit any grade cell.

#### Scenario: Director views grade grid
- **WHEN** the director is on the Notas tab
- **AND** selects a Nivel, Grado, Sección
- **THEN** the system SHALL display a grid with student names as rows and subjects as columns
- **AND** each cell SHALL show the numeric grade value
- **AND** the director SHALL double-click any cell to edit it

#### Scenario: Grade grid filters
- **WHEN** the director changes the Nivel/Grado/Sección filter
- **THEN** the grid SHALL reload with the matching students and subjects

### Requirement: Docente grade entry
The docente SHALL enter grades for their assigned subjects. For each student, the docente enters: examen (0-20), tarea (0-20), proyecto (0-20). The system SHALL calculate promedio = (examen + tarea + proyecto) / 3.

#### Scenario: Docente enters grades
- **WHEN** the docente is on the Notas tab
- **AND** selects an assigned subject and section
- **THEN** the system SHALL display a grid with columns: Estudiante, Examen, Tarea, Proyecto, Promedio
- **AND** the docente SHALL type grades in the Examen, Tarea, Proyecto cells
- **AND** clicking "Calcular Promedio" SHALL compute and populate the Promedio column

#### Scenario: Validate grade range
- **WHEN** the docente enters a grade outside 0-20
- **THEN** the system SHALL show a validation error
- **AND** SHALL NOT allow saving

### Requirement: Student grade view
The student SHALL view their grades in a read-only card-per-subject layout.

#### Scenario: Student views grades
- **WHEN** a student is on the Notas tab
- **THEN** the system SHALL display a card for each subject with: nombre_curso, examen, tarea, proyecto, promedio
- **AND** the overall average across all subjects SHALL be shown at the top
