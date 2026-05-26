## ADDED Requirements

### Requirement: Director creates report request
The director SHALL be able to create a report request specifying title, description, target (nivel/grado/sección), and maximum delivery date/time.

#### Scenario: Report request created
- **WHEN** director fills the report request form and submits
- **THEN** a solicitud_reporte record SHALL be created with the specified filters and deadline

### Requirement: Teacher views active requests
Teachers SHALL see only the report requests relevant to their assigned grades/sections. Each request SHALL show title, description, and remaining time until deadline.

#### Scenario: Teacher sees requests
- **WHEN** teacher opens Subir Reportes
- **THEN** only requests matching their assigned grades/sections SHALL be displayed

### Requirement: Teacher uploads report
For each active request (before deadline), the teacher SHALL be able to upload a PDF or Word file with title and description. The file SHALL be stored and linked to the request.

#### Scenario: Report uploaded
- **WHEN** teacher uploads a valid PDF/Word file before deadline
- **THEN** a DocumentoDocente record SHALL be created linked to the solicitud, with estado='pendiente'

### Requirement: Deadline enforcement
Once the maximum delivery date passes, the upload form SHALL be disabled and teachers SHALL NOT be able to submit files for that request.

#### Scenario: Upload blocked after deadline
- **WHEN** teacher views a request past its deadline
- **THEN** the upload controls SHALL be disabled and "Fecha límite pasada" SHALL display

### Requirement: Director reviews submissions
The director SHALL see all submitted documents in the Reportes sub-tab and SHALL be able to approve or reject them with comments.

#### Scenario: Document reviewed
- **WHEN** director approves or rejects a document with a comment
- **THEN** the DocumentoDocente status SHALL update and the teacher SHALL see the review result
