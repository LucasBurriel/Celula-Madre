# Experiment V3 — Market Redesign

## Diagnóstico

Tanto control (random mutation) como experimental (guided mutation) fallaron igual:
- Gen0 $12.56-12.76/tx vs Evolved $7.51-7.66/tx (-39% a -41%)
- Gen2+ casi no recibió transacciones (2% del total)
- La mutación guiada no mejoró nada vs random

**El problema no es la mutación, es el mercado.**

## Problemas estructurales identificados

### 1. Incumbency bias (el más grave)
Los clientes usan `select_agent` con scores basados en track record. Agentes nuevos tienen score 0 → nunca son elegidos → nunca pueden demostrar valor. Loop vicioso.

**No es un subsidio lo que falta — es igualdad de condiciones.** Los clientes actuales discriminan a los nuevos por falta de datos, no por mala performance.

### 2. Sin costos = sin presión selectiva
Costo local = $0. Un agente que genera 200 líneas y uno que genera 20 tienen el mismo margen. Sin costos no hay trade-offs, sin trade-offs no hay evolución.

### 3. Retirement demasiado laxo
max_lifespan=40, max_gen_gap=3. Gen0 puede sobrevivir 40 txs antes de retirarse. En 200 txs, Gen0 acapara el mercado entero.

### 4. Precios demasiado discretos
3 tiers por cliente (bueno/medio/malo). Poca resolución → poca información → poca guía evolutiva.

### 5. Sin muerte por pérdidas
Agentes malos sobreviven indefinidamente consumiendo txs sin aportar.

## Correcciones

### A. Client exploration (epsilon-greedy)
- 70% del tiempo: elige por score (explotación)
- 30% del tiempo: elige random entre todos (exploración)
- **Justificación austriaca:** Los humanos prueban cosas nuevas. Un restaurante nuevo no necesita subsidio — necesita que la gente le dé una chance. La exploración es comportamiento natural del consumidor, no intervención.

### B. Neutral default para nuevos agentes
- Agentes sin historial → score = media del mercado (no 0)
- Esto no es subsidio, es ausencia de información = incertidumbre = neutral

### C. Costos por token simulados
- $0.001 por token generado (simula costo energético/computacional)
- Esto crea presión: verboso = caro, conciso = eficiente
- Net profit = revenue - costs. Ahora importa ser eficiente.

### D. Retirement agresivo
- max_lifespan: 40 → 15 txs
- max_gen_gap: 3 → 2 generaciones
- Fuerza turnover, abre mercado a nuevos

### E. Muerte por pérdidas
- Si avg_price < 6.0 después de 5+ txs → muerte automática
- Equivalente a quiebra empresarial

### F. Precios más granulares
- Evaluar en escala continua, no 3 tiers
- Más señal = mejor guía evolutiva

## Métricas de éxito
1. Gen evolved > Gen0 en avg price/tx
2. Distribución de txs más equitativa entre generaciones
3. Prompts evolucionan de forma interpretable
4. Gen3+ recibe txs significativas
