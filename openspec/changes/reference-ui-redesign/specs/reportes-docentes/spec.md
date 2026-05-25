## ADDED Requirements

### Requirement: Director creates report requests
The director SHALL be able to create report requests for docentes. Each request SHALL have: título, descripción, fecha_máxima (deadline), and assigned docente. Docentes SHALL see pending report requests in their "Subir Reportes" tab.

#### Scenario: Create report request
- **WHEN** the director is on the Académico tab
- **AND** clicks "Nuevo Reporte"
- **THEN** a form SHALL open with fields: título, descripción, fecha_máxima, docente asignado
- **AND** submitting SHALL create the report request and assign it to the selected docente

### Requirement: Docente uploads report
The docente SHALL upload a PDF report for a pending request. The system SHALL block uploads if the current date exceeds fecha_máxima.

#### Scenario: Upload report successfully
- **WHEN** the docente is on the Subir Reportes tab
- **AND** clicks "Subir Reporte" for a pending request
- **AND** the current date is before or on fecha_máxima
- **AND** selects a valid PDF file
- **THEN** the system SHALL save the file
- **AND** SHALL change the request estado to "entregado"
- **AND** SHALL record the upload timestamp

#### Scenario: Upload rejected after deadline
- **WHEN** the current date is after fecha_máxima
- **AND** the docente attempts to upload
- **THEN** the client-side UI SHALL disable the upload button and show "Fecha límite pasada"
- **AND** the server SHALL reject any POST request with HTTP 400 and error message

### Requirement: Director views submitted reports
The director SHALL view submitted reports for each docente, including the upload date and a link to download the PDF.

#### Scenario: View submitted reports
- **WHEN** the director is on the Académico tab
- **AND** views report requests
- **THEN** the system SHALL show which requests are "entregado" vs "pendiente"
- **AND** SHALL provide a download link for completed reports
