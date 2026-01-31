# Guía para Ejecutar Planes de Implementación

## Propósito
Ejecutar e implementar un plan creado con `create-plan.md`. Seguir principios de minimalismo, modularidad y documentación primero.

---

## Principios Fundamentales

1. **Minimalismo (KISS & YAGNI)**: Solución más simple, no agregar funcionalidades no especificadas
2. **Modularidad**: Un componente a la vez, validar antes de continuar
3. **Documentación Primero**: Consultar docs oficiales (MCP Context7, web). Si no hay docs: **NO INVENTAR**, preguntar al usuario

---

## Proceso de Ejecución

### Paso 0: Preparación

**ANTES de implementar**:

#### 0.1. Identificar Tipo de Plan

**Plan Único** vs **Plan Dividido**:

Buscar en `workflow/request/`:
- Si existe `plan-[nombre].md` (1 solo archivo) → **Plan único**
- Si existe `plan-master-[nombre].md` + `plan-1.X-*.md` (múltiples archivos) → **Plan dividido**

**Si el plan está DIVIDIDO**:
1. **Leer primero** `plan-master-[proyecto].md`:
   - Resumen ejecutivo del proyecto completo
   - Arquitectura general
   - Índice de sub-planes (sección "Índice de Sub-Planes")
   - Orden de ejecución recomendado (sección "Orden de Ejecución Recomendado")
   - Dependencias globales (centralizadas aquí)

2. **LUEGO leer cada sub-plan** según orden de ejecución:
   - Archivo: `plan-1.X-[componente].md`
   - Contiene: Tareas atómicas del componente, validaciones, estructura de archivos
   - Usar navegación interna (📍 Navegación) para moverse entre sub-planes

3. **Referencias al plan**:
   - Plan maestro: Usar "Índice de Sub-Planes", "Orden de Ejecución", "Dependencias Globales"
   - Sub-planes: Usar "Tareas Detalladas", "Validaciones de Este Componente"

**Si el plan es ÚNICO**:
- Leer todo el archivo `plan-[nombre].md` normalmente
- Usar secciones estándar: 5.3 (Componentes), 5.5 (Orden), 5.7 (Estructura)

#### 0.2. Leer y Entender el Plan

**Para plan único**: Leer resumen ejecutivo, arquitectura, orden de implementación (sección 5.5)

**Para plan dividido**:
- Leer plan maestro completo
- Identificar qué sub-plan ejecutar primero según "Orden de Ejecución Recomendado"
- Leer sub-plan correspondiente ANTES de implementar ese componente

#### 0.3. Analizar Código Base (AGENTE code-analist)
```
Use the code-analist agent to analyze the existing codebase structure and conventions
```
Aplicar hallazgos: Respetar convenciones identificadas

#### 0.4. Verificar Dependencias
- **Plan único**: Librerías en sección 5.4
- **Plan dividido**: Librerías en "Dependencias Globales" del plan maestro
- Variables de entorno, archivos de configuración

#### 0.5. Revisar Ejemplos con Precaución
`workflow/examples/` son referencia de patrones, **NO copiar librerías** si difieren del plan

#### 0.6. Clarificar Dudas
Preguntar al usuario, no asumir

---

### Paso 1: Implementación por Componentes

**Seguir orden del plan**:
- **Plan único**: Orden en sección 5.5
- **Plan dividido**: "Orden de Ejecución Recomendado" del plan maestro

Para cada componente:

#### 1.1. Preparación

**Plan único**:
- Leer sección detallada (5.3): Nombre, responsabilidades, dependencias, interfaz/API, manejo errores, logging

**Plan dividido**:
- Abrir sub-plan correspondiente: `plan-1.X-[componente].md`
- Leer "Tareas Detalladas": Para cada tarea atómica del componente
- Referencia: Nombre, responsabilidad, dependencias, criterios de aceptación, tests, red flags

#### 1.2. Consultar Documentación
Buscar docs oficiales (MCP Context7, web). Si no hay: **detener y solicitar al usuario**

#### 1.3. Implementación
- **Ubicación de archivos**:
  - Plan único: Sección 5.7
  - Plan dividido: "Estructura de Archivos de Este Componente" en el sub-plan
- Implementar según pasos clave del plan
- Código simple (KISS), comentarios útiles (docstrings, decisiones clave)
- Respetar interfaz/API del plan
- Implementar manejo de errores y logging según plan
- Seguir convenciones de nomenclatura

#### 1.4. Red Flag Detection (MAKER-inspired)

**INMEDIATAMENTE después de implementar, ANTES de tests**:

```
Use the red-flag-detector agent to analyze [component name]:
- Plan specification: [From plan section 5.3]
- Expected complexity: [Simple/Medium from plan]
- Required outputs: [List from plan]
```

**Evaluar resultado**:
- **❌ CRITICAL**: STOP. Simplificar / Descomponer (task-decomposer) / Regenerar
- **⚠️ WARNING**: Revisar puntos específicos. Simplificar si no justificado
- **✅ PASS**: Continuar con tests

**Principio**: Un red flag → Descartar y regenerar, no "reparar"

#### 1.5. Tests Unitarios (OBLIGATORIO)

**Después de red flags PASS, ANTES de validador**:

1. **Crear 2-3 tests** basados en criterios de aceptación del plan:
   ```python
   def test_criterio_1():
       """Verifica [criterio del plan]"""
       input_data = [input del plan]
       result = component.method(input_data)
       assert result == [output esperado del plan]
   ```

2. **Ejecutar**: `pytest tests/test_component.py -v` (Python) o `npm test` (Node.js)

3. **Criterio de paso**: TODOS pasan, <5 seg/test, sin warnings críticos

**Si fallan**: ⛔ NO avanzar. Corregir y re-ejecutar

#### 1.6. Validación Inmediata (AGENTE validador)

**Pre-requisitos**:
- ✅ Red flags PASS
- ✅ Tests unitarios existen (2-3)
- ✅ Todos los tests PASAN

```
Use the validador agent to perform Level 1 validation on [component]:
- Red flag status: [PASS/WARNING]
- Unit tests: [X] tests, all passing
- First validation: [Yes/No]
```

**Nota sobre Script de Validación**:
- Si existe `workflow/tools/validate.sh` (generado en create-plan), el validador lo detectará y usará automáticamente
- **Ventaja**: 1 comando vs 5-10 comandos (más rápido, menos tokens, logs unificados)
- Si NO existe: Validador ejecuta comandos manualmente (más flexible pero más lento)

Validador verifica: Atomicidad, red flags, errores correlacionados, linting, type checking, convenciones

**Si errores**:
- Falla 1ra vez: Corregir y re-validar
- Falla 2da vez: Corregir, documentar patrón
- Falla 3ra vez: 🚨 ERROR CORRELACIONADO → Ver "Decorrelación de Errores"

**SOLO si PASS** → Siguiente componente

---

### Paso 2: Integración de Componentes

1. **Integrar**: Conectar módulos según dependencias del plan, verificar interfaces
2. **Validar integración**:
   - Probar flujo completo entre componentes
   - Tests de integración
   - **Plan dividido**: Verificar integración entre componentes de diferentes sub-planes
3. **Actualizar dependencias**: `requirements.txt` con versiones, `.gitignore` para archivos sensibles

---

### Paso 3: Validación Final (AGENTE validador Nivel 3)

```
Use the validador agent to perform Level 3 comprehensive validation on the entire implementation
```

Validador ejecuta: Linting, type checking, full test suite, build, coverage, convention compliance, implementation completeness, integration testing, quality assessment

**Checklist crítico**:

**Plan único**:
- [ ] Todos componentes implementados según plan (sección 5.3)
- [ ] Criterios de éxito cumplidos (sección 5.6)
- [ ] Estructura de archivos correcta (sección 5.7)

**Plan dividido**:
- [ ] Todos sub-planes ejecutados según "Orden de Ejecución Recomendado" del plan maestro
- [ ] Cada componente de cada sub-plan implementado según "Tareas Detalladas"
- [ ] "Validaciones de Este Componente" pasadas para TODOS los sub-planes
- [ ] Validaciones globales del plan maestro cumplidas

**Ambos tipos**:
- [ ] Integración funcional entre componentes
- [ ] Minimalismo (no over-engineering)
- [ ] Manejo de errores y logging según plan
- [ ] Dependencias actualizadas

⚠️ **CRÍTICO**: Si issues críticos o tests fallan, NO considerar completo

---

## Manejo de Problemas

### Plan ambiguo o incompleto
**NO asumir**: Preguntar al usuario, documentar decisión

### Librería no funciona
Revisar docs oficial. Si persiste: Consultar usuario antes de cambiar stack

### Componente más complejo de lo estimado
**AGENTE task-decomposer**: Descomponer en tareas más pequeñas
```
Use the task-decomposer agent to break down the following component:
[Descripción y contexto]
```
Implementar tareas atómicas una por una, validando cada una

### Error en el plan
Informar al usuario, proponer corrección, esperar confirmación

---

## Decorrelación de Errores (MAKER)

**🚨 Si tarea falla validación >2 veces** = Error correlacionado (sistemático)

**Por qué es peligroso**: Mismo prompt → Mismo error. Tarea mal definida o no atómica.

**Estrategias (en orden)**:

#### 1. Re-prompting con Paráfrasis
NO regenerar con mismo prompt. Parafrasear:

❌ Original: "Implementar función de hash de password"
✅ Paráfrasis: "Crear método que genere hash bcrypt seguro, retornando string hash"

Cambios: Sinónimos, contexto específico, explicitar output

#### 2. Descomposición Adicional
Tarea NO es atómica. Invocar task-decomposer:
```
Use the task-decomposer agent to further break down this failing task:
Task: [nombre]
Failures: [X] times
Error pattern: [descripción]
```

#### 3. Cambio de Enfoque
Re-consultar docs oficial, buscar alternativa en `workflow/examples/`, considerar librería alternativa (preguntar usuario)

#### 4. Escalado a Usuario
Tras 3 intentos decorrelacionados: Probablemente requisitos ambiguos. Preguntar: ¿Requisito claro? ¿Ejemplo concreto? ¿Stack correcto?

**📝 DOCUMENTAR ERRORES CORRELACIONADOS**:

Después del 2do fallo, documentar en `workflow/request/error-log.md` usando el template `workflow/request/error-log-template.md`:
- Tarea que falló y contexto
- Número de intentos y tipo de error
- Análisis: ¿Es realmente atómica?
- Estrategia de decorrelación aplicada
- Resultado y lecciones aprendidas

**Beneficio**: Identificar patrones, mejorar descomposición futura, evitar repetir errores

---

## Resumen de Agentes a Usar

| Paso | Agente | Cuándo |
|------|--------|--------|
| Paso 0 | `code-analist` | Analizar código base existente |
| Durante implementación | `task-decomposer` | Componente más complejo de lo esperado |
| Paso 1.4 | `red-flag-detector` | Después de implementar, antes de tests |
| Paso 1.6 | `validador` (Nivel 1) | Después de tests, por cada componente |
| Paso 3 | `validador` (Nivel 3) | Validación final comprehensive |

---

## Salida Esperada

Al completar, el proyecto debe tener:
- **Todos componentes implementados**:
  - Plan único: Todos de sección 5.3
  - Plan dividido: Todos de cada sub-plan ejecutado
- Tests unitarios (2-3 por componente) pasando
- Validación comprehensive (Nivel 3) pasada
- Código simple, limpio, comentado apropiadamente
- Manejo de errores y logging según plan
- **Estructura de archivos**:
  - Plan único: Sección 5.7
  - Plan dividido: "Estructura de Archivos" de cada sub-plan
- Dependencias actualizadas, `.gitignore` apropiado

---

## Instrucciones para IA

**Ejecutar en orden estricto**:

1. **Paso 0**: Identificar tipo de plan (único vs dividido) → code-analist
2. **Si plan dividido**: Leer plan maestro → Identificar orden de sub-planes
3. **Para cada componente** (siguiendo orden del plan/sub-plan):
   - Leer sub-plan correspondiente (si dividido)
   - Implementar → red-flag-detector → Tests → validador (L1)
4. **Integración**: Verificar conexiones entre componentes (incluso de diferentes sub-planes)
5. **validador (L3)**: Validación comprehensive del proyecto completo

**Si plan dividido**:
- Leer plan maestro PRIMERO
- Ejecutar sub-planes según "Orden de Ejecución Recomendado"
- Usar navegación interna (📍) entre sub-planes
- Validar integración entre componentes de diferentes sub-planes

**Si falla >2 veces**: Aplicar decorrelación (paráfrasis, descomponer, cambiar enfoque, escalar)

**Reglas**:
- Seguir plan al pie de la letra (plan maestro + sub-planes si dividido)
- Si no está claro: Preguntar (no improvisar)
- Validar constantemente (no esperar al final)
- Reportar progreso al usuario
- Respetar análisis de agentes
