# Log de Errores Correlacionados

**Propósito**: Registrar tareas que fallan validación repetidamente para identificar patrones y aplicar estrategias de decorrelación (MAKER paper).

**Criterio**: Una tarea que falla validación >2 veces = error correlacionado (sistemático, no aleatorio)

---

## Cómo Usar Este Log

### Cuándo Documentar
- Después del 2do fallo de validación de una tarea
- Antes de aplicar estrategia de decorrelación

### Qué Documentar
- Tarea que falló
- Número de intentos
- Tipo de error (format, logic, test failure, red flag)
- Estrategia de decorrelación aplicada
- Resultado

### Beneficios
- Identificar tareas que NO son atómicas
- Mejorar descomposición en futuros planes
- Evitar repetir mismo error
- Aprender patrones de error del proyecto

---

## Formato de Entrada

```markdown
## [YYYY-MM-DD HH:MM] - [Tarea: Nombre]

### Contexto
- **Tarea del plan**:
  - Plan único: [Sección X.Y del plan]
  - Plan dividido: [Sub-plan 1.X, Tarea 1.X.Y]
- **Intento**: #[N]
- **Tipo de fallo**: [Format / Logic / Test failure / Red flag / Validation]
- **Agente que detectó**: [red-flag-detector / validador / tests unitarios]

### Error Detallado
```
[Copiar output del error o descripción del validador]
```

### Análisis
**¿Por qué falló?**
- [Descripción de la causa raíz]

**¿Es la tarea realmente atómica?**
- [ ] Sí, tarea es atómica (30min-2h, responsabilidad única)
- [ ] No, tarea NO es atómica (requiere descomposición)

### Estrategia de Decorrelación Aplicada
- [ ] **Opción 1**: Re-prompting con paráfrasis
  - Prompt original: [texto]
  - Prompt parafraseado: [texto]

- [ ] **Opción 2**: Descomposición adicional (task-decomposer)
  - Sub-tareas resultantes: [lista]

- [ ] **Opción 3**: Cambio de enfoque técnico
  - Enfoque anterior: [descripción]
  - Nuevo enfoque: [descripción]

- [ ] **Opción 4**: Escalado a usuario
  - Pregunta al usuario: [pregunta específica]

### Resultado
- **Status**: [Éxito / Falló nuevamente / Pendiente]
- **Solución final**: [Descripción de lo que funcionó]

### Lecciones Aprendidas
- [Qué se aprendió de este error correlacionado]
- [Cómo mejorar la descomposición en el futuro]

---
```

---

## Ejemplos

### Ejemplo 1: Tarea NO era atómica

```markdown
## 2025-11-21 14:30 - Tarea: Implementar autenticación de usuarios

### Contexto
- **Tarea del plan**: Sección 5.3.2
- **Intento**: #3
- **Tipo de fallo**: Red flag (excessive length)
- **Agente que detectó**: red-flag-detector

### Error Detallado
```
❌ CRITICAL Red Flag: Excessive length
- File: auth/authentication.py
- LOC: 450 (threshold: 300 for atomic task)
- Functions: 8 (expected: 1-2 for single responsibility)

Indicates: Task NOT atomic OR over-engineered
```

### Análisis
**¿Por qué falló?**
- Tarea incluía: hash password, validar password, crear usuario, login, logout, gestión sesiones
- Múltiples responsabilidades en una sola tarea

**¿Es la tarea realmente atómica?**
- [X] No, tarea NO es atómica

### Estrategia de Decorrelación Aplicada
- [X] **Opción 2**: Descomposición adicional (task-decomposer)
  - Sub-tareas resultantes:
    1. Crear modelo User con hash de password
    2. Implementar endpoint POST /register
    3. Implementar endpoint POST /login
    4. Implementar middleware de autenticación
    5. Implementar endpoint POST /logout

### Resultado
- **Status**: Éxito
- **Solución final**: Implementar cada sub-tarea independientemente. Todas pasaron validación en 1er intento.

### Lecciones Aprendidas
- "Autenticación" es demasiado amplio para ser atómico
- Siempre descomponer features grandes en operaciones específicas
- Palabras clave que indican NO atómico: "gestión", "sistema", "completo"
```

---

### Ejemplo 2: Prompt ambiguo

```markdown
## 2025-11-21 16:45 - Tarea: Validar email de usuario

### Contexto
- **Tarea del plan**: Sección 5.3.5
- **Intento**: #3
- **Tipo de fallo**: Test failure
- **Agente que detectó**: tests unitarios

### Error Detallado
```
FAILED test_validate_email_rejects_invalid
Expected: Raise ValueError for invalid email
Actual: Returns False (no exception)
```

### Análisis
**¿Por qué falló?**
- Plan decía "validar email" pero no especificó SI debe:
  - Retornar bool (True/False)
  - Lanzar excepción
  - Retornar objeto Result con error
- Cada intento usó enfoque diferente, tests diseñados para uno específico

**¿Es la tarea realmente atómica?**
- [X] Sí, tarea es atómica (validación = responsabilidad única)
- Problema: Especificación ambigua

### Estrategia de Decorrelación Aplicada
- [X] **Opción 4**: Escalado a usuario
  - Pregunta: "¿La función validate_email debe retornar bool o lanzar excepción para emails inválidos?"
  - Respuesta usuario: "Lanzar ValueError con mensaje descriptivo"

### Resultado
- **Status**: Éxito
- **Solución final**: Implementar con excepción explícita, actualizar tests. Pasó validación.

### Lecciones Aprendidas
- Siempre especificar comportamiento de error en el plan
- Para funciones de validación: explicitar qué retornan y qué excepciones lanzan
- Incluir en plan: "Lanza ValueError si email inválido" en lugar de solo "valida email"
```

---

## Estadísticas de Errores (Actualizar periódicamente)

### Total de Errores Correlacionados: [N]

### Por Tipo de Error:
- Red flags (excessive length): [N]
- Red flags (format violation): [N]
- Test failures: [N]
- Validation failures: [N]

### Estrategias Más Efectivas:
1. [Estrategia]: [X] éxitos de [Y] intentos
2. [Estrategia]: [X] éxitos de [Y] intentos

### Tareas Más Problemáticas:
- [Tipo de tarea]: [N] errores correlacionados
- [Tipo de tarea]: [N] errores correlacionados

### Mejoras para Próximos Planes:
- [Lección aprendida aplicable]
- [Lección aprendida aplicable]
