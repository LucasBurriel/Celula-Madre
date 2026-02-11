# Paper Notes — Célula Madre Research

## GEA: Group-Evolving Agents (arXiv:2602.04837, Feb 2026)
**Estado del arte en evolución de agentes. Competencia directa.**

### Arquitectura
- Unidad de evolución: **grupo de K agentes** (no individuos como DGM)
- Selección: `score(i) = performance × √novelty` donde novelty = distancia coseno promedio a M vecinos más cercanos en espacio de task-success vectors
- Evolución en 3 pasos por agente:
  1. **Collect traces**: patches aplicados, task patches, execution logs, outcomes
  2. **Reflect**: módulo de reflexión analiza traces compartidos del grupo → genera "evolution directives"
  3. **Evolve**: genera framework-level patches basados en directivas
- **Experience sharing**: todos los agentes del grupo comparten sus traces, no evolución aislada
- Archive: keep all que compilen y tengan funcionalidad básica de coding

### Resultados
- 71.0% SWE-bench Verified (vs 56.7% DGM, vs 71.8% mejor humano-diseñado)
- 88.3% Polyglot (vs 68.3% DGM, vs 52.0% mejor humano-diseñado)
- Fixes bugs en 1.4 iteraciones (vs 5 para DGM)
- Transferible entre GPT y Claude

### Key insight
La innovación clave es que DGM tiene ramas aisladas (tree-structured) donde la diversidad se pierde. GEA comparte experiencia entre agentes, convirtiendo diversidad exploratoria en progreso acumulativo.

### Relevancia para Célula Madre
- GEA sigue usando **benchmarks** como fitness → mismo problema que DGM
- Su selección performance×novelty es interesante — podríamos usar precio×novelty
- El experience sharing entre grupo es ortogonal a nuestra tesis (mercado vs benchmark)
- Podríamos implementar GEA-style groups CON selección de mercado = combinación única

---

## Beyond the Sum (arXiv:2501.10388, Jan 2025)
**Paper más cercano a nuestra tesis filosófica.**

### Tesis
- AI agents como participantes económicos independientes en mercados digitales
- Markets > centralized systems para coordinar agentes (Hayek, Schumpeter, Smith)
- Price signals como feedback distribuido: profits = valor creado, losses = recursos mal asignados
- Agents tienen ventajas únicas: replicación perfecta, operación continua, learning colectivo

### Lo que propone pero NO implementa
- Infraestructura para agentes en mercados: identity, payments, service discovery, interfaces
- Agentes que compiten/cooperan via mercados emergen inteligencia superior

### Limitaciones
- Paper conceptual, no implementación
- No habla de evolución/mutación/selección genética — solo coordinación via mercados
- Foco en infraestructura más que en mecanismo evolutivo

### Relevancia para Célula Madre  
- **Base teórica perfecta** para justificar market selection
- Citable como "market forces for agent improvement" — pero nosotros vamos más allá con evolución explícita
- Su gap (no implementación) es exactamente lo que nosotros llenamos

---

## A-Evolve / Evolution-Time Compute (arXiv:2602.00359, Jan 2026)
**Position paper que introduce "evolution-time compute" como tercer eje.**

### Tesis
- Hay 3 ejes de compute: training-time, inference-time, evolution-time
- Evolution-time compute = iteraciones de auto-mejora del agente
- Propone agente "evolver" autónomo que diagnostica fallas y se auto-modifica
- +16% task completion con más evolution-time compute

### Relevancia
- Valida que evolución de agentes escala con compute
- Pero sigue usando benchmarks como fitness
- Nuestro contribution: evolution-time compute guiado por mercado, no benchmarks

---

## DGM Original (arXiv:2505.22954, May 2025)
Ya lo conocemos. Benchmark: SWE-bench. Selección: score_child_prop. Código completo del agente evoluciona via Docker + git patches. Modelo fuerte (o1) diagnostica, modelo fuerte (Claude) implementa.

---

## Magentic Marketplace (arXiv:2510.25779, Microsoft, Oct 2025)
Simulador de mercados de agentes buyer/seller. No evolución. Estudia biases (first-proposal, scale degradation). Open-source. Podría ser infraestructura para Célula Madre Phase 3.

---

## REBEL (arXiv:2602.06248, Feb 2026)
Evolutionary prompt optimization para adversarial attacks. Usa LLM secundario para evolucionar prompts. ASR hasta 93%. Técnicamente similar a nuestro prompt-evolution approach pero con objetivo diferente (jailbreaking vs improvement).

---

## Evolving Constitutions (arXiv:2602.00755, Jan 2026)
Multi-island genetic programming para evolucionar "constituciones" (reglas) de sistemas multi-agente. Fitness: Societal Stability Score. +123% sobre baselines. Interesante: evoluciona REGLAS no agentes.

---

# Mapa del Campo

```
                    BENCHMARK FITNESS          MARKET FITNESS
                    ─────────────────          ──────────────
CODE EVOLUTION      DGM (2025)                 ???
                    GEA (2026)                 
                    A-Evolve (2026)            

PROMPT EVOLUTION    REBEL (2026)               ???
                    Nuestro DGM v1             

RULE EVOLUTION      Evolving Const. (2026)     ???

MARKET INFRA        ---                        Beyond the Sum (2025)
                                               Magentic (2025)
                                               Agent Economies (2025)
```

**Célula Madre llena el cuadrante "CODE EVOLUTION × MARKET FITNESS"**
Nadie lo ha hecho. Los más cercanos son Beyond the Sum (market pero sin evolución) y DGM/GEA (evolución pero sin market).
