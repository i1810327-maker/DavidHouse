# Rediseño UI/UX Completo - Sistema de Gestión Escolar

## ¿Qué?

Rediseño completo de la interfaz de usuario del sistema de gestión escolar "David House - Camino de Vida", modernizando todos los paneles por rol (directora, docente, estudiante), landing page y login, manteniendo intacto el backend Flask existente.

## ¿Por qué?

- La interfaz actual es funcional pero visualmente anticuada (tablas densas, colores inconsistentes, falta de cards y componentes modernos).
- Los usuarios (directora, docentes, alumnos de inicial/primaria) necesitan una experiencia visual más amigable, colorida e intuitiva.
- Las referencias de diseño proporcionadas (student-care-hq.lovable.app) muestran un estándar moderno al que debemos aspirar.
- El sistema es usado por niños pequeños - necesita ser atractivo, con iconos grandes, colores vibrantes y tipografía clara.

## Alcance

### Incluye:
1. **Landing Page** - Rediseño completo con hero, niveles, eventos (carrusel automático), testimonios, contacto. Inspirada en david-house-webpage-azul.lovable.app
2. **Login** - Mejora visual manteniendo lógica de autenticación existente (bloqueo por IP/usuario, bcrypt). Inspirado en david-house-login-portal.lovable.app
3. **Dashboard Directora** - Cards de resumen, tabs modernos, teacher cards con avatares iniciales, sección de reportes con filtros. Inspirado en student-care-hq.lovable.app/director
4. **Dashboard Docente** - Cards de cursos, gestión de calificaciones/asistencia con diseño moderno. Inspirado en student-care-hq.lovable.app/docente
5. **Dashboard Estudiante/Padre** - Vista de calificaciones, horarios, tareas, eventos, mensajes. Inspirado en student-care-hq.lovable.app/padre
6. **Sistema de Eventos** - Nuevo módulo con carrusel automático en landing page y CRUD para administración
7. **Refactor CSS** - Migrar a variables CSS, componentes reutilizables, diseño responsive mobile-first

### No incluye:
- Cambios en la lógica de backend Flask (autenticación, rutas, modelos, base de datos)
- Migración a otro framework frontend (se mantiene Jinja2 + CSS vanilla)
- Cambios en la estructura de base de datos existente

## Referencias de Diseño

| Página | Referencia |
|--------|-----------|
| Landing Page | https://david-house-webpage-azul.lovable.app |
| Login | https://david-house-login-portal.lovable.app |
| Dashboard Directora | https://student-care-hq.lovable.app/director |
| Dashboard Docente | https://student-care-hq.lovable.app/docente |
| Dashboard Estudiante | https://student-care-hq.lovable.app/padre |

## Stack Tecnológico (Confirmado)

- **Backend**: Flask + SQLAlchemy + MySQL + Bcrypt (existente, no modificar)
- **Frontend**: Jinja2 templates + CSS3 vanilla
- **Base de datos**: MySQL con connector nativo
- **Autenticación**: Sesiones Flask + bloqueo por intentos/IP (no modificar)
