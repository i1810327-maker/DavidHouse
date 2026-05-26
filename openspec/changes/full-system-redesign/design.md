## Context

Colegio David House runs a Flask-based monolithic system with Jinja2 templates, SQLAlchemy ORM, and MySQL on Alwaysdata. The current UI is functional but lacks modern design, proper navigation structure, and several key features (event carousel, payment scheduling with late fees, Excel-style grade entry, report request workflow). All auth logic (banning, IP blocking, login attempt tracking) must be preserved.

The project uses a single `app.py` (~1564 lines) with all routes, 25 Jinja2 templates, one `styles.css` (~3200 lines), and 18 SQLAlchemy models. The redesign must work within this monolithic architecture without introducing a frontend framework.

## Goals / Non-Goals

**Goals:**
- Redesign all public-facing pages (landing, login) with modern UI inspired by reference links
- Restructure director, teacher, and student dashboards into clean tabbed module layouts
- Implement event carousel on landing page (auto-scroll left-to-right)
- Implement payment scheduling by section with auto late-fee (S/5/day)
- Implement Excel-style grade entry grid for director
- Implement teacher report submission workflow with director deadlines
- Implement student justification form with required file upload
- Preserve all existing auth security (baneos, intentos_login, logs_acceso, IP blocking)
- Preserve all existing database tables and relationships
- Keep monolithic Flask architecture (no frontend framework migration)

**Non-Goals:**
- No migration to React/Vue/SPA
- No REST API rewrite (keep server-rendered Jinja2)
- No user role changes or new authentication providers
- No mobile apps
- No real-time notifications (WebSocket)
- No payment gateway integration (QR is placeholder only)

## Decisions

1. **Template structure**: Each dashboard becomes a single self-contained template with JS tab switching rather than separate route per sub-module. This avoids route proliferation and keeps navigation fast (no page reload on tab switch). The director dashboard already uses this pattern - we extend it.

2. **CSS architecture**: Extend existing `styles.css` with new section-based classes rather than creating separate CSS files. Use CSS variables consistently. Component classes prefixed by page/role (`.landing-`, `.login-`, `.dir-`, `.doc-`, `.est-`) to avoid collisions.

3. **Event carousel**: Pure CSS animation with `@keyframes` for the auto-scroll (translateX loop). No JS carousel library needed. Events stored in a new `eventos` table (id, titulo, descripcion, imagen_url, activo, fecha_publicacion, orden). Director can CRUD events from a hidden section.

4. **Payment late fee**: A `sincronizar_mora()` function (similar to existing `sincronizar_estado_pagos`) runs on page load for the payments view. It calculates days past due_date * S/5 and updates a new `mora_acumulada` field on `PagoRealizado`. No cron job needed - synchronous on view.

5. **Report request workflow**: New `solicitudes_reportes` table (id, nivel_id, grado_id, seccion_id, titulo, descripcion, fecha_maxima, activa, creado_por, fecha_creacion). Director creates requests with deadline. Teachers see active requests and can upload files (PDF/Word) via existing `DocumentoDocente` table, associated to the solicitud. Frontend checks `fecha_maxima` and disables upload if past deadline.

6. **Excel-style grade entry**: Extend existing `evaluaciones_curso` route with a table grid where all students and all 5 evaluation types (cuaderno, libro, practicas, exposiciones, examen) are editable inline. Saving updates all rows at once. Reuse existing `openpyxl` import/export.

7. **Student "Justificar" flow**: Existing justification logic preserved. The form in `estudiante_asistencia.html` gets enhanced with required title field and required file upload. File saved to `static/uploads/` and path stored in `Justificacion.archivo_ruta`.

8. **Comentario types**: Extend the existing `Comentario.tipo` enum to include 'comportamiento', 'recomendacion', 'otro' (currently 'positivo', 'negativo', 'neutral', 'informativo'). Add migration: ALTER TABLE to modify ENUM.

## Risks / Trade-offs

- **Risk**: CSS file grows very large (~4000+ lines) → **Mitigation**: Use clear section comments and consider splitting into page-specific files if it exceeds 5000 lines
- **Risk**: `app.py` grows beyond manageable size → **Mitigation**: Extract dashboard routes into blueprint files (`routes_directora.py`, `routes_docente.py`, `routes_estudiante.py`) in a new `routes/` package
- **Risk**: Monolithic template files become too complex → **Mitigation**: Use Jinja2 `include` and `macro` for reusable components (event cards, grade rows, payment status badges)
- **Risk**: ENUM alteration for Comentario.tipo may fail depending on MySQL version → **Mitigation**: Use raw SQL ALTER with IF EXISTS check, or drop/recreate with new values
- **Risk**: Performance of grade entry grid with many students → **Mitigation**: Batch save with single SQLAlchemy `bulk_save_objects()` call per course
