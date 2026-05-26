## ADDED Requirements

### Requirement: Director dashboard with five-tab navigation
The system SHALL provide a director dashboard with tabs: Colaboradores, Alumnos, Pagos, Notas, Académico. Each tab SHALL display a card-based content panel matching the reference design. The sidebar SHALL show the director's name, role, and avatar. The top bar SHALL show "Panel de Control - Directora" and the current date.

#### Scenario: Director sees all five tabs
- **WHEN** a director user navigates to `/director`
- **THEN** the system SHALL display tabs: Colaboradores, Alumnos, Pagos, Notas, Académico in that order
- **AND** the first tab (Colaboradores) SHALL be selected by default
- **AND** the sidebar SHALL show the director's name, "Directora" role badge, and avatar circle

#### Scenario: Tab navigation preserves filter state
- **WHEN** a director selects filters (Nivel/Grado/Sección) on the Colaboradores tab
- **AND** switches to the Alumnos tab
- **THEN** the filters SHALL NOT persist across tabs (each tab has independent filter state)

### Requirement: Colaboradores tab CRUD
The Colaboradores tab SHALL list all collaborators (teachers, staff) with: nombre, apellido, correo, rol, nivel_asignado, grado_asignado, estado (activo/inactivo toggle). The director SHALL be able to add new collaborators via a modal form, edit existing ones, and toggle their active status.

#### Scenario: List collaborators
- **WHEN** the Colaboradores tab is active
- **THEN** the system SHALL display a table with columns: Nombre, Apellido, Correo, Rol, Nivel, Grado, Estado
- **AND** a search/input field SHALL filter by nombre/apellido

#### Scenario: Add new collaborator
- **WHEN** the director clicks "Agregar Colaborador"
- **THEN** a modal SHALL open with fields: nombre, apellido, correo, contraseña, rol, nivel_asignado, grado_asignado
- **AND** submitting the form SHALL create the collaborator and refresh the table

#### Scenario: Toggle collaborator status
- **WHEN** the director clicks the toggle switch for a collaborator
- **THEN** the system SHALL change the estado between activo/inactivo
- **AND** inactivo collaborators SHALL NOT appear in selection dropdowns elsewhere

### Requirement: Alumnos tab in director dashboard
The Alumnos tab SHALL display the student management module (see alumnos-module spec) embedded within the director dashboard.

#### Scenario: Alumnos tab shows students
- **WHEN** the Alumnos tab is active
- **THEN** the system SHALL display the student management interface with filters and table

### Requirement: Pagos tab in director dashboard
The Pagos tab SHALL display the payment management module (see pagos-module spec) embedded within the director dashboard.

#### Scenario: Pagos tab shows payments
- **WHEN** the Pagos tab is active
- **THEN** the system SHALL display the payment management interface

### Requirement: Notas tab in director dashboard
The Notas tab SHALL display an Excel-style grade grid (see notas-module spec) for viewing all students' grades across subjects, with filters for Nivel/Grado/Sección and subject selection.

#### Scenario: Notas tab shows grade grid
- **WHEN** the Notas tab is active
- **THEN** the system SHALL display a grid with students as rows and subjects as columns
- **AND** the director SHALL be able to edit any cell (grade) directly

### Requirement: Académico tab
The Académico tab SHALL display academic configuration: periodos, grados, secciones, subjects (cursos), and report request configuration.

#### Scenario: Academic configuration displayed
- **WHEN** the Académico tab is active
- **THEN** the system SHALL display sections for: Periodos, Grados, Secciones, Cursos, Report Requests
- **AND** the director SHALL be able to add/edit/delete each entity
