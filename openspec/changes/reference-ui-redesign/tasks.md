## 1. CSS Reference Styles

- [x] 1.1 Create `static/css/reference.css` with all `.ref-*` classes (layout, cards, tabs, tables, buttons, forms, modals, toasts, sidebar, filters)
- [x] 1.2 Include `reference.css` in all dashboard templates (`dashboard_directora.html`, `dashboard_docente.html`, `dashboard_estudiante.html`)
- [x] 1.3 Define CSS custom properties for reference color palette at `:root` level
- [x] 1.4 Implement sidebar dark theme styles (avatar circle, role badge, user info layout)
- [x] 1.5 Implement tab navigation horizontal bar with active indicator
- [x] 1.6 Implement table styles (striped rows, header, action icons, hover)
- [x] 1.7 Implement card component (white bg, radius, shadow, padding)
- [x] 1.8 Implement button variants (primary, success, danger, ghost)
- [x] 1.9 Implement modal overlay and centered modal card
- [x] 1.10 Implement toast notification with slide-in animation and auto-dismiss
- [x] 1.11 Implement filter dropdown row with labels
- [x] 1.12 Implement form input/select/textarea consistent styling

## 2. Director Dashboard Template

- [x] 2.1 Rewrite `templates/dashboard_directora.html` with reference layout (sidebar + main content + tab bar)
- [x] 2.2 Implement Colaboradores tab with table listing, add/edit modal, toggle activo/inactivo
- [x] 2.3 Implement Alumnos tab embedding student registration, table with filters, CSV import/export, detail/edit view
- [x] 2.4 Implement Pagos tab embedding payment management table with mora calculation
- [x] 2.5 Implement Notas tab with Excel-style grade grid (students x subjects), editable cells
- [x] 2.6 Implement Académico tab with periodos, grados, secciones, cursos, report request management
- [x] 2.7 Add filter dropdowns (Nivel/Grado/Sección) to every tab that needs them

## 3. Docente Dashboard Template

- [x] 3.1 Rewrite `templates/dashboard_docente.html` with reference layout (sidebar + main content + tab bar)
- [x] 3.2 Implement Asistencia tab with date picker, student roster, present/ausente/tardanza toggles, save button
- [x] 3.3 Implement Notas tab with subject/section selector and grade entry grid (examen, tarea, proyecto, promedio)
- [x] 3.4 Implement Comentarios tab with student selector, comment history display, comment form
- [x] 3.5 Implement Subir Reportes tab with report request table, deadline display, file upload with client-side date check
- [x] 3.6 Implement Horario tab with weekly schedule grid (lunes-viernes, time slots)
- [x] 3.7 Add filter dropdowns (Nivel/Grado/Sección) to Asistencia and Notas tabs

## 4. Estudiante Dashboard Template

- [x] 4.1 Rewrite `templates/dashboard_estudiante.html` with reference layout (sidebar + main content + tab bar)
- [x] 4.2 Implement Notas tab with per-subject grade cards and overall average display
- [x] 4.3 Implement Asistencia tab with attendance history table and summary counts
- [x] 4.4 Implement Comentarios tab with teacher comment history and justificación form (título, motivo, archivo)
- [x] 4.5 Implement Pagos tab with payment history table showing monto_base, mora, total, estado, and Pay button
- [x] 4.6 Add justificación mandatory validation (título, motivo, archivo required)

## 5. Backend Routes & Logic

- [x] 5.1 Update `routes/routes_directora.py` to pass all tab data and filter query params
- [x] 5.2 Add CSV import/export routes for student registration (`/director/alumnos/importar`, `/director/alumnos/exportar`)
- [x] 5.3 Update `routes/routes_docente.py` to pass attendance, grades, comments, reports, schedule data
- [x] 5.4 Add server-side deadline validation for report upload (reject if past fecha_maxima)
- [x] 5.5 Update `routes/routes_estudiante.py` to pass grades, attendance, comments, payments for the logged-in student
- [x] 5.6 Add justificación submission route with file upload handling
- [x] 5.7 Calculate mora (S/5/day) server-side in payment routes
- [x] 5.8 Register `now` as a Jinja2 global in `app.py` for template date comparisons

## 6. Models & Database

- [x] 6.1 Add `Justificacion` model (id, estudiante_id, titulo, motivo, archivo_path, created_at) if not exists
- [x] 6.2 Verify `Comentario` model has all necessary fields for docente comment history
- [x] 6.3 Verify `Asistencia` model supports present/ausente/tardanza status
- [x] 6.4 Verify `Pago` model has mora and estado fields for late fee tracking
- [x] 6.5 Verify `ReporteRequest` model has fecha_maxima, estado, archivo_path fields

## 7. Shared Components

- [x] 7.1 Create `templates/_tab_nav.html` macro for unified tab rendering across dashboards
- [x] 7.2 Create `templates/_filters.html` macro for Nivel/Grado/Sección dropdowns
- [x] 7.3 Create `templates/_modal.html` macro for reusable modal component
- [x] 7.4 Create `templates/_toast.html` macro for toast notification display
- [x] 7.5 Create `templates/_sidebar.html` macro for user sidebar component
