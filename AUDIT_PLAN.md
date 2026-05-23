# PLAN DE AUDITORÍA - COLEGIO SYS

## FASE 1: CRÍTICO ✅ COMPLETADO
| # | Archivo | Línea | Problema | Estado |
|---|---------|-------|----------|--------|
| 1 | app.py | 709, 798, 815 | `estudiante_id` vs `alumno_id` (NameError 500) | ✅ |
| 2 | editar_alumno.html | 23 | `<form>` sin `action` | ✅ |
| 3 | editar_docente.html | 23 | `<form>` sin `action` | ✅ |
| 4 | perfil.html | 70 | `<` sin escapar en `#req-sym` | ✅ |
| 5 | editar_docente.html | 189 | `hidden` vs `style.display` | ✅ |
| 6 | editar_docente.html | 363 | `secci?n` encoding roto | ✅ |
| 7 | editar_alumno+docente | varios | Patrones regex con `?` literal | ✅ |
| 8 | docentes_form.html | 36, 40 | Asteriscos en teléfonos sin `required` | ✅ |

## FASE 2: SEGURIDAD/UX ✅ COMPLETADO
| # | Archivo | Línea | Problema | Estado |
|---|---------|-------|----------|--------|
| 1 | app.py | login | `session.clear()` movido después de auth exitosa | ✅ |
| 2 | app.py | login | Rate limiting (IntentoLogin/Baneo) implementado | ✅ |
| 3 | styles.css | - | Clases faltantes agregadas (grid-2, grid-3, summary-*, btn-info, btn-warning, badge-info, table, form-input, card-item, comentario-card, asist-radio, avatar-icon, main-nav, etc.) | ✅ |
| 4 | login.html | 102 | `disableSubmitButton` unificado con base.html | ✅ |
| 5 | registrar_alumno.html | 15, 42 | "Informacion" → "Información" | ✅ |
| 6 | login.html | 90 | Link "Olvidaste contraseña" apunta a ruta real | ✅ |
| 7 | app.py | 1224 | Validación archivos subidos (extensión + tamaño) | ✅ |

## FASE 3: LÓGICA/FUNCIONALIDAD (Parcial)
| # | Archivo | Línea | Problema | Estado |
|---|---------|-------|----------|--------|
| 1 | PagoRealizado | - | Usar `fecha_vencimiento` real del plan (bajo impacto) | ⏸️ |
| 2 | base.html | - | Navbar sin sidebar (por diseño) | ⏸️ |
| 3 | editar_alumno+docente | - | Campo sección SÍ existe | ⏸️ |
| 4 | app.py | 786, 619, 929 | DNI duplicado en editar_docente, editar_colaborador, editar_estudiante | ✅ |
| 5 | listar_alumnos/docentes | - | Agregado `{% else %}` para lista vacía | ✅ |
| 6 | dashboard_directora | - | Refresh automático (baja prioridad) | ⏸️ |
| 7 | Horario | - | No hay ruta docente-horario | ⏸️ |
| 8 | base.html | - | Navegación inline por diseño | ⏸️ |
| 9 | evaluaciones | - | Importar repetido (baja prioridad) | ⏸️ |
| 10 | varios selects | - | Cursos no duplicados en queries | ⏸️ |
| 11 | comentarios.html | 6 | Ruta coincide con form action | ⏸️ |
| 12 | app.py | eliminar_* | Cascade deletes implementados | ✅ |

## FASE 4: CALIDAD/RENDIMIENTO (Pendiente)
| # | Archivo | Problema | Prioridad |
|---|---------|----------|-----------|
| 1 | app.py | Duplicados `import os/re` | ✅ YA LIMPIO |
| 2 | app.py | `cargar_grados`/`cargar_secciones` fragmentar | Baja |
| 3 | templates | Consistencia Jinja2 espacios | Baja |
| 4 | app.py | logging.DEBUG → WARNING | ✅ |
| 5 | templates | Forms sin CSRF | Media |
| 6 | app.py | Refactor rutas duplicadas | Baja |
| 7 | app.py | N+1 queries (calcular_promedio, asistencia, import) | **Media** |
| 8 | styles.css | Variables CSS colores | Baja |
| 9 | base.html/home.html | Semántica HTML/aria | Baja |

## LEYENDA
- ✅ = Completado
- ⏸️ = Pausado (baja prioridad o no es bug real)
- Pendiente = Sin empezar
