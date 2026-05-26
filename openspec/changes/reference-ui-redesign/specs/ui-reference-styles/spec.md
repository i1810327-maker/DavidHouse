## ADDED Requirements

### Requirement: Reference CSS class library
The system SHALL include a `static/css/reference.css` file defining all `.ref-*` CSS classes that replicate the student-care-hq.lovable.app visual design. This includes: layout grid, card components, tabs, tables, buttons, form inputs, avatars, badges, toasts, modals, filter dropdowns, and sidebar navigation.

#### Scenario: CSS is loaded on all dashboard pages
- **WHEN** any dashboard page is rendered
- **THEN** the `<head>` SHALL include `<link rel="stylesheet" href="/static/css/reference.css">`
- **AND** the reference classes SHALL NOT conflict with existing styles

### Requirement: Sidebar navigation style
The sidebar SHALL use a dark background (e.g., `#1e293b`), with the user's avatar circle (45px), name, and role badge. Navigation items SHALL use white text with a colored active indicator.

#### Scenario: Sidebar renders correctly
- **WHEN** a dashboard page loads
- **THEN** the sidebar SHALL show:
  - User avatar (circle, 45px, with first-letter fallback)
  - User full name
  - Role badge ("Directora"/"Docente"/"Estudiante")
  - No navigation links (tabs are in the main content area)

### Requirement: Card component style
Cards SHALL use white background, subtle border, border-radius 12px, padding 20px, light shadow. Cards SHALL be used to wrap each tab's content.

#### Scenario: Card renders in dashboard
- **WHEN** any tab content is displayed
- **THEN** the content SHALL be wrapped in a `.ref-card` div with proper styling

### Requirement: Tab navigation style
Tabs SHALL be displayed as horizontally aligned buttons with a bottom-border active indicator. Active tab SHALL have colored text and border (e.g., `#6366f1`). Inactive tabs SHALL have gray text. A subtle background hover effect SHALL be present.

#### Scenario: Tabs render correctly
- **WHEN** a dashboard loads
- **THEN** the tab bar SHALL show all tabs in a horizontal row
- **AND** the active tab SHALL have a bottom border and colored text

### Requirement: Table style
Tables SHALL use striped rows (alternating `#f8fafc`), header with `#f1f5f9` background, and border-radius 8px. Action buttons (edit/delete/toggle) SHALL be icon-only with hover tooltips.

#### Scenario: Table renders
- **WHEN** a data table is displayed
- **THEN** rows SHALL alternate background colors
- **AND** the header SHALL have a light gray background
- **AND** action icons SHALL show tooltips on hover

### Requirement: Button style variants
Buttons SHALL have three variants: `.ref-btn-primary` (indigo `#6366f1`), `.ref-btn-success` (green `#22c55e`), `.ref-btn-danger` (red `#ef4444`), and `.ref-btn-ghost` (transparent with text). All SHALL have border-radius 8px and proper hover/active states.

#### Scenario: Buttons render with correct colors
- **WHEN** a button with class `.ref-btn-primary` is displayed
- **THEN** it SHALL have indigo background, white text, and darken on hover

### Requirement: Filter dropdown style
Filter dropdowns SHALL use a consistent design: light border, border-radius 8px, padding 8px 12px, subtle shadow on focus. Multiple filters SHALL be displayed in a horizontal flex row.

#### Scenario: Filters render
- **WHEN** filter dropdowns are displayed
- **THEN** they SHALL be in a horizontal row with consistent sizing
- **AND** each dropdown SHALL have a label above it

### Requirement: Modal overlay style
Modals SHALL use a centered card with backdrop overlay (`rgba(0,0,0,0.5)`), border-radius 12px, max-width 500px, with a close (X) button.

#### Scenario: Modal opens
- **WHEN** a modal is triggered
- **THEN** a dark overlay SHALL appear
- **AND** the modal card SHALL be centered with the form content inside

### Requirement: Toast notification style
Toast notifications SHALL appear at the top-right, slide in with animation, and auto-dismiss after 3 seconds. Success toast: green background, white text. Error toast: red background, white text.

#### Scenario: Toast notification shows
- **WHEN** an action succeeds or fails
- **THEN** a toast SHALL slide in from the top-right
- **AND** SHALL auto-dismiss after 3 seconds
