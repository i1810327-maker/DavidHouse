# Diseño Técnico - Rediseño UI/UX Completo

## 1. Arquitectura de Frontend

Se mantiene la arquitectura existente (Jinja2 + CSS vanilla). No se introducen nuevos frameworks ni build tools. El rediseño se logra mediante:

- **Templates HTML**: Refactor completos de `templates/` con nueva estructura semántica
- **CSS puro**: Stylesheet único `static/css/styles.css` con variables CSS y componentes reutilizables
- **JavaScript vanilla**: Funcionalidad mínima (tabs, modales, carrusel, fetch para APIs)

## 2. Paleta de Colores (CSS Variables)

```css
:root {
  --color-primary: #003D82;
  --color-secondary: #0066CC;
  --color-accent: #ff9800;
  --color-success: #28a745;
  --color-danger: #dc3545;
  --color-info: #17a2b8;
  --color-warning: #ffc107;
  --color-dark: #0B2B5E;
  --color-bg: #f8f9fa;
  --color-surface: #ffffff;
  --color-text: #333333;
  --color-text-muted: #888888;
  --color-border: #e0e0e0;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 40px rgba(0,0,0,0.08);
}
```

## 3. Estructura de Templates por Página

### 3.1 Landing Page (`templates/home.html`)
```
.home-header (logo + nav + hamburger)
.hero-section (slider/welcome)
.about-section (nosotros)
.levels-section (inicial / primaria cards)
.events-section (carrusel automático)
  ├── .events-carousel (auto-slide left-to-right)
  ├── .event-card (imagen + título + descripción + "Ver más")
  └── .carousel-controls (navegación manual)
.testimonials-section
.contact-section
.home-footer
```

### 3.2 Login (`templates/login.html`)
```
.login-container
  └── .login-card
        ├── .login-header (logo + título)
        ├── .login-body (formulario)
        │     ├── correo input
        │     ├── clave input + toggle visibility
        │     ├── submit button
        │     └── forgot password link
        └── .login-footer
```
- Mantener: toggle contraseña, flash messages, `disableSubmitButton`

### 3.3 Base Template (`templates/base.html`)
```
<header> (sistema) → .system-header
<main>
  .container
    ├── flash messages
    └── {% block content %}
</main>
<script> disableSubmitButton() </script>
```
- Agregar: `<nav>` con aria-label, `<main>` semántico, responsive header

### 3.4 Dashboard Directora (`templates/dashboard_directora.html`)
```
.dashboard-container
  ├── .summary-row (4 cards: docentes, estudiantes, ingresos, promedio)
  ├── .dir-tabs [Colaboradores | Pagos | Académico | Registro]
  ├── Tab: Colaboradores
  │     ├── .dir-subtabs [Gestión | Reportes]
  │     ├── Gestión: teacher cards con avatares iniciales
  │     └── Reportes: tabla filtrable por nivel/grado/sección
  ├── Tab: Pagos (planes + registro de pago)
  ├── Tab: Académico (estructura, periodos, cursos, horarios)
  └── Tab: Registro (estudiantes, boletas, justificaciones)
```

### 3.5 Dashboard Docente (`templates/dashboard_docente.html`)
```
.dashboard-container
  ├── summary cards
  ├── course cards grid (cada curso con acceso a notas/asistencia)
  └── quick actions (comentarios, documentos)
```

### 3.6 Dashboard Estudiante (`templates/dashboard_estudiante.html`)
```
.dashboard-container
  ├── summary cards + pagos atrasados
  ├── course cards con promedio y asistencia
  └── action buttons grid (horario, notas, asistencia, comentarios, pagos)
```

## 4. Sistema de Eventos (Nuevo Módulo)

### Modelo (`models.py`)
```python
class Evento(db.Model):
    __tablename__ = 'eventos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(500))  # ruta o URL
    fecha_evento = db.Column(db.Date)
    activo = db.Column(db.Boolean, default=True)
    orden = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Rutas (`app.py`)
- `GET /api/eventos` → JSON para carrusel (activos, ordenados)
- `POST /directora/eventos` → CRUD (crear, toggle, eliminar)

### Carrusel (Landing Page)
- Auto-slide izquierda→derecha cada 5 segundos
- Pausa en hover
- Botones de navegación manual (prev/next)
- Responsive: 1 card en mobile, 2 en tablet, 3 en desktop

## 5. Plan de Migración por Fases

| Fase | Componentes | Dependencias |
|------|-----------|-------------|
| 1 | CSS refactor (variables, reset, componentes base) | Ninguna |
| 2 | Dashboard Directora (completar rediseño actual) | Fase 1 |
| 3 | Dashboard Docente (cards, navegación) | Fase 1 |
| 4 | Dashboard Estudiante (resumen, acciones) | Fase 1 |
| 5 | Landing Page (hero, niveles, eventos) | Fase 1 |
| 6 | Login rediseño visual | Fase 1 |
| 7 | Módulo Eventos (modelo + CRUD + carrusel) | Fase 5 |
| 8 | Base template (nav semántica, responsive) | Fase 1 |
| 9 | Responsive testing + ajustes finales | Fases 2-8 |

## 6. Consideraciones Técnicas

- **Rendimiento**: El CSS único continuará creciendo. Considerar dividir en `styles.css` (general) + `dashboard.css` (paneles) si supera 4000 líneas.
- **Accesibilidad**: Agregar `aria-label` en navegación, roles semánticos (`<main>`, `<nav>`), contraste suficiente.
- **Responsive**: Mobile-first. Breakpoints: 480px, 768px, 1024px, 1280px.
- **Sin dependencias nuevas**: Todo el rediseño usa CSS vanilla + JS vanilla + Font Awesome (ya existente).
