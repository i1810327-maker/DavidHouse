## ADDED Requirements

### Requirement: Payment plan creation by section
The director SHALL be able to create payment plans filtered by Nivel, Grado, and Sección. Plans SHALL have: name, amount, type (matricula/mensualidad/otro), due date, and associated period.

#### Scenario: Payment plan created
- **WHEN** director fills the plan form and submits
- **THEN** a PagoPlan record SHALL be created with the specified filters and due date

### Requirement: Payment status tracking
Each student's payment SHALL have a status: Pendiente (pending), Pagado (paid), or Retrasado (overdue). The system SHALL auto-sync status on page load.

#### Scenario: Payment status synced
- **WHEN** any user views payments
- **THEN** the system SHALL check all unpaid plans against their due dates and update status to Retrasado if past due

### Requirement: Automatic late fee (mora)
The system SHALL calculate a late fee of S/5 per calendar day after the due date for unpaid plans. The accumulated mora SHALL be displayed alongside the base amount.

#### Scenario: Late fee calculated
- **WHEN** a plan is 3 days past due and unpaid
- **THEN** the system SHALL display mora_acumulada = S/15 (3 days * S/5)

### Requirement: Payment registration
The director SHALL be able to manually register a payment for a student against a specific plan, recording the amount paid.

#### Scenario: Payment registered
- **WHEN** director selects student, plan, enters amount, and submits
- **THEN** a PagoRealizado record SHALL be created with estado='pagado'
