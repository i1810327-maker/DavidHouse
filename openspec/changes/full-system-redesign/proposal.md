## Why

The current Colegio David House system has a functional but outdated UI that doesn't reflect the institution's modern educational brand. Parents, teachers, and administrators need an intuitive, visually appealing platform that makes daily school management seamless. The landing page lacks engagement features (no event carousel), dashboards are crammed into single pages with poor UX, and key modules like payments (with late-fee automation), Excel-style grade entry, and teacher report submission are either missing or underdeveloped.

## What Changes

- **Landing Page**: Complete redesign with hero section, stats bar, values/mission/vision sections, and an auto-scrolling event carousel (left-to-right) showing event image, title, and description
- **Login Page**: Visual redesign matching the reference login portal (split-screen layout, modern form styling, animated elements) - EXISTING auth logic (banning, IP blocking, login attempts) preserved entirely
- **Director Panel**: Tabbed interface with 5 modules in exact order: Colaboradores (Gestión + Reportes submódulos), Alumnos, Pagos, Académico (Estructura + Cursos + Horarios), Notas (Excel-style entry)
- **Teacher Panel**: Modules for Asistencia, Notas (per-course grade forms with cuaderno/libro/prácticas/exposición/examen fields), Comentarios (filterable, with tipo: Comportamiento/Recomendación/Otro), Subir Reportes (view director's requests, upload PDF/Word), Horario (filtered by assigned grades)
- **Student/Parent Panel**: Modules for Notas (view per-course/bimestre with averages), Asistencia (view with "Justificar" button - title, description, required file), Comentarios (view all), Pagos (pending/paid/late with "Pagar" button placeholder)
- **Payments Module**: Schedule payments by section, auto late-fee of S/5 per day after due date, states: Pendiente/Retrasado/Pagado
- **Grades Module**: Excel-like grid for entering notes and generating academic report cards
- **Report System**: Director can request reports with deadlines; past deadline blocks teacher uploads
- Design inspired by provided reference links (blue/navy + orange accent scheme)

## Capabilities

### New Capabilities
- `landing-page`: Redesigned home page with hero, stats, values, mission/vision, gallery, footer, and auto-scrolling event carousel
- `login-ui`: Visual redesign of login page (split-screen, modern form) preserving existing auth security logic
- `directora-panel`: Director dashboard with 5 tabbed modules: Colaboradores, Alumnos, Pagos, Académico, Notas
- `docente-panel`: Teacher dashboard with Asistencia, Notas, Comentarios, Subir Reportes, Horario modules
- `estudiante-panel`: Student/parent dashboard with Notas, Asistencia (with justification), Comentarios, Pagos modules
- `pagos-module`: Payment plan scheduling by section, auto late-fee calculation (S/5/day), status tracking
- `notas-module`: Excel-style grade entry grid, academic report card generation
- `reportes-docentes`: Director report requests with deadlines, teacher file upload (PDF/Word), deadline enforcement

### Modified Capabilities
- *(none - existing capabilities are being replaced/redesigned, not modified)*

## Impact

- **Frontend**: Complete rewrite of all templates (home.html, login.html, dashboard_directora.html, dashboard_docente.html, dashboard_estudiante.html, and child templates). New CSS architecture. Event carousel JS.
- **Backend**: New routes for payment scheduling, late-fee cron, report requests, Excel-style grade bulk operations. Existing auth routes preserved.
- **Database**: May need new tables for eventos (events carousel) and solicitudes_reportes (report requests with deadlines). Existing tables preserved entirely.
- **Dependencies**: No new major dependencies (openpyxl already available for Excel import/export).
