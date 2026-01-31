# Guía para Crear Planes de Implementación

## Propósito
Este documento define el proceso y criterios para crear planificaciones de código que guiarán la implementación de proyectos. El plan debe ser claro, ejecutable y alineado con principios de simplicidad.

---

## Principios Fundamentales

### 1. Minimalismo (KISS & YAGNI)
- **No overengineering**: La solución más simple que cumpla el requisito.
- **Límite del plan**:
  - Objetivo: 500-800 líneas para un plan completo
  - Si excede 800 líneas: **DIVIDIR en sub-planes** (plan maestro + sub-planes de ~200-300 líneas c/u)
  - Nota: Se refiere al documento del plan, no al código de cada componente
- **Evitar abstracciones prematuras**: Solo crear abstracciones cuando haya duplicación real o necesidad comprobada.

### 2. Modularidad
- Cada componente debe poder entenderse y modificarse de forma independiente.
- Responsabilidad única: un módulo = una función clara.
- Interfaces simples entre módulos.

### 3. Documentación Primero
- **Antes de usar cualquier tecnología o librería**: Leer su documentación oficial.
- **Herramientas disponibles**:
  - MCP Context7 (para documentación de librerías)
  - Búsqueda web (para tecnologías generales)
- **Regla crítica**: Si no encuentras documentación, **NO INVENTAR**. Pedir al usuario que proporcione la documentación.

---

## Proceso de Creación del Plan

### Paso 0: Clarificación de Requisitos (MUY IMPORTANTE)
**ANTES de comenzar a planificar**, es crítico:
- **Preguntar al usuario** sobre cualquier aspecto no especificado del proyecto.
- Identificar gaps de conocimiento o casos de uso que no se están considerando.
- **Solicitar la pila tecnológica** de cada componente si no está especificada previamente.
- Revisar en la carpeta `workflow/examples/` si hay ejemplos de ayuda para alguna implementación similar.
- **No asumir**: Si algo no está claro, preguntar explícitamente antes de continuar.

### Paso 1: Análisis del Requerimiento
- Entender qué se necesita construir (con toda la información recopilada en el Paso 0).
- Identificar tecnologías/librerías necesarias.
- Estimar complejidad y alcance.

### Paso 2: Análisis de Código Base (USAR AGENTE code-analist)
**🤖 AGENTE RECOMENDADO: code-analist**

Antes de diseñar el plan, es crítico entender el contexto del proyecto existente:

#### 2.1. Invocar el agente code-analist
Usar el agente especializado `code-analist` para analizar:
- Patrones de arquitectura y estructura del proyecto existente (si existe)
- Convenciones de código y naming standards del proyecto base
- Patrones de integración entre componentes existentes
- Enfoques de testing y comandos de validación disponibles
- Uso de librerías externas y configuraciones existentes
- Revisar la carpeta `workflow/examples/` para identificar patrones reutilizables

**Cómo usar el agente:**
```
Use the code-analist agent to analyze the project structure and conventions
```

#### 2.2. Aplicar los hallazgos del análisis
- **Consistencia**: El plan debe respetar las convenciones encontradas por code-analist
- **Patrones existentes**: Reutilizar patrones arquitectónicos que ya funcionan
- **Nomenclatura**: Seguir los naming standards identificados
- **Testing**: Alinearse con los enfoques de testing existentes
- **⚠️ ADVERTENCIA CRÍTICA**: Los ejemplos pueden utilizar librerías diferentes a las especificadas en el plan. Por ejemplo, un ejemplo puede usar PydanticAI pero el plan puede requerir LangChain. **NO copiar directamente las librerías del ejemplo**. Usar los ejemplos solo como referencia de patrones y estructura, pero adaptar la implementación a la pila tecnológica confirmada en el Paso 0.

### Paso 3: Investigación de Tecnologías
- Para cada tecnología/librería identificada:
  1. Buscar documentación oficial (MCP Context7 o web).
  2. Entender conceptos clave y mejores prácticas.
  3. Si no se encuentra: **detener y solicitar documentación al usuario**.

### Paso 4: Diseño Modular Inicial

#### 4.1. Diseño de Componentes (SIN task-decomposer todavía)
**IMPORTANTE**: En esta etapa NO usar `task-decomposer` todavía. Primero crear el plan completo.

Basándose en el análisis de `code-analist` y los requisitos:
- Identificar componentes principales del sistema
- Definir responsabilidades de cada módulo
- Identificar dependencias entre módulos
- Para cada componente, confirmar la pila tecnológica (si no se especificó previamente, solicitarla al usuario)
- Diseñar la arquitectura general del sistema

### Paso 5: Estructura del Plan
Crear un documento estructurado que incluya:

#### 5.0. Instrucciones de Ejecución (OBLIGATORIO)
**ANTES de comenzar a ejecutar este plan**, es obligatorio leer completamente el documento `workflow/commands/execute-plan.md` que contiene las instrucciones detalladas sobre cómo ejecutar planes de implementación. Este paso es crítico para asegurar una ejecución correcta y alineada con los principios establecidos.

#### 5.1. Resumen Ejecutivo
- Objetivo del proyecto.
- Alcance (qué se incluye y qué no).
- Tecnologías principales.

#### 5.2. Arquitectura General
- Diagrama de alto nivel (textual o ASCII).
- Componentes principales y sus relaciones.

#### 5.3. Componentes Detallados (ACTUALIZADO - MAKER-inspired)

Para cada componente:
- **Nombre y propósito**
- **Responsabilidades** (UNA sola, si son >1 → descomponer más)
- **Dependencias** (otras librerías o módulos)
- **Interfaz/API** (qué expone al resto)
- **Implementación aproximada** (pasos clave, no código completo)
- **Manejo de errores** (qué errores/excepciones esperar y cómo manejarlos de forma simple)
- **Logging** (puntos críticos donde agregar logs para debugging)
- **Estimación de complejidad** (simple, media, alta)

**NUEVO - Tests Unitarios Obligatorios**:
- **Criterios de aceptación** (mínimo 2-3, verificables):
  - [ ] Criterio 1: [Descripción específica y testeable]
  - [ ] Criterio 2: [Descripción específica y testeable]
  - [ ] Criterio 3: [Manejo de error específico]

- **Tests unitarios requeridos** (mínimo 2-3):
  - Test 1: `test_[nombre]` - Verifica criterio 1
    - Input: [Input específico]
    - Output esperado: [Output específico]
  - Test 2: `test_[nombre]` - Verifica criterio 2
    - Input: [Input específico]
    - Output esperado: [Output específico]
  - Test 3: `test_[nombre]_error` - Verifica manejo de error
    - Input: [Input inválido]
    - Error esperado: [Tipo de excepción]

- **Red flags esperados** (para red-flag-detector):
  - Longitud máxima esperada: ~[X] líneas de código
  - Si implementación excede 2x → Task NO es atómica
  - Formato de output requerido: [Especificación exacta]

**Ejemplo**:
```markdown
### Componente: Hash de Password de Usuario

**Responsabilidades**: Generar hash bcrypt de password (UNA sola responsabilidad)

**Criterios de aceptación**:
- [ ] Función hash_password(plain_password) retorna string hash bcrypt válido
- [ ] Hash generado es diferente cada vez (salt aleatorio)
- [ ] Hash puede verificarse con bcrypt.checkpw()

**Tests unitarios requeridos**:
- Test 1: `test_hash_password_returns_bcrypt_format`
  - Input: "test_password_123"
  - Output: String que empieza con "$2b$" (bcrypt prefix)
- Test 2: `test_hash_password_different_each_time`
  - Input: "same_password" (llamado 2 veces)
  - Output: Dos hashes diferentes
- Test 3: `test_hash_password_verifiable`
  - Input: hash generado + password original
  - Output: bcrypt.checkpw() retorna True

**Red flags**:
- Longitud esperada: ~30-50 LOC
- Si >100 LOC → Probablemente está haciendo validación de password (separar)
- Formato: Función debe estar en auth/utils.py
```

#### 5.4. Dependencias Externas y Configuración
- Lista de librerías necesarias con versiones recomendadas.
- Fuentes de documentación consultadas.
- **Archivo de dependencias**: Especificar archivo (`requirements.txt`, `package.json`, etc.) y su ubicación.
- **Variables de entorno**: Listar variables necesarias (API keys, configuraciones) y dónde definirlas (`.env`, config files).
- **Archivos de configuración**: Indicar qué archivos de configuración se necesitan y su propósito.

#### 5.4.5. Script de Validación Automática (NUEVO - Auto-generado)

**IMPORTANTE**: Una vez definido el stack tecnológico del proyecto, generar script de validación automática para acelerar validaciones durante la ejecución.

**Proceso**:
1. **Identificar stack principal** del proyecto:
   - Python (FastAPI, Django, Flask, etc.)
   - Node.js/TypeScript (Express, Next.js, etc.)
   - Go, Rust, Java, etc.

2. **Copiar template de validación** desde `workflow/examples/validation-templates/`:
   ```bash
   # Para Python
   cp workflow/examples/validation-templates/python-validation.sh workflow/tools/validate.sh
   chmod +x workflow/tools/validate.sh

   # Para Node.js
   cp workflow/examples/validation-templates/nodejs-validation.sh workflow/tools/validate.sh
   chmod +x workflow/tools/validate.sh
   ```

3. **Personalizar script** (opcional):
   - Ajustar umbrales (coverage ≥70% vs ≥80%)
   - Agregar/remover herramientas específicas
   - Adaptar a convenciones del proyecto

4. **Documentar en plan**:
   ```markdown
   ### Script de Validación
   - **Stack**: Python (o Node.js según corresponda)
   - **Ubicación**: `workflow/tools/validate.sh`
   - **Herramientas validadas**:
     - Python: pylint/flake8, mypy, pytest (coverage ≥70%), bandit (security), radon (complexity)
     - Node.js: ESLint, TypeScript (tsc), Jest/Mocha, npm build
   - **Uso**: `./workflow/tools/validate.sh` (ejecuta todas las validaciones automáticamente)
   - **Logs**: Guarda logs en `.validation-*.log` para análisis detallado
   ```

**Beneficio (alineado con MAKER)**:
- **Red-flagging**: Scripts detectan múltiples tipos de problemas (linting, security, complexity)
- **Eficiencia**: 1 comando vs 5-10 comandos (menos tokens, más rápido)
- **Decorrelación**: Logs detallados permiten identificar y corregir errores sistemáticos

#### 5.5. Orden de Implementación
- Secuencia sugerida (qué construir primero).
- Justificación del orden (dependencias, complejidad).

#### 5.6. Validaciones y Testing
- Criterios de éxito para cada componente.
- Cómo validar que funciona correctamente.
- **Tests básicos**: Casos de prueba mínimos para validar funcionalidad (no TDD completo, solo validaciones esenciales).
- **Ejemplos de entrada/salida esperada**: Para facilitar la validación durante la implementación.

#### 5.7. Estructura de Archivos
- Organización de directorios del proyecto.
- Ubicación de cada componente/módulo.
- Convenciones de nomenclatura (snake_case, CamelCase, etc.) según el lenguaje usado.
- Archivos adicionales necesarios (`.env.example`, `.gitignore`, config files).

---

## Paso 6: Descomposición Iterativa del Plan (USAR AGENTE task-decomposer)

**🤖 AGENTE RECOMENDADO: task-decomposer**

**⚠️ CRÍTICO**: Este paso se ejecuta DESPUÉS de haber guardado el plan completo en `workflow/request/plan-[nombre-proyecto].md`.

### 6.1. ¿Cuándo usar task-decomposer?
- Cuando el proyecto tiene múltiples componentes interconectados
- Cuando una funcionalidad es compleja y no está claro por dónde empezar
- Cuando el alcance del proyecto es grande (más de 3-4 componentes principales)
- Cuando necesitas claridad sobre el orden de implementación
- Cuando hay dependencias complejas entre componentes

### 6.2. Proceso de Descomposición Iterativa

**IMPORTANTE**: El agente debe leer el plan ya guardado y descomponerlo iterativamente.

#### 6.2.1. Primera invocación (lectura del plan)
```
Use the task-decomposer agent to read the plan at workflow/request/plan-[nombre-proyecto].md
and identify which tasks/components need further decomposition.
```

El agente debe:
- Leer el plan completo guardado
- Identificar tareas marcadas como `[ATOMIC]` (listas para implementar)
- Identificar tareas marcadas como `[NEEDS_DECOMPOSITION]` (necesitan más desglose)

#### 6.2.2. Invocaciones iterativas (descomposición progresiva)
Para cada tarea que necesite descomposición:

```
Use the task-decomposer agent to decompose Task X.Y "[nombre de la tarea]" from the plan.
Read the current plan state and break down this specific task into atomic subtasks.
```

El agente debe:
1. **Leer el plan actual** (puede haber sido actualizado en iteraciones previas)
2. **Tomar UNA tarea** que necesite descomposición
3. **Dividirla en 2-4 subtareas** más específicas
4. **Actualizar el plan** reemplazando la tarea original por sus subtareas
5. **Guardar el plan actualizado**

#### 6.2.3. Criterio de finalización
Continuar iterativamente hasta que:
- Todas las tareas sean `[ATOMIC]` (cumplen los 7 criterios de atomicidad)
- Cada tarea tenga 2-3 tests unitarios definidos
- Cada tarea tenga red flags esperados especificados

### 6.3. Aplicar la Descomposición al Plan

Después de cada iteración, el plan debe actualizarse con:
- Subtareas atómicas en lugar de tareas generales
- Orden de ejecución refinado
- Dependencias específicas entre subtareas
- Criterios de aceptación detallados para cada subtarea
- Tests unitarios específicos por subtarea

**Ejemplo de transformación**:

**ANTES (tarea general en el plan inicial)**:
```markdown
### Componente: Sistema de Autenticación
- Implementar login, registro y validación de usuarios
- Estimar: Alta complejidad
```

**DESPUÉS (tras descomposición iterativa)**:
```markdown
### Tarea 1.1: Hash de Password [ATOMIC]
- **Responsabilidad**: Generar hash bcrypt
- **Tests**: test_hash_password_returns_bcrypt_format, test_hash_password_verifiable
- **Red flags**: ~30-50 LOC, formato bcrypt requerido

### Tarea 1.2: Validación de Email [ATOMIC]
- **Responsabilidad**: Validar formato de email con regex
- **Tests**: test_validate_email_valid_format, test_validate_email_invalid_raises_error
- **Red flags**: ~20-30 LOC, debe usar regex estándar

### Tarea 1.3: Endpoint de Registro [ATOMIC]
- **Responsabilidad**: Recibir POST /register y crear usuario
- **Tests**: test_register_endpoint_success, test_register_endpoint_duplicate_email
- **Red flags**: ~50-80 LOC, debe retornar 201 en éxito
```

---

## Paso 6.5: División de Planes Extensos (NUEVO)

**⚠️ PROBLEMA**: Después de descomposición iterativa con task-decomposer, el plan puede exceder 1000 líneas, dificultando su manejo y navegación.

### 6.5.1. Cuándo Dividir el Plan

**Umbral de división**: Si el plan descompuesto excede **800 líneas**, dividirlo en múltiples archivos.

**Indicadores**:
- Plan tiene >10 componentes principales
- Descomposición generó >30 tareas atómicas
- Archivo difícil de navegar o leer completo
- Contexto muy grande para el modelo

### 6.5.2. Estrategia de División

**Dividir por componente o módulo lógico**, NO arbitrariamente por número de líneas.

**Estructura recomendada** (~200-300 líneas por sub-plan):

```
workflow/request/
├── plan-master-[proyecto].md           # Índice principal (obligatorio)
├── plan-1.1-[componente-1].md          # Sub-plan 1
├── plan-1.2-[componente-2].md          # Sub-plan 2
├── plan-1.3-[componente-3].md          # Sub-plan 3
└── plan-1.N-[componente-N].md          # Sub-plan N
```

### 6.5.3. Contenido del Plan Maestro

El **plan maestro** (`plan-master-[proyecto].md`) debe contener:

```markdown
# Plan Maestro: [Nombre del Proyecto]

## ⚠️ IMPORTANTE
Este plan ha sido dividido en múltiples archivos debido a su extensión (>800 líneas).
Cada componente tiene su propio sub-plan detallado.

## Instrucciones de Ejecución
**ANTES de ejecutar**, leer: `workflow/commands/execute-plan.md`

---

## Resumen Ejecutivo
- **Objetivo**: [Descripción breve]
- **Alcance**: [Qué incluye y qué no]
- **Stack tecnológico**: [Tecnologías principales]
- **Total de sub-planes**: [N]

## Arquitectura General
[Diagrama de alto nivel textual/ASCII]
[Componentes principales y relaciones]

## Índice de Sub-Planes

### 1. Plan 1.1: [Componente 1]
- **Archivo**: `plan-1.1-[componente-1].md`
- **Descripción**: [Qué cubre este sub-plan]
- **Tareas atómicas**: [N]
- **Dependencias**: [Ninguno / Plan 1.X]

### 2. Plan 1.2: [Componente 2]
- **Archivo**: `plan-1.2-[componente-2].md`
- **Descripción**: [Qué cubre este sub-plan]
- **Tareas atómicas**: [N]
- **Dependencias**: [Plan 1.1]

[Continuar con todos los sub-planes...]

## Orden de Ejecución Recomendado

**Fase 1** (Paralelo):
- Plan 1.1: [Componente 1]
- Plan 1.2: [Componente 2]

**Fase 2** (Secuencial, depende de Fase 1):
- Plan 1.3: [Componente 3]

**Fase 3** (Final):
- Plan 1.N: [Integración/Validación]

## Dependencias Externas y Configuración
[Centralizadas aquí para evitar duplicación]

### Librerías Globales
[Lista con versiones]

### Variables de Entorno
[Lista centralizada]

### Script de Validación
- **Stack**: [Python/Node.js/etc]
- **Ubicación**: `workflow/tools/validate.sh`
- **Uso**: `./workflow/tools/validate.sh`

## Validaciones Globales
[Criterios de éxito del proyecto completo]

---

**Próximos pasos**: Leer el sub-plan correspondiente según orden de ejecución.
```

### 6.5.4. Contenido de Cada Sub-Plan

Cada sub-plan (`plan-1.X-[componente].md`) debe incluir:

```markdown
# Sub-Plan 1.X: [Nombre del Componente]

## 📍 Navegación
- **Plan Maestro**: `plan-master-[proyecto].md`
- **Sub-plan anterior**: `plan-1.[X-1]-[componente].md` (si aplica)
- **Sub-plan siguiente**: `plan-1.[X+1]-[componente].md` (si aplica)

---

## Resumen de Este Componente
- **Objetivo**: [Qué resuelve este componente]
- **Dependencias**: [De qué otros sub-planes depende]
- **Tareas atómicas**: [N]

## Tareas Detalladas

### Tarea 1.X.1: [Nombre] [ATOMIC]
- **Responsabilidad**: [Descripción]
- **Dependencias**: [Ninguna / Tarea 1.Y.Z]
- **Criterios de aceptación**:
  - [ ] [Criterio 1]
  - [ ] [Criterio 2]
- **Tests unitarios**:
  - `test_[nombre]`: [Descripción]
- **Red flags**: [Longitud esperada, formato]

### Tarea 1.X.2: [Nombre] [ATOMIC]
[...]

[Continuar con todas las tareas de este componente...]

## Validaciones de Este Componente
- [Cómo validar que este componente funciona correctamente]
- [Tests de integración con otros componentes]

## Estructura de Archivos de Este Componente
```
proyecto/
├── [directorio relevante]/
│   ├── [archivo 1]
│   └── [archivo 2]
```

---

**Próximo sub-plan**: `plan-1.[X+1]-[componente].md` (si aplica)
```

### 6.5.5. Proceso de División

1. **Identificar componentes lógicos** del plan descompuesto
2. **Agrupar tareas atómicas** por componente (mantener cohesión)
3. **Crear plan maestro** con índice y arquitectura general
4. **Crear sub-planes** por componente (~200-300 líneas cada uno)
5. **Agregar navegación** entre sub-planes (links relativos)
6. **Centralizar información global** en plan maestro (dependencias, config)
7. **Validar completitud**: Todas las tareas del plan original están en algún sub-plan

### 6.5.6. Convención de Nomenclatura

- **Plan maestro**: `plan-master-[nombre-proyecto].md`
- **Sub-planes**: `plan-1.X-[componente-descriptivo].md`
  - Numeración: `1.1`, `1.2`, `1.3`, etc. (orden lógico de ejecución)
  - Nombre descriptivo: `authentication`, `database`, `api-endpoints`, `frontend`, etc.

**Ejemplos**:
- `plan-master-ecommerce-backend.md`
- `plan-1.1-authentication.md`
- `plan-1.2-database-models.md`
- `plan-1.3-product-api.md`
- `plan-1.4-order-processing.md`

### 6.5.7. Beneficios de la División

✅ **Manejabilidad**: Archivos de ~200-300 líneas vs 1000+ líneas
✅ **Contexto reducido**: El modelo solo carga el sub-plan relevante
✅ **Navegación clara**: Fácil encontrar componentes específicos
✅ **Ejecución modular**: Implementar componente por componente
✅ **Paralelización**: Diferentes sub-planes pueden ejecutarse en paralelo (si no hay dependencias)

---

## Validaciones Antes de Entregar

Antes de considerar el plan completo, verificar:

- [ ] Se preguntó al usuario sobre aspectos no especificados antes de planificar.
- [ ] **Se usó el agente code-analist** para analizar la estructura, convenciones y patrones del proyecto existente.
- [ ] **El plan respeta las convenciones** identificadas por code-analist (nomenclatura, estructura, patrones).
- [ ] **Se escribió y guardó el plan completo PRIMERO** en `workflow/request/plan-[nombre-proyecto].md` (Paso 5).
- [ ] **DESPUÉS de guardar el plan, se usó el agente task-decomposer** para descomponer el plan en tareas atómicas (Paso 6) - solo si el proyecto es complejo.
- [ ] **La descomposición fue ITERATIVA sobre el plan guardado**: el agente leyó el plan, dividió tareas, y actualizó el documento progresivamente.
- [ ] **Si el plan excede 800 líneas, se dividió en sub-planes** (Paso 6.5): plan maestro + sub-planes por componente (~200-300 líneas cada uno).
- [ ] **Todas las tareas descompuestas llegaron a nivel `[ATOMIC]`** (cumplen 7 criterios de atomicidad).
- [ ] **Cada tarea atómica especifica 2-3 tests unitarios obligatorios** con inputs/outputs esperados.
- [ ] **Cada tarea especifica red flags esperados** (longitud máxima, formato requerido).
- [ ] Se revisó la carpeta `workflow/examples/` en busca de ejemplos relevantes.
- [ ] Se verificó que las librerías de los ejemplos no se copiaron directamente si difieren de la pila tecnológica del plan.
- [ ] Se confirmó la pila tecnológica de cada componente (o se solicitó al usuario).
- [ ] **Se generó script de validación automática** (`workflow/tools/validate.sh`) basándose en el stack definido.
- [ ] Todas las tecnologías tienen documentación consultada o solicitada.
- [ ] El plan completo tiene entre 500 y 1000 líneas (no se refiere al código).
- [ ] No hay overengineering (solución más simple posible).
- [ ] Cada módulo tiene responsabilidad única y clara.
- [ ] Las dependencias entre módulos están definidas.
- [ ] El orden de implementación es lógico.
- [ ] No se inventó ninguna funcionalidad sin documentación.
- [ ] El plan incluye la sección 5.0 con instrucciones para leer `workflow/commands/execute-plan.md` antes de ejecutar.
- [ ] Cada componente especifica manejo de errores y logging necesario.
- [ ] Se definieron variables de entorno y archivos de configuración necesarios.
- [ ] Se especificó la estructura de archivos y convenciones de nomenclatura.
- [ ] Se definieron tests básicos y ejemplos de entrada/salida para validación.

---

## Formato de Salida

El plan debe entregarse como un documento Markdown estructurado, listo para ser usado en la fase de ejecución. **Debe incluir obligatoriamente la sección 5.0** que instruye a leer `workflow/commands/execute-plan.md` antes de comenzar la ejecución.

### Ubicación del Plan
**El plan debe guardarse en la carpeta `workflow/request/`** junto con todo lo relacionado a instrucciones, notas de planificación o documentos generados por el agente durante el proceso de creación del plan. Esta carpeta centraliza toda la documentación relacionada con la planificación y requisitos del proyecto.

**📝 Archivos en `workflow/request/`**:
- **Plan de implementación**: `workflow/request/plan-[nombre-proyecto].md` (generado por create-plan)
- **Log de errores correlacionados**: `workflow/request/error-log.md` (se crea durante execute-plan si hay errores repetidos)
  - Usar template: `workflow/request/error-log-template.md` como referencia
  - Documenta tareas que fallan >2 veces para identificar patrones (MAKER paper)
- **Otros documentos**: Notas, requisitos, diagramas, etc.

---

## Notas Importantes

- **Flujo correcto de descomposición (CRÍTICO)**:
  1. Escribir y guardar el plan completo PRIMERO (Paso 5)
  2. LUEGO usar task-decomposer para descomponer el plan ya guardado (Paso 6)
  3. Si el plan excede 800 líneas, dividirlo en sub-planes (Paso 6.5)
  4. El agente debe leer el plan, dividir tareas iterativamente, y actualizar el documento progresivamente
  - **Razón**: Si se descompone antes de escribir el plan, se pueden olvidar partes importantes del sistema
- **División de planes extensos (NUEVO - Paso 6.5)**: Si después de la descomposición el plan excede **800 líneas**, dividirlo en:
  - **Plan maestro** (`plan-master-[proyecto].md`): Índice, arquitectura general, dependencias globales
  - **Sub-planes** por componente (`plan-1.X-[componente].md`): ~200-300 líneas cada uno
  - **Dividir por lógica**, no arbitrariamente: Agrupar tareas relacionadas por componente/módulo
  - **Beneficios**: Manejabilidad, contexto reducido, navegación clara, ejecución modular
- **Usar el agente code-analist (CRÍTICO)**: Antes de crear el plan, SIEMPRE usar el agente code-analist para entender las convenciones, patrones y estructura del proyecto. El plan debe ser consistente con el análisis del agente.
- **Usar el agente task-decomposer (RECOMENDADO para proyectos complejos)**: DESPUÉS de guardar el plan completo, usar el agente task-decomposer para descomponer iterativamente las tareas en unidades atómicas. El agente debe trabajar sobre el plan guardado, no sobre ideas en memoria.
- **Preguntar primero (MUY IMPORTANTE)**: Antes de planificar, identificar y preguntar sobre cualquier aspecto no especificado para evitar gaps de conocimiento o casos no considerados.
- **Revisar ejemplos con precaución**: Siempre consultar `workflow/examples/` antes de planificar para aprovechar patrones existentes, pero **NO copiar librerías directamente** si difieren de la pila tecnológica del plan. Los ejemplos son referencia de estructura/patrones, no de tecnologías específicas.
- **Pila tecnológica**: Si no está especificada, siempre solicitarla al usuario antes de continuar.
- **No asumir**: Si algo no está claro, preguntar explícitamente antes de planificar.
- **Iterativo**: El plan puede refinarse después de la primera implementación.
- **Priorizar simplicidad**: Mejor un plan simple que funcione que uno complejo que falle.