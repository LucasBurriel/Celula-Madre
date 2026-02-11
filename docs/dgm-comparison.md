# DGM Original vs Nuestro DGM — Comparación Detallada

## Arquitectura General

| Aspecto | DGM Original (Sakana) | Nuestro DGM |
|---------|----------------------|-------------|
| **Qué evoluciona** | Código completo del agente (coding_agent.py + tools/ + prompts/) via git patches | Solo el system prompt del agente |
| **Cómo muta** | Coding agent modifica su propio código fuente dentro de Docker | LLM genera un nuevo system prompt |
| **Evaluación** | SWE-bench (GitHub issues reales) o Polyglot benchmark | Tasks de coding custom (regex, json_parser, etc.) |
| **Selección** | score_child_prop (sigmoid + 1/(1+children)) | score_child_prop (misma fórmula) ✅ |
| **Archive** | keep_all (todo lo que compila) | keep_all ✅ |
| **Diagnóstico** | o1 (fuerte) analiza logs + tests + código del agente | Mismo modelo (Gemma 4B) analiza logs + tests |
| **Implementación** | Coding agent (Claude) edita su propio código con tools (bash, editor) en Docker | LLM genera nuevo prompt directamente |
| **Infraestructura** | Docker containers, git patches, SWE-bench harness | Python directo, tempdir, pytest |

## Diferencias Críticas

### 1. 🔴 Lo que evoluciona (MAYOR DIFERENCIA)
**DGM original**: Evoluciona el **código completo** del agente — puede añadir tools nuevos, cambiar el flujo de `forward()`, modificar prompts, agregar utilities. Los cambios se guardan como git patches que se acumulan.

**Nuestro DGM**: Solo evoluciona el **system prompt**. El código del agente (`CodingAgent.forward()`) es fijo — siempre hace: generar código → escribir → pytest → (optional) fix.

**Impacto**: El DGM original puede descubrir mejoras arquitectónicas (nuevos tools, retry strategies, etc.), no solo mejoras de instrucciones. Nuestro DGM está limitado a prompt engineering evolutivo.

### 2. 🔴 Modelo de diagnóstico vs agente
**DGM original**: Usa **o1** (reasoning model fuerte) para diagnóstico, y **Claude** para implementación. Son modelos diferentes y ambos potentes.

**Nuestro DGM**: Usa **Gemma 4B** para ambos. Un modelo débil diagnosticando sus propios errores y proponiéndose mejoras a sí mismo.

**Impacto**: La calidad del diagnóstico es mucho peor. El modelo no tiene la capacidad de razonamiento profundo para identificar por qué falla.

### 3. 🟡 Evaluación
**DGM original**: SWE-bench Verified — 500+ issues reales de GitHub. Evaluación robusta y reproducible.

**Nuestro DGM**: 3-4 tasks custom. Poca diversidad, alta varianza.

### 4. 🟡 Docker isolation
**DGM original**: Cada mutación corre en un Docker container aislado. El agente modifica código, se commitea, se evalúa. Si rompe algo, el container se destruye.

**Nuestro DGM**: Todo corre en el mismo proceso Python. Sin aislamiento.

### 5. 🟢 Selección (CORRECTA)
Ambos usan `score_child_prop`:
```
probability = sigmoid(10*(score-0.5)) × 1/(1+children_count)
```
Favorece agentes con buen score que no han sido explorados mucho. ✅

### 6. 🟢 Archive (CORRECTA)  
Ambos usan `keep_all` — todo agente que compila/corre se mantiene en el archivo. ✅

### 7. 🟡 Tipos de diagnóstico
**DGM original**: 4 tipos de prompts de diagnóstico:
- `solve_empty_patches` (25% chance) — cuando el agente no genera patch
- `solve_stochasticity` (25% chance) — manejar varianza del agente
- `solve_contextlength` (conditional) — cuando excede contexto
- Normal — analizar un issue específico que falló

**Nuestro DGM**: Un solo tipo de diagnóstico (analizar tarea fallida).

### 8. 🟡 Gating
**DGM original**: `filter_compiled` — solo agentes que compilan y no tienen todos patches vacíos entran al archive. Opcionalmente `keep_better` con noise leeway.

**Nuestro DGM**: Todo entra al archive sin filtro. ✅ (coincide con default `keep_all`)

## Qué necesitamos cambiar para ser fieles al DGM

### Prioridad Alta (afecta validez del paper)
1. **Evolucionar código, no solo prompts** — El claim central de DGM es self-improvement del código. Si solo evolucionamos prompts, no estamos replicando DGM, estamos haciendo "evolutionary prompt engineering".
2. **Usar modelo fuerte para diagnóstico** — Necesitamos al menos un modelo razonable para diagnosticar. Opciones:
   - Qwen3-30B (local, más capaz) para diagnóstico + Gemma para ejecución
   - Claude/GPT via API para diagnóstico (costo)

### Prioridad Media
3. **Docker isolation** — Para evolucionar código de forma segura necesitamos containers
4. **Más tasks** — 3-4 no es suficiente. Necesitamos 20+ tareas diversas
5. **Múltiples tipos de diagnóstico** — Al menos empty_patches y stochasticity

### Prioridad Baja
6. **Git patches** — Nice to have para tracking, no esencial
7. **Two-tier evaluation** — DGM evalúa en subset chico primero, si pasa threshold evalúa en set grande
8. **Post-improvement diagnosis** — Diagnosticar si la mejora realmente ayudó

## Opciones Realistas

### Opción A: Prompt Evolution (lo que tenemos)
- ✅ Funciona, es rápido, corre local
- ❌ No es DGM, es "evolutionary prompt engineering"
- Sirve como **baseline** para comparar con DGM real

### Opción B: Code Evolution con Gemma
- Gemma modifica su propio código (el CodingAgent)
- Problema: Gemma 4B no puede generar código complejo de forma confiable
- Necesitamos Docker para aislar mutaciones

### Opción C: Code Evolution con Qwen (diagnóstico) + Gemma (ejecución)
- Qwen3-30B diagnostica y genera patches de código
- Gemma 4B es el agente que se evalúa en tasks
- Más fiel al DGM (modelo fuerte para diagnóstico, modelo evaluado diferente)
- Requiere cargar ambos modelos (problema de VRAM que ya tuvimos)

### Opción D: API para diagnóstico + Gemma local para ejecución
- Claude/GPT para diagnóstico (pocas llamadas, bajo costo)
- Gemma local para ejecución (muchas llamadas, gratis)
- Más fiel al DGM original (que usa o1 + Claude)
- Costo estimado: ~$1-5 por run completo
