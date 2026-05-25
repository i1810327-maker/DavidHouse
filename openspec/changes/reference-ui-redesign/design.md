## Context

The current system uses Flask + Jinja2 templates with vanilla CSS. There is no frontend framework. The reference design (student-care-hq.lovable.app) uses a modern card-based layout with colored sidebar navigation, avatar-based user headers, and consistent filter/search components. The CSS overhaul must work within the existing Flask/Jinja2 stack without introducing a JS framework.

The reference URL paths use role-based routing (e.g., `/director`, `/docente`, `/padre`).
Our system already uses similar routing but needs complete template and CSS replacement.

## Goals / Non-Goals

**Goals:**
- Match the reference design pixel-for-pixel for all three dashboards
- Implement all tabs and sub-modules as specified (Colaboradores, Alumnos, Pagos, Notas, Academico for director, etc.)
- Add client-side date blocking for report uploads (disabled after fecha_maxima)
- Add late-fee (mora) calculation (S/5/day) visible in payment tables
- Add justificación form with mandatory título, motivo, archivo
- Add filter dropdowns (Nivel/Grado/Sección) to every data table
- Add CSV import/export for student registration
- Add toggle (activo/inactivo) for students and collaborators
- Add comment history display in docente and estudiante panels

**Non-Goals:**
- No backend framework migration (stays Flask)
- No database schema changes (stays current SQLite/MySQL models)
- No user authentication rewrite
- No real-time WebSocket features
- No mobile-responsive design beyond what the reference provides

## Decisions

1. **CSS Approach**: Create a new `static/css/reference.css` file with `.ref-*` classes that mirror the Lovable reference design. Import it after existing styles to override without breaking current functionality during development. Use CSS custom properties for all colors to match the reference palette exactly.

2. **Template Structure**: Replace template content block-by-block rather than rewriting entire files. Use the existing `{% block %}` inheritance but replace the inner content for each dashboard. This minimizes risk and allows partial deployment.

3. **Tab Navigation**: Use a unified tab macro `_tab_nav.html` that renders tabs uniformly across all dashboards. Configure tabs via Jinja2 variables passed from each route.

4. **Filter Components**: Create a shared `_filters.html` partial that renders Nivel/Grado/Sección dropdowns. Populate from existing model queries.

5. **Date Handling**: Pass `now` as a Jinja2 global for date comparisons in templates (deadline checking). Use JavaScript Date.parse for client-side date blocking.

6. **Payment Late Fees**: Calculate mora server-side in the route and pass as template variable. Display in the payment table as a column.

7. **CSV Import/Export**: Add routes at `/director/alumnos/importar` and `/director/alumnos/exportar` using standard Python `csv` module.

8. **Comment System**: Reuse existing `Comentario` model. Justificación uses a separate `Justificacion` model with título, motivo, archivo fields.

## Risks / Trade-offs

- **CSS collision risk** → Use `.ref-*` prefixed classes exclusively for reference styles; never apply to global elements
- **Template size** → Dashboard templates may exceed 500 lines each; mitigate by extracting repeated patterns into Jinja2 macros/partials
- **File upload for justificación** → Must enforce file type/size limits in the route; add client-side validation for better UX
- **Date deadline enforcement** → Users could bypass client-side JS; always validate fecha_maxima server-side before accepting upload
