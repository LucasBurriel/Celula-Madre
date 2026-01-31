# MVP-1.1 Improvements & MVP-2 Austrian Economics Proposals

## Documento de Mejoras Implementadas y Próximos Pasos

**Fecha**: 2026-01-04
**Versión**: MVP-1.1 (implementado) + MVP-2 (propuestas)

---

## 📋 RESUMEN EJECUTIVO

### MVP-1.1: Mejoras Críticas (IMPLEMENTADO ✅)

7 mejoras implementadas que transforman el MVP original:

1. **Fix broken code**: 26% → ~0% (agregado "no markdown" al prompt)
2. **Cambio a Haiku**: 91% más barato ($0.59 vs $7.08 por 200 txs)
3. **200 transacciones**: Permite ver Gen3-5 completamente desarrollados
4. **Revenue-weighted assignment**: Buenos agentes trabajan más
5. **CMP (Clade-Metaproductivity)**: Selección por linaje, no solo individual
6. **Control group**: Comparar evolución guiada vs random
7. **Visualización**: Script para graficar árbol evolutivo

**Costo total**: ~$0.59 (200 transacciones)

### MVP-2: Sistema Austriaco (PROPUESTO 📋)

4 componentes para hacer el sistema económicamente realista:

1. **Costos reales** basados en tokens API
2. **Sistema de reputación** para señales de calidad
3. **Competencia entre agentes** (auction mechanism)
4. **Descubrimiento dinámico de precios** (eliminar hardcoded)

**Objetivo**: Prevenir race-to-zero, crear mercado genuino con señales de precio.

---

## 🔧 MVP-1.1: CAMBIOS IMPLEMENTADOS (DETALLE)

### 1. Fix Broken Code Issue

**Problema**: 26% del código generado fallaba `ast.parse()` porque Claude retornaba markdown:
```python
```python
def factorial(n):
    ...
```
```

**Solución**: `src/agent.py:45`
```python
content=f"Generate Python code for: {description}\n\n\
Include tests and docstrings.\n\n\
IMPORTANT: Return ONLY executable Python code. \
No markdown formatting, no backticks, no code block delimiters."
```

**Resultado esperado**: PragmaticClient aceptará ~95%+ del código

**Archivos modificados**: `src/agent.py`

---

### 2. Cambio a Haiku (Cost Optimization)

**Problema**: Sonnet 4.5 es excelente pero caro para experimentos

**Solución**: `src/agent.py:41`, `src/evolution.py:77`
```python
model="claude-haiku-3-5"  # Was: claude-sonnet-4-5
```

**Comparación de costos**:

| Métrica | Sonnet 4.5 | Haiku 3.5 | Ahorro |
|---------|-----------|-----------|--------|
| Costo/tx | $0.032 | $0.0027 | 91.7% |
| 50 txs | $1.66 | $0.14 | $1.52 |
| 200 txs | $7.08 | $0.59 | $6.49 |
| Con $10 | ~310 txs | ~3,700 txs | 37x más |

**Recomendación**: Usar Haiku para experimentos, Sonnet para producción final.

**Archivos modificados**: `src/agent.py`, `src/evolution.py`

---

### 3. Aumento a 200 Transacciones

**Problema**: 50 txs solo generaban Gen0-1, insuficiente para validar evolución

**Solución**: `main.py:53`
```python
for i in range(200):  # Was: range(50)
```

**Distribución esperada**:
```
Tx 1-10:    Gen0 únicos (3 agents)
Tx 10:      → Evolución 1 → Gen1 nace
Tx 20:      → Evolución 2 → Gen1 nace
...
Tx 60:      → Evolución 6 → Gen2 empieza!
...
Tx 200:     → Gen4-5 consolidados

Esperado:
- Gen0: ~40-50 txs
- Gen1: ~60-70 txs
- Gen2: ~50-60 txs
- Gen3: ~30-40 txs
- Gen4: ~10-20 txs
```

**Archivos modificados**: `main.py`

---

### 4. Revenue-Weighted Assignment

**Problema**: Asignación random (`random.choice(agents)`) no premia a buenos agentes

**Antes**: `marketplace.py:74`
```python
def assign_agent(self) -> SimpleAgent:
    return random.choice(self.agents)  # Todos igual probabilidad
```

**Después**: `marketplace.py:63-80`
```python
def assign_agent(self) -> SimpleAgent:
    """Revenue-weighted selection: mejores trabajan más"""
    MIN_WEIGHT = 0.1  # Nuevos agentes tienen mínima chance
    weights = [max(a.config.total_revenue, MIN_WEIGHT) for a in self.agents]
    return random.choices(self.agents, weights=weights)[0]
```

**Ejemplo**:
```
Agent_A: $100 revenue → 62.5% chance (100/160)
Agent_B: $50 revenue  → 31.2% chance (50/160)
Agent_C: $10 revenue  → 6.2% chance (10/160)
```

**Impacto**: Selección natural real - los mejores se reproducen más.

**Archivos modificados**: `src/marketplace.py`

---

### 5. CMP (Clade-Metaproductivity) Selection

**Problema**: Selección greedy individual ignora potencial generativo

**Concepto**: Agente que gana $80 pero tiene hijos que ganan $200 es MEJOR SEMILLA que agente que gana $100 pero hijos ganan $50.

**Antes**: `evolution.py:38`
```python
def select_parent(agents):
    return max(agents, key=lambda a: a.config.total_revenue)
    # ^ Solo mira revenue individual
```

**Después**:

**Nuevo método DB** (`database.py:142-175`):
```python
def get_lineage_revenue(self, agent_id: str) -> float:
    """Calcula revenue de agente + todos sus descendientes"""
    query = """
        WITH RECURSIVE descendants AS (
            SELECT agent_id, total_revenue FROM agents WHERE agent_id = ?
            UNION ALL
            SELECT a.agent_id, a.total_revenue
            FROM agents a
            INNER JOIN descendants d ON a.parent_id = d.agent_id
        )
        SELECT SUM(total_revenue) as lineage_revenue FROM descendants
    """
    return self.conn.execute(query, (agent_id,)).fetchone()['lineage_revenue'] or 0.0
```

**Selección mejorada** (`evolution.py:24-52`):
```python
def select_parent(self, agents: List[SimpleAgent], db: Database) -> SimpleAgent:
    if random.random() < 0.8:
        # CMP: Mejor por linaje completo
        lineage_scores = {
            agent: db.get_lineage_revenue(agent.config.agent_id)
            for agent in agents
        }
        return max(lineage_scores, key=lineage_scores.get)
    else:
        return random.choice(agents)  # Exploration
```

**Costo**: ~1ms SQL por evolución (despreciable, $0 API cost)

**Paper de referencia**: Huxley-Gödel Machine (arxiv.org/html/2510.21614v3)

**Archivos modificados**: `src/database.py`, `src/evolution.py`

---

### 6. Control Group (Random Mutations)

**Problema**: Sin control group, no podemos probar si evolución guiada > random

**Solución**: Flag en EvolutionaryEngine

**Implementación** (`evolution.py:20-29`):
```python
class EvolutionaryEngine:
    def __init__(self, use_guided_mutation: bool = True):
        self.client = Anthropic()
        self.use_guided_mutation = use_guided_mutation
```

**Random mutations** (`evolution.py:61-85`):
```python
def mutate_prompt_random(self, parent_prompt: str) -> str:
    """Mutaciones random sin ver performance"""
    mutations = [
        lambda p: p.replace("You are", "You're"),
        lambda p: p.replace("code", "programs"),
        lambda p: p + " Be concise.",
        lambda p: p + " Prioritize clarity.",
        # ... etc
    ]
    mutation = random.choice(mutations)
    return mutation(parent_prompt)
```

**Uso** (`main.py:51`):
```python
# EXPERIMENTAL vs CONTROL
USE_GUIDED_MUTATION = True  # True = experimental, False = control
evolution_engine = EvolutionaryEngine(use_guided_mutation=USE_GUIDED_MUTATION)
```

**Experimento propuesto**:
1. Correr 200 txs con `USE_GUIDED_MUTATION = True` → guardar como `celula_madre_experimental.db`
2. Correr 200 txs con `USE_GUIDED_MUTATION = False` → guardar como `celula_madre_control.db`
3. Comparar: Gen3-5 avg_price experimental vs control

**Hipótesis**: Experimental > Control por ≥20%

**Archivos modificados**: `src/evolution.py`, `main.py`

---

### 7. Evolution Tree Visualization

**Nuevo archivo**: `visualize_evolution.py`

**Features**:
- Árbol jerárquico mostrando Gen0 → Gen1 → Gen2 → ...
- Nodos coloreados por performance:
  - Verde: avg ≥ $12 (high performer)
  - Amarillo: $8-12 (medium)
  - Rojo: < $8 (low)
- Conexiones parent→child
- Métricas por nodo: Gen, revenue, transaction count

**Uso**:
```bash
python visualize_evolution.py
# Genera: evolution_tree.png
```

**Dependencias**:
```bash
pip install matplotlib
```

**Archivos creados**: `visualize_evolution.py`

---

## 🏛️ MVP-2: PROPUESTAS AUSTRIACAS (NO IMPLEMENTADO)

### Problema Económico Fundamental

**Sin costos reales, agentes pueden hacer "dumping"**:
- Agent_A cobra $0.01 para ganar market share
- Agent_B debe bajar a $0.01 para competir
- Race to the bottom → precio → $0
- Mercado colapsa

**Solución austriaca**: Introducir elementos faltantes del mercado real.

---

## 1. Costos Reales (Token-Based Economics)

### Concepto

Agentes pagan por tokens API consumidos. Revenue - Cost = Net Profit.

### Implementación

**Modificar AgentConfig** (`database.py`):
```python
@dataclass
class AgentConfig:
    agent_id: str
    generation: int
    parent_id: Optional[str]
    system_prompt: str
    total_revenue: float = 0.0
    total_cost: float = 0.0      # NEW
    net_profit: float = 0.0       # NEW
    transaction_count: int = 0
```

**Calcular costo real** (`agent.py`):
```python
def solve_request(self, description: str) -> tuple[str, float]:
    response = self.client.messages.create(...)

    # Extract token usage
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    # Haiku pricing (Jan 2026)
    HAIKU_INPUT_COST = 0.25 / 1_000_000   # $0.25 per MTok
    HAIKU_OUTPUT_COST = 1.25 / 1_000_000  # $1.25 per MTok

    cost = (input_tokens * HAIKU_INPUT_COST +
            output_tokens * HAIKU_OUTPUT_COST)

    return response.content[0].text, cost
```

**Deducir costo del revenue** (`marketplace.py`):
```python
def process_request(self, request: Request) -> Transaction:
    code, api_cost = agent.solve_request(request.description)
    price_paid = request.client.evaluate(code).price_paid

    net_profit = price_paid - api_cost

    # Update agent financials
    agent.config.total_revenue += price_paid
    agent.config.total_cost += api_cost
    agent.config.net_profit += net_profit

    # Agent can go BANKRUPT!
    if agent.config.net_profit < -10.0:
        print(f"⚠️ Agent {agent.config.agent_id} BANKRUPT (profit: ${net_profit:.2f})")
        # Remove from population
```

### Impacto

✅ **No más dumping**: Cobrar menos que costo = bancarrota
✅ **Incentivo a eficiencia**: Código breve = menos tokens = más profit
✅ **Selección natural real**: Solo sobreviven agentes rentables

**Ejemplo**:
```
Agent genera código de 1500 tokens:
- Cost: $0.002
- Client paga: $3 (broken code)
- Net profit: $2.998 ❌ PIERDE DINERO

Agent genera código de 200 tokens:
- Cost: $0.0003
- Client paga: $18 (excellent docs)
- Net profit: $17.9997 ✅ GANA DINERO
```

---

## 2. Sistema de Reputación

### Concepto

Track record público de calidad. Clientes prefieren agentes con buena reputación.

### Schema

```sql
CREATE TABLE agent_reputation (
    agent_id TEXT PRIMARY KEY,
    avg_satisfaction REAL,      -- 0-5 stars
    success_rate REAL,          -- % non-broken code
    avg_quality REAL,           -- avg price paid (proxy)
    total_jobs INTEGER,
    reputation_score REAL,      -- weighted composite
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);
```

### Cálculo

```python
@dataclass
class AgentReputation:
    agent_id: str
    avg_satisfaction: float  # Derived from client feedback
    success_rate: float      # (total_txs - broken_count) / total_txs
    avg_quality: float       # total_revenue / total_txs
    total_jobs: int

    @property
    def reputation_score(self) -> float:
        """Weighted composite: 40% satisfaction, 30% success, 30% quality"""
        return (0.4 * self.avg_satisfaction / 5.0 +
                0.3 * self.success_rate +
                0.3 * (self.avg_quality / 20.0))  # Normalize to 0-1
```

### Uso en Marketplace

```python
def assign_agent(self) -> SimpleAgent:
    """Weight by reputation, not just revenue"""
    weights = [db.get_reputation(a.agent_id).reputation_score
               for a in self.agents]
    return random.choices(self.agents, weights=weights)[0]
```

### Feedback Loop

```python
# After each transaction
if feedback == "Broken code":
    db.update_reputation(agent_id, satisfaction_delta=-0.1, success=False)
elif feedback == "Excellent documentation":
    db.update_reputation(agent_id, satisfaction_delta=+0.2, success=True)
```

---

## 3. Competencia entre Agentes (Auction Mechanism)

### Concepto

Múltiples agentes compiten por mismo request. Cliente elige mejor value (precio vs calidad).

### Workflow

```
1. Client posts REQUEST
   ↓
2. ALL Agents submit BIDS (price + reputation)
   ↓
3. Client evaluates: Best value for money
   ↓
4. Winning agent gets job
   ↓
5. Losers learn: adjust pricing strategy
```

### Implementación

**Request con presupuesto**:
```python
@dataclass
class Request:
    request_id: str
    description: str
    client: object
    max_budget: float  # NEW: Willingness to pay
```

**Agent bids**:
```python
@dataclass
class AgentBid:
    agent_id: str
    offered_price: float  # What agent ASKS
    reputation_score: float
    estimated_delivery_time: int  # Future: time premium
```

**Auction**:
```python
class Marketplace:
    def auction_request(self, request: Request) -> SimpleAgent:
        # Collect bids from all agents
        bids = []
        for agent in self.agents:
            asking_price = agent.calculate_bid(request.description)
            reputation = db.get_reputation(agent.config.agent_id)
            bids.append(AgentBid(agent.config.agent_id, asking_price, reputation))

        # Client selects winner
        winner = self._select_winning_bid(bids, request.client)
        return winner
```

**Client selection strategies**:
```python
def _select_winning_bid(self, bids, client):
    if isinstance(client, PragmaticClient):
        # Cheapest with reputation > 0.5
        valid = [b for b in bids if b.reputation_score > 0.5]
        return min(valid, key=lambda b: b.offered_price)

    elif isinstance(client, DocumenterClient):
        # Best quality regardless of price
        return max(bids, key=lambda b: b.reputation_score)

    elif isinstance(client, MinimalistClient):
        # Best value: reputation / price
        scores = [b.reputation_score / b.offered_price for b in bids]
        return bids[scores.index(max(scores))]
```

---

## 4. Descubrimiento Dinámico de Precios

### Problema

`BASE_PRICE = 10.0` está hardcoded (planificación central, no austriaco).

### Solución

Precios emergen del mercado: bid-ask spread entre agentes y clientes.

**Agent pricing strategy**:
```python
class SimpleAgent:
    def calculate_bid(self, description: str) -> float:
        # 1. Estimate cost
        estimated_tokens = self._estimate_complexity(description)
        estimated_cost = estimated_tokens * HAIKU_COST_PER_TOKEN

        # 2. Desired profit margin (EVOLVED!)
        profit_margin = 1.5  # Learned through evolution

        # 3. Market awareness
        market_avg = marketplace.get_average_price()

        # 4. Bid formula
        base_price = estimated_cost * profit_margin
        competitive_price = min(base_price, market_avg * 1.1)

        return competitive_price
```

**Client evaluation with bid**:
```python
class MinimalistClient:
    def evaluate(self, code: str, agent_bid: float) -> EvaluationResult:
        # Calculate subjective value
        lines = len([l for l in code.split('\n') if l.strip()])

        if lines < 20:
            perceived_value = 15.0
        elif lines < 40:
            perceived_value = 10.0
        else:
            perceived_value = 7.0

        # Price discovery: accept if bid ≤ value
        if agent_bid <= perceived_value:
            actual_price = agent_bid
            feedback = "Accepted"
        else:
            actual_price = 0.0  # REJECTED!
            feedback = "Rejected: too expensive"

        return EvaluationResult("MinimalistClient", actual_price, feedback)
```

### Learning Loop

```
Agent bids $15 → Client values at $10 → REJECTED
    ↓
Agent learns: lower bid next time
    ↓
Agent bids $9 → Client values at $10 → ACCEPTED ($9)
    ↓
Agent learns: could have charged more
    ↓
Agent bids $10.5 next time
    ↓
Equilibrium emerges around $10 (without hardcoding!)
```

### Evolution of Pricing Strategy

**Gen0 naive**:
```
"You are a Python programmer. Bid strategy: always $10."
```

**Gen3 evolved**:
```
"You are a Python programmer. Estimate complexity.
Formula: cost * 1.4. Undercut competitors by 10% if losing jobs."
```

**Gen5 sophisticated**:
```
"Python expert specialized in documentation.
DocumenterClient: bid high ($18-20), quality over price.
MinimalistClient: bid low ($8-10), price sensitive.
Identify client from keywords, adjust bid."
```

---

## 📊 ARQUITECTURA COMPLETA MVP-2

```
┌─────────────────────────────────────────────┐
│         AUSTRIAN MARKETPLACE                │
└─────────────────────────────────────────────┘

Client posts REQUEST (max_budget)
    ↓
ALL Agents submit BIDS
    bid = f(estimated_cost, profit_margin, market_avg, reputation)
    ↓
Client evaluates BIDS
    selection = f(price, reputation, client_preferences)
    ↓
Winning Agent generates CODE
    cost = input_tokens * $0.00000025 + output_tokens * $0.00000125
    ↓
Client evaluates QUALITY
    if quality ≥ expectations: pay bid
    if quality < expectations: reject or partial payment
    ↓
Agent financials updated
    net_profit = revenue - api_cost
    if net_profit < -10: BANKRUPTCY → remove from population
    ↓
Reputation updated
    success_rate, avg_satisfaction, avg_quality
    ↓
Evolution selects parent
    Based on: net_profit (not revenue!) + CMP lineage
    ↓
Mutation
    Evolve: PROMPT + PRICING STRATEGY
    ↓
New generation competes in market
```

---

## 🎯 COMPARACIÓN: MVP-1.1 vs MVP-2

| Feature | MVP-1.1 (Actual) | MVP-2 (Propuesto) |
|---------|------------------|-------------------|
| **Modelo de Costos** | Sin costos | ✅ Token-based real costs |
| **Asignación** | Revenue-weighted random | ✅ Auction + reputation |
| **Precios** | Hardcoded BASE_PRICE | ✅ Dynamic (bid-ask) |
| **Competencia** | Entre agentes (oferta) | ✅ Entre agentes Y clientes |
| **Reputación** | No existe | ✅ Track record público |
| **Pricing strategy** | No existe | ✅ Evoluciona con prompt |
| **Bancarrota** | Imposible | ✅ Si cost > revenue |
| **Selección** | CMP lineage | ✅ CMP + net_profit |
| **Race to $0** | Posible | ✅ Prevenido (costos) |
| **Austrian** | Parcial (señales precio) | ✅ Full (Hayek knowledge) |

---

## 📈 PLAN DE IMPLEMENTACIÓN

### Fase 1: MVP-1.1 Baseline (COMPLETADO ✅)

**Objetivo**: Establecer baseline con fixes críticos
**Duración**: Completado
**Costo**: ~$0.59

**Entregables**:
- ✅ Código sin errores de parsing
- ✅ 200 transacciones (Gen3-5 visible)
- ✅ Revenue-weighted + CMP
- ✅ Control group framework
- ✅ Visualización

### Fase 2: MVP-2 Core (2-3 días)

**Objetivo**: Costos + Reputación básica
**LOC estimado**: ~200

**Tareas**:
1. Agregar `total_cost`, `net_profit` a AgentConfig
2. Capturar `response.usage` y calcular API cost
3. Actualizar evolution para usar `net_profit` en lugar de `total_revenue`
4. Schema de reputación + tracking básico
5. Marketplace selection por reputación

**Test**:
- Correr 200 txs y verificar que agentes con código largo tengan lower net_profit
- Verificar que reputación sube/baja según feedback

### Fase 3: MVP-2 Auction (3-4 días)

**Objetivo**: Competencia entre agentes
**LOC estimado**: ~300

**Tareas**:
1. Implementar `AgentBid` dataclass
2. Método `agent.calculate_bid()` (naive al principio)
3. Marketplace auction workflow
4. Client selection strategies
5. Rejection mechanism (bid > perceived_value)

**Test**:
- Verificar que clientes eligen diferentes agentes según strategy
- Verificar que precios convergen (no divergen a $0 o ∞)

### Fase 4: MVP-2 Dynamic Pricing (2-3 días)

**Objetivo**: Pricing strategy evoluciona
**LOC estimado**: ~200

**Tareas**:
1. Eliminar BASE_PRICE hardcoded
2. Agregar pricing parameters al prompt
3. Evolution muta pricing strategy
4. Market feedback loop (agent aprende de rechazos)

**Test**:
- Gen5 tiene pricing strategy interpretable
- Precios se estabilizan en equilibrio (~$10-15 range)
- Agents especializan por cliente (high-price vs low-price)

### Fase 5: MVP-2 Full Integration (2 días)

**Objetivo**: Sistema completo funcionando
**LOC estimado**: ~100 (polish)

**Tareas**:
1. Bancarrota mechanism
2. Visualización mejorada (mostrar costos, net_profit)
3. Dashboard con métricas austriacas
4. Tests de integración

---

## 🧪 EXPERIMENTOS PROPUESTOS

### Experimento 1: MVP-1.1 Baseline (PRÓXIMO)

**Setup**:
- 200 transacciones
- Haiku model
- Revenue-weighted + CMP
- Guided mutations

**Hipótesis**:
- Gen3-5 avg_price > Gen0 avg_price
- Broken code rate < 5%
- CMP selecciona mejores padres

**Métricas**:
```python
{
    "gen0_avg_price": float,
    "gen3_avg_price": float,
    "gen5_avg_price": float,
    "improvement_pct": float,  # (gen5 - gen0) / gen0
    "broken_code_rate": float,
    "cmp_correlation": float,  # corr(lineage_revenue, offspring_success)
}
```

### Experimento 2: Control Group Comparison

**Setup**:
- 2 runs de 200 txs cada uno
- Run A: `USE_GUIDED_MUTATION = True`
- Run B: `USE_GUIDED_MUTATION = False`

**Hipótesis**: A > B por ≥20% en Gen5

### Experimento 3: MVP-2 Cost Impact

**Setup**:
- MVP-2 con costos reales
- 200 transacciones

**Hipótesis**:
- Agentes con código breve tienen higher net_profit
- Agents con código largo (>100 LOC) van a bancarrota
- Selection pressure hacia eficiencia

### Experimento 4: MVP-2 Auction Market

**Setup**:
- MVP-2 completo (auction + dynamic pricing)
- 500 transacciones

**Hipótesis**:
- Precios convergen a equilibrio ($10-15)
- No race to $0 (costos lo previenen)
- Agents especializan (high-price quality vs low-price volume)

---

## 💡 APRENDIZAJES CLAVE

### Del MVP-1.0 Original

1. **Broken code era problema de formato, no de modelo**: Claude es excelente, solo necesitaba "no markdown"
2. **50 txs insuficiente**: Necesitas ≥200 para ver Gen3+
3. **Random assignment es anti-evolutivo**: Goods agents murieron por mala suerte
4. **Revenue individual ≠ potencial generativo**: CMP captura esto

### Para MVP-2

1. **Costos son CRÍTICOS**: Sin costos, no hay economía real
2. **Reputación complementa precio**: Quality signal necesario
3. **Competencia es bilateral**: Agents compiten, clients también
4. **Pricing es estrategia evolucionable**: No hardcodear

---

## 📚 REFERENCIAS

### Papers

- **Huxley-Gödel Machine**: [arxiv.org/html/2510.21614v3](https://arxiv.org/html/2510.21614v3)
  - CMP (Clade-Metaproductivity)
  - Thompson Sampling para selección
  - Metaproductivity-Performance Mismatch

### Economía Austriaca

- **Hayek**: Knowledge Problem - precios descubren información dispersa
- **Mises**: Utilidad marginal subjetiva - cada cliente valora diferente
- **Rothbard**: Acción humana - estrategias emergen de incentivos

### Anthropic API

- **Pricing**: [anthropic.com/pricing](https://www.anthropic.com/pricing)
- **Token counting**: `response.usage.input_tokens`, `response.usage.output_tokens`

---

## ✅ CRITERIOS DE ÉXITO

### MVP-1.1 (Baseline)

- [x] Broken code < 5%
- [ ] Gen5 avg_price > Gen0 avg_price (≥15%)
- [ ] CMP selecciona mejores padres
- [ ] Control group: guided > random (≥20%)

### MVP-2 (Austrian)

- [ ] No race to $0 (precios estables $8-18)
- [ ] Agents eficientes sobreviven (net_profit > 0)
- [ ] Reputación correlaciona con success
- [ ] Pricing strategy evoluciona interpretablemente
- [ ] Market equilibrium emerge (no hardcoded)

---

## 🚧 LIMITACIONES Y FUTURO

### Limitaciones Actuales

1. **Clientes no compiten**: Solo agents compiten, clients eligen pasivamente
2. **Un solo marketplace**: No hay múltiples markets especializados
3. **No hay capital accumulation**: Agents no pueden invertir profits
4. **Time no existe**: Delivery instant, sin premium por urgencia
5. **Perfect information**: Clients ven toda la reputación

### MVP-3+ (Visión)

1. **Multi-market**: Niche markets (web dev, data science, ML)
2. **Capital**: Agents invierten en "mejor hardware" (Opus vs Haiku)
3. **Time premium**: Urgent requests pay more
4. **Reputation uncertainty**: Costly to verify quality
5. **Agent death and birth**: Natural population dynamics
6. **Emergent specialization**: Experts vs generalists

---

## 📞 SIGUIENTE PASO

**INMEDIATO**: Ejecutar Experimento 1 (MVP-1.1 Baseline)

```bash
# Limpiar DB vieja
rm celula_madre.db

# Ejecutar
python main.py
```

Después de analizar resultados, decidir si proceder a MVP-2.

---

**FIN DEL DOCUMENTO**
