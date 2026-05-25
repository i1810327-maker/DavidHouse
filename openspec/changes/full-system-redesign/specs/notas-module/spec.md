## ADDED Requirements

### Requirement: Excel-style grade entry grid
The director's Notas module SHALL display a spreadsheet-like grid where rows are students and columns are evaluation types (Cuaderno, Libro, Prácticas, Exposición, Examen). Each cell SHALL be an editable input. A "Guardar Todo" button SHALL batch-save all changes.

#### Scenario: Grade grid renders
- **WHEN** director selects a course, bimestre, and clicks Notas
- **THEN** a grid SHALL render with students as rows and 5 evaluation type columns, each cell containing an editable number input (0-20)

#### Scenario: Bulk save grades
- **WHEN** director edits grades and clicks "Guardar Todo"
- **THEN** all changed grades SHALL be saved to the Evaluacion table in a single batch operation

### Requirement: Academic report card generation
The system SHALL generate an academic report card (boleta) per section and bimestre, showing each student's average per course, letter grade (AD/A/B/C), and attendance percentage.

#### Scenario: Report card generated
- **WHEN** director selects section, bimestre, and clicks "Generar Boleta"
- **THEN** a printable report card SHALL display with all students, their per-course averages, letter grades, and attendance
