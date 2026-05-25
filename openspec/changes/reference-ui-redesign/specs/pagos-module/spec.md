## ADDED Requirements

### Requirement: Payment record with late fee calculation
The system SHALL maintain monthly payment records for each student. Each record SHALL have: mes, año, monto_base, fecha_vencimiento, fecha_pago, estado (pendiente/pagado/vencido). The system SHALL automatically calculate mora as S/5 per calendar day past fecha_vencimiento.

#### Scenario: Calculate late fee
- **WHEN** viewing a payment where fecha_vencimiento is in the past and estado is "pendiente"
- **THEN** the system SHALL calculate mora = (current_date - fecha_vencimiento).days * 5
- **AND** display the mora amount in the payment row
- **AND** display the total = monto_base + mora

#### Scenario: Mark payment as pagado
- **WHEN** the director or student marks a payment as "Pagar"
- **THEN** the system SHALL set estado to "pagado"
- **AND** SHALL set fecha_pago to current date
- **AND** SHALL recalculate and freeze the mora at the time of payment

### Requirement: Payment listing with filters
Payments SHALL be filterable by Nivel/Grado/Sección/Mes/Año. The table SHALL show: Estudiante, Mes, Monto Base, Mora, Total, Estado, Acciones.

#### Scenario: Filter payments
- **WHEN** viewing the Pagos tab
- **AND** the director selects Nivel, Grado, Sección filters
- **THEN** the payment table SHALL update to show only matching records

### Requirement: Payment history for students
Students (in their dashboard) SHALL see only their own payment records with the same columns and mora calculation.

#### Scenario: Student views payments
- **WHEN** a student views the Pagos tab
- **THEN** the system SHALL display only that student's payment records
- **AND** SHALL calculate and display mora for each overdue record
