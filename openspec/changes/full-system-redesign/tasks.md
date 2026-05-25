## 1. Database Migrations & New Models

- [x] 1.1 Add `Evento` model (id, titulo, descripcion, imagen_url, activo, fecha_publicacion, orden) to `models.py`
- [x] 1.2 Add `SolicitudReporte` model (id, nivel_id, grado_id, seccion_id, titulo, descripcion, fecha_maxima, activa, creado_por, fecha_creacion) to `models.py`
- [x] 1.3 Add `mora_acumulada` column (Numeric(8,2), default=0) to `PagoRealizado` model
- [x] 1.4 Add `archivo_ruta` and `titulo` columns to `Justificacion` model if missing
- [x] 1.5 Alter `Comentario.tipo` ENUM to include 'comportamiento', 'recomendacion', 'otro'
- [x] 1.6 Add `solicitud_reporte_id` foreign key to `DocumentoDocente` model
- [x] 1.7 Run `db.create_all()` or generate SQL migration scripts

## 2. Project Structure Refactor

- [ ] 2.1 Create `routes/` package with `__init__.py`, `routes_directora.py`, `routes_docente.py`, `routes_estudiante.py`
- [ ] 2.2 Extract director routes from `app.py` into `routes_directora.py` as Flask Blueprint
- [ ] 2.3 Extract teacher routes from `app.py` into `routes_docente.py` as Flask Blueprint
- [ ] 2.4 Extract student routes from `app.py` into `routes_estudiante.py` as Flask Blueprint
- [ ] 2.5 Register blueprints in `app.py` and keep shared helpers (auth, decorators, helpers)
- [ ] 2.6 Create reusable Jinja2 macros file `templates/macros/` for grade rows, payment status badges, event cards

## 3. Landing Page Redesign

- [ ] 3.1 Rewrite `templates/home.html` with hero section, stats bar, nosotros, valores, misión/visión, niveles, galería, footer
- [ ] 3.2 Implement event carousel section with CSS auto-scroll animation (`@keyframes` translateX loop)
- [ ] 3.3 Add scroll reveal animation JS (`IntersectionObserver` or scroll listener)
- [ ] 3.4 Add responsive hamburger menu for mobile navigation
- [ ] 3.5 Add landing page CSS sections to `styles.css` (`.landing-hero`, `.landing-stats`, `.landing-section`, etc.)
- [ ] 3.6 Add `GET/POST` routes in `app.py` for event CRUD (director-only, accessible from a hidden section)

## 4. Login Page Redesign

- [ ] 4.1 Rewrite `templates/login.html` with split-screen layout (60/40), branding on left, form on right
- [ ] 4.2 Add password visibility toggle JS, loading spinner on submit, animated elements
- [ ] 4.3 Add login CSS sections to `styles.css` (`.login-wrapper`, `.login-left`, `.login-right`, `.login-form-container`, etc.)
- [ ] 4.4 Verify all existing auth flash messages, ban checks, IP tracking, and login attempt logic still work

## 5. Director Dashboard - Colaboradores Module

- [ ] 5.1 Rewrite `templates/dashboard_directora.html` with 5 tab structure (Colaboradores, Alumnos, Pagos, Académico, Notas)
- [ ] 5.2 Implement Gestión sub-tab: teacher card grid with avatar initials, filters (Nivel/Grado/Sección), "Registrar nuevo docente" button
- [ ] 5.3 Implement Reportes sub-tab: document review list with status badges, "Solicitar Reportes" button with deadline form
- [ ] 5.4 Add director-specific CSS (`.dir-tabs`, `.dir-tab-content`, `.teacher-card`, `.summary-card-dir`, etc.)

## 6. Director Dashboard - Alumnos Module

- [ ] 6.1 Implement Alumnos tab with student table, search/filter, CRUD modal forms
- [ ] 6.2 Add routes for student creation, editing, toggle active, and deletion (if not already present)
- [ ] 6.3 Add justificaciones pendientes review section

## 7. Director Dashboard - Pagos Module

- [ ] 7.1 Implement Pagos tab with payment plans table, "Nuevo Plan" form, "Registrar Pago" form
- [ ] 7.2 Implement `sincronizar_mora()` function calculating S/5/day late fee
- [ ] 7.3 Add filters by Nivel, Grado, Sección for payment views
- [ ] 7.4 Add boletas generation section (reuse existing `generar_boleta` route)

## 8. Director Dashboard - Académico Module

- [ ] 8.1 Implement Estructura sub-tab: Niveles, Grados, Secciones CRUD with toggle buttons
- [ ] 8.2 Implement Cursos sub-tab: course table with CRUD and dynamic dropdowns (Nivel→Grado→Sección)
- [ ] 8.3 Implement Horarios sub-tab: schedule table with CRUD, day/time selectors
- [ ] 8.4 Implement Periodos/Bimestres sub-tab: period and bimestre CRUD

## 9. Director Dashboard - Notas Module (Excel-style)

- [ ] 9.1 Implement Notas tab with course/bimestre selector and Excel-style editable grid
- [ ] 9.2 Create `POST` route for batch-saving all grades in one transaction (`bulk_save_objects`)
- [ ] 9.3 Add "Generar Boleta" button that renders academic report card
- [ ] 9.4 Add Notas CSS for the grid layout (`.grade-grid`, `.grade-cell`, etc.)

## 10. Teacher Dashboard Redesign

- [ ] 10.1 Rewrite `templates/dashboard_docente.html` with course cards and action links
- [ ] 10.2 Implement Asistencia module: student radio buttons (Presente/Tarde/Falta), "Marcar Todos", date picker
- [ ] 10.3 Implement Notas module: per-course grade form with 5 evaluation type fields per student, attendance % display
- [ ] 10.4 Implement Comentarios module: filters (Nivel/Grado/Sección/Estudiante), tipo dropdown (Comportamiento/Recomendación/Otro), textarea
- [ ] 10.5 Implement Subir Reportes module: list director requests with deadline, upload form (title, desc, file), disable past deadline
- [ ] 10.6 Implement Horario module: weekly schedule grid filtered by assigned grades
- [ ] 10.7 Add teacher-specific CSS (`.doc-`, `.teacher-grid`, `.dashboard-course-card`, etc.)

## 11. Student/Parent Dashboard Redesign

- [ ] 11.1 Rewrite `templates/dashboard_estudiante.html` with summary cards, course cards, action grid
- [ ] 11.2 Rewrite `templates/estudiante_notas.html`: per-course per-bimestre detail with all evaluations, average, letter grade, attendance %
- [ ] 11.3 Rewrite `templates/estudiante_asistencia.html`: attendance list with status badges, "Justificar" button with modal (title, desc, file required)
- [ ] 11.4 Rewrite `templates/estudiante_comentarios.html`: comment list with teacher name, type badge, date
- [ ] 11.5 Rewrite `templates/estudiante_pagos.html`: payment records with status, late fee, "Pagar" placeholder button
- [ ] 11.6 Rewrite `templates/estudiante_horario.html`: weekly schedule grid
- [ ] 11.7 Add student-specific CSS (`.est-`, `.asistencia-card-item`, `.comentario-card`, etc.)

## 12. Report System (Director Solicits, Teacher Submits)

- [ ] 12.1 Create `POST /directora/solicitar_reporte` route to create report requests with deadline
- [ ] 12.2 Create `GET /docente/solicitudes` API route returning active requests for the teacher's grades/sections
- [ ] 12.3 Create `POST /docente/subir_reporte/<solicitud_id>` route with deadline validation
- [ ] 12.4 Add deadline check: if current time > fecha_maxima, reject upload with flash message
- [ ] 12.5 Add document review workflow (approve/reject) in director's Reportes sub-tab

## 13. Payment Late Fee Automation

- [ ] 13.1 Implement `sincronizar_mora()`: iterate pending/overdue PagoRealizado, calculate days * 5, update mora_acumulada
- [ ] 13.2 Call `sincronizar_mora()` in payment-related route handlers (directora pagos, estudiante pagos)
- [ ] 13.3 Display mora_acumulada in payment views

## 14. CSS Architecture & Responsive Design

- [ ] 14.1 Organize `styles.css` with clear section comments for each role/page
- [ ] 14.2 Ensure all new UI is mobile-responsive (grid breakpoints, hamburger menus)
- [ ] 14.3 Add smooth transitions, hover effects, and animations
- [ ] 14.4 Ensure color scheme consistency (blue/navy primary, orange accent)

## 15. Final Verification

- [ ] 15.1 Verify all existing auth flows still work (login, logout, ban, IP block, password recovery)
- [ ] 15.2 Verify all existing CRUD operations still work (niveles, grados, secciones, cursos, horarios, periodos)
- [ ] 15.3 Verify attendance, grades, comments, payments, justifications read/write correctly
- [ ] 15.4 Test responsive layout on mobile viewport sizes
- [ ] 15.5 Run the application and verify no 404/500 errors on any route
