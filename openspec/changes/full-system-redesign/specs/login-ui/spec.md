## ADDED Requirements

### Requirement: Split-screen login layout
The login page SHALL use a split-screen layout: left side (60%) with gradient blue background, school branding, feature icons; right side (40%) with the login form on a white/light background.

#### Scenario: Login page renders
- **WHEN** any user visits `/login`
- **THEN** the split-screen layout SHALL render with branding on the left and form on the right

### Requirement: Login form fields
The login form SHALL have email and password fields with icons, a submit button "Ingresar", "¿Olvidaste tu contraseña?" link, and a help text line.

#### Scenario: Form fields present
- **WHEN** login page is loaded
- **THEN** email input with envelope icon, password input with lock icon and toggle visibility button, submit button, forgot password link, and help text SHALL be displayed

### Requirement: Password visibility toggle
The password field SHALL have a toggle button to show/hide the password text.

#### Scenario: Toggle shows password
- **WHEN** user clicks the eye icon on the password field
- **THEN** the password SHALL become visible and the icon SHALL change to eye-slash

#### Scenario: Toggle hides password
- **WHEN** user clicks the eye-slash icon
- **THEN** the password SHALL be masked and the icon SHALL change back to eye

### Requirement: Preserve existing auth logic
The login POST handler SHALL preserve all existing security: ban checks (`Baneo` table), IP tracking, `IntentoLogin` logging, 3-attempt lockout, 5-minute ban, user inactive check, and flash messages.

#### Scenario: Banned user blocked
- **WHEN** a banned user (usuario or IP) attempts to login
- **THEN** the system SHALL reject the login with flash message "Cuenta temporalmente bloqueada. Intente más tarde."

#### Scenario: Invalid credentials logged
- **WHEN** login fails with wrong email/password
- **THEN** the system SHALL record the attempt in `IntentoLogin` and increment the counter

#### Scenario: Lockout after 3 attempts
- **WHEN** 3 failed login attempts occur within 5 minutes
- **THEN** the system SHALL create a `Baneo` record and block further attempts for 5 minutes

### Requirement: Login loading state
The submit button SHALL show a loading spinner and become disabled when clicked to prevent double submission.

#### Scenario: Button loading state
- **WHEN** user clicks the submit button
- **THEN** the button SHALL display a spinner and become disabled until the response returns
