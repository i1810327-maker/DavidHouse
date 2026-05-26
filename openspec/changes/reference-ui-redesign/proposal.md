## Why

The current dashboards do not match the user's requirements for module structure, visual design, or functionality. The director dashboard is missing the Alumnos module, the docente dashboard lacks proper tabs (Asistencia, Notas, Comentarios, Subir Reportes, Horario), and the estudiante dashboard does not match the reference design. The UI must be rebuilt to exactly match the structure, colors, and functionality of the reference application at student-care-hq.lovable.app.

## What Changes

- **Director dashboard**: Restructure tabs to Colaboradores, Alumnos, Pagos, Notas, Académico (in that order). Each tab must have proper sub-modules, filters, and CRUD functionality matching the reference.
- **Docente dashboard**: Restructure to 5 tabs: Asistencia, Notas, Comentarios, Subir Reportes, Horario. Each tab must have full functionality (grade entry, attendance marking, comment writing, report upload with deadline check, schedule view).
- **Estudiante dashboard**: Restructure to 4 tabs: Notas, Asistencia, Comentarios, Pagos. Matching the parent/student reference design.
- **Alumnos module**: New tab in director dashboard with registration, filters, alphabetical listing, detail/edit/toggle for each student.
- **Filter components**: Add filter dropdowns (Nivel/Grado/Sección) to every module that requires them.
- **CSS overhaul**: Replace all dashboard CSS with reference design classes (`.ref-*`), matching colors, card styles, avatars, and layout from student-care-hq.lovable.app.
- **Late fee automation**: Ensure S/5/day mora is calculated and displayed in payment views.
- **Justification system**: Ensure estudiante justificación requires título, motivo, and archivo (mandatory).
- **Report deadline check**: Block teacher uploads after fecha_maxima passes.

## Capabilities

### New Capabilities
- `directora-panel`: Director dashboard with Colaboradores, Alumnos, Pagos, Notas, Académico tabs, each with full CRUD and filters
- `docente-panel`: Teacher dashboard with Asistencia, Notas, Comentarios, Subir Reportes, Horario tabs
- `estudiante-panel`: Student dashboard with Notas, Asistencia, Comentarios, Pagos tabs matching reference
- `alumnos-module`: Student management tab for director with filters, listing, detail/edit/toggle
- `reportes-docentes`: Report request/submission system with deadline enforcement
- `pagos-module`: Payment management with late fee (S/5/day) and status tracking
- `notas-module`: Excel-style grade grid for director and teacher grade entry
- `ui-reference-styles`: Complete CSS redesign matching student-care-hq.lovable.app look and feel

### Modified Capabilities
- *None* (this is a full rebuild, not a modification)

## Impact

- `templates/dashboard_directora.html`: Full rewrite with 5-tab structure
- `templates/dashboard_docente.html`: Full rewrite with 5-tab structure
- `templates/dashboard_estudiante.html`: Full rewrite with 4-tab structure
- `templates/base.html`: Header matching reference design
- `static/css/styles.css`: Add ~700+ lines of `.ref-*` classes
- `routes/routes_directora.py`: May need additional query params for new filters
- `routes/routes_docente.py`: Dashboard route must pass more template variables
- `routes/routes_estudiante.py`: Dashboard route must pass asistencia, pagos, comentarios
- `app.py`: May need additional Jinja2 globals (e.g., `now()` for deadline checks)
