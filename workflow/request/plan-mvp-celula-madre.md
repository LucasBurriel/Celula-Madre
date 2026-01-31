# Plan MVP: Célula Madre - Price-Driven Code Evolution

## 0. Instrucciones de Ejecución (OBLIGATORIO)

**ANTES de comenzar a ejecutar este plan**, leer completamente `workflow/commands/execute-plan.md`.

---

## 1. Resumen Ejecutivo MVP

### Objetivo
Validar la hipótesis: **¿Pueden señales de precio guiar la evolución de agentes mejor que mutación random?**

### Alcance MVP (Ultra-Simple)

**Incluye**:
- ✅ Agente simple: Claude Sonnet 4.5 con **prompt variable** (única mutación)
- ✅ Marketplace simulado: 3-4 clientes bot con preferencias diferentes
- ✅ Evolución básica: Greedy (top performer) + 20% exploración random
- ✅ Población pequeña: 3-5 agentes máximo
- ✅ Persistencia: SQLite (simple, archivo local)
- ✅ Métricas: Revenue por agente, evolución de prompts

**NO incluye** (dejamos para MVP-2):
- ❌ Clade-Metaproductivity (CMP) - solo greedy por ahora
- ❌ Múltiples modelos LLM (solo Claude Sonnet)
- ❌ AP2 protocolo completo (mock simple de pricing)
- ❌ MCP servers variables
- ❌ Docker sandbox
- ❌ Web UI (solo CLI + logs)

### Métricas de Éxito

Después de **50-100 transacciones simuladas**:
1. ✅ Revenue promedio aumenta entre generaciones (Gen 5 > Gen 0)
2. ✅ Hay variación entre agentes (algunos ganan más que otros)
3. ✅ Prompts evolucionan de forma interpretable
4. ✅ Evolución guiada > mutación random (experimento de control)

### Tamaño del Código
**~400-500 LOC total** (excluyendo tests)

---

## 2. Arquitectura MVP

```
┌────────────────────────────────────────────────┐
│          MVP: Price-Driven Evolution           │
└────────────────────────────────────────────────┘

┌─────────────────┐         ┌──────────────────┐
│  AGENT POPULATION│◄────────┤   MARKETPLACE    │
│   (3-5 agents)  │ prices  │  (Bot Clients)   │
│                 │────────►│                  │
│ • Agent_0       │ solution│ • MinimalistBot  │
│ • Agent_1       │         │ • DocumenterBot  │
│ • Agent_2       │         │ • TesterBot      │
└────────┬────────┘         │ • PragmaticBot   │
         │                  └──────────────────┘
         │ mutation
         │ (prompt evolution)
         │
┌────────▼─────────────────┐
│  EVOLUTIONARY ENGINE     │
│  • Greedy selection      │
│  • +20% random explore   │
│  • Prompt mutation       │
└────────┬─────────────────┘
         │
         │ persistence
┌────────▼────────┐
│   SQLite DB     │
│ • agents        │
│ • transactions  │
└─────────────────┘
```

---

## 3. Componentes MVP (Simplificados)

### Componente 1: SimpleAgent

**Responsabilidades**: Generar código usando Claude con prompt variable

**Dependencias**:
- `anthropic` SDK
- Pydantic

**Código**:
```python
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Optional

class AgentConfig(BaseModel):
    """Configuración del agente - Solo prompt es mutable en MVP"""
    agent_id: str
    generation: int
    parent_id: Optional[str] = None
    system_prompt: str
    total_revenue: float = 0.0
    transaction_count: int = 0

class SimpleAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = Anthropic()

    async def solve_request(self, description: str) -> str:
        """Genera código basándose en descripción del cliente"""
        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            system=self.config.system_prompt,
            messages=[{
                "role": "user",
                "content": f"Generate Python code for: {description}\n\nInclude tests and docstrings."
            }],
            max_tokens=2048
        )
        return response.content[0].text
```

**Criterios de aceptación**:
- [ ] Agent genera código funcional desde descripción simple
- [ ] Diferentes prompts resultan en diferentes estilos de código
- [ ] Config es serializable a DB

**Tests**:
- `test_agent_generates_code`: Input: "sum function", Output: código válido
- `test_different_prompts_different_output`: 2 agents con prompts distintos → outputs mediblemente diferentes

**LOC esperado**: ~40-50

---

### Componente 2: Bot Clients (Evaluadores)

**Responsabilidades**: Simular clientes con diferentes preferencias de valor

**Código**:
```python
import ast
from dataclasses import dataclass

@dataclass
class EvaluationResult:
    client_name: str
    price_paid: float
    feedback: str

class MinimalistClient:
    """Paga más por código conciso"""
    BASE_PRICE = 10.0

    def evaluate(self, code: str) -> EvaluationResult:
        lines = len([l for l in code.split('\n') if l.strip()])

        if lines < 20:
            price = self.BASE_PRICE * 1.5  # $15
            feedback = "Excellent brevity"
        elif lines < 40:
            price = self.BASE_PRICE  # $10
            feedback = "Good length"
        else:
            price = self.BASE_PRICE * 0.7  # $7
            feedback = "Too verbose"

        return EvaluationResult("MinimalistClient", price, feedback)

class DocumenterClient:
    """Paga más por buena documentación"""
    BASE_PRICE = 10.0

    def evaluate(self, code: str) -> EvaluationResult:
        has_docstring = '"""' in code or "'''" in code
        has_comments = '#' in code

        if has_docstring and has_comments:
            price = self.BASE_PRICE * 1.8  # $18
            feedback = "Excellent documentation"
        elif has_docstring or has_comments:
            price = self.BASE_PRICE * 1.2  # $12
            feedback = "Good documentation"
        else:
            price = self.BASE_PRICE * 0.6  # $6
            feedback = "Poor documentation"

        return EvaluationResult("DocumenterClient", price, feedback)

class TesterClient:
    """Paga más por tests"""
    BASE_PRICE = 10.0

    def evaluate(self, code: str) -> EvaluationResult:
        has_test = 'def test_' in code or 'assert' in code
        test_count = code.count('def test_')

        if test_count >= 3:
            price = self.BASE_PRICE * 2.0  # $20
            feedback = "Comprehensive tests"
        elif has_test:
            price = self.BASE_PRICE * 1.3  # $13
            feedback = "Basic tests included"
        else:
            price = self.BASE_PRICE * 0.5  # $5
            feedback = "No tests"

        return EvaluationResult("TesterClient", price, feedback)

class PragmaticClient:
    """Paga por simplicidad y funcionamiento"""
    BASE_PRICE = 10.0

    def evaluate(self, code: str) -> EvaluationResult:
        # Validación básica: código parseable
        try:
            ast.parse(code)
            parseable = True
        except:
            parseable = False

        lines = len([l for l in code.split('\n') if l.strip()])

        if parseable and lines < 30:
            price = self.BASE_PRICE * 1.4  # $14
            feedback = "Simple and works"
        elif parseable:
            price = self.BASE_PRICE  # $10
            feedback = "Works"
        else:
            price = self.BASE_PRICE * 0.3  # $3
            feedback = "Broken code"

        return EvaluationResult("PragmaticClient", price, feedback)
```

**Criterios de aceptación**:
- [ ] Cada bot tiene criterios de evaluación distintos y automáticos
- [ ] Mismo código evaluado por 4 bots → 4 precios diferentes
- [ ] Evaluación determinística (mismo código → mismo precio)

**Tests**:
- `test_minimalist_prefers_short_code`: Código de 15 LOC → precio > código 50 LOC
- `test_documenter_prefers_docstrings`: Código con docstrings → precio > sin docstrings
- `test_tester_prefers_tests`: Código con 3 tests → precio > sin tests

**LOC esperado**: ~80-100

---

### Componente 3: Marketplace

**Responsabilidades**: Generar requests, asignar a agentes, registrar transacciones

**Código**:
```python
import random
from typing import List
from dataclasses import dataclass

@dataclass
class Request:
    request_id: str
    description: str
    client: object  # MinimalistClient, etc.

@dataclass
class Transaction:
    request_id: str
    agent_id: str
    code_generated: str
    price_paid: float
    client_name: str
    feedback: str

class Marketplace:
    def __init__(self, agents: List[SimpleAgent]):
        self.agents = agents
        self.clients = [
            MinimalistClient(),
            DocumenterClient(),
            TesterClient(),
            PragmaticClient()
        ]
        self.transactions = []

    def generate_request(self) -> Request:
        """Genera request random con cliente random"""
        descriptions = [
            "Function to calculate factorial",
            "Class to parse CSV files",
            "Function to validate email addresses",
            "Function to merge two sorted lists",
            "Class for a simple stack data structure"
        ]

        return Request(
            request_id=f"req_{len(self.transactions)}",
            description=random.choice(descriptions),
            client=random.choice(self.clients)
        )

    def assign_agent(self) -> SimpleAgent:
        """Asigna agente random (o revenue-weighted en versión avanzada)"""
        # MVP: Random assignment
        # TODO: Revenue-weighted selection
        return random.choice(self.agents)

    async def process_request(self, request: Request) -> Transaction:
        """Procesa request completo: asignar → generar → evaluar → pagar"""
        agent = self.assign_agent()

        # Generar solución
        code = await agent.solve_request(request.description)

        # Evaluar con cliente
        evaluation = request.client.evaluate(code)

        # Crear transacción
        transaction = Transaction(
            request_id=request.request_id,
            agent_id=agent.config.agent_id,
            code_generated=code,
            price_paid=evaluation.price_paid,
            client_name=evaluation.client_name,
            feedback=evaluation.feedback
        )

        # Actualizar revenue del agente
        agent.config.total_revenue += evaluation.price_paid
        agent.config.transaction_count += 1

        self.transactions.append(transaction)
        return transaction
```

**Criterios de aceptación**:
- [ ] Marketplace genera requests variados
- [ ] Asigna agentes (random en MVP)
- [ ] Registra transacciones completas con revenue

**Tests**:
- `test_generate_request_has_client`: Request generado → tiene cliente asignado
- `test_process_request_updates_revenue`: Después de transacción → agent.total_revenue actualizado
- `test_multiple_transactions_accumulate`: 3 transacciones → revenue acumulado correcto

**LOC esperado**: ~80-100

---

### Componente 4: EvolutionaryEngine

**Responsabilidades**: Seleccionar padres, mutar prompts, crear nuevas generaciones

**Código**:
```python
import random
from anthropic import Anthropic

class EvolutionaryEngine:
    def __init__(self):
        self.client = Anthropic()

    def select_parent(self, agents: List[SimpleAgent]) -> SimpleAgent:
        """
        Selección Greedy + Epsilon Random:
        - 80% probabilidad: Mejor agente por revenue
        - 20% probabilidad: Random (exploración)
        """
        if random.random() < 0.8:
            # Greedy: Mejor por revenue
            return max(agents, key=lambda a: a.config.total_revenue)
        else:
            # Exploración: Random
            return random.choice(agents)

    async def mutate_prompt(self, parent_prompt: str, performance_data: dict) -> str:
        """
        Usa Claude para generar prompt mejorado basándose en performance
        """
        mutation_instruction = f"""
You are optimizing a coding agent's system prompt based on market feedback.

Current prompt:
{parent_prompt}

Performance data:
- Total revenue: ${performance_data['total_revenue']:.2f}
- Transactions: {performance_data['transaction_count']}
- Average price: ${performance_data['avg_price']:.2f}

Client feedback samples:
{performance_data['feedback_samples']}

Generate an IMPROVED system prompt that might increase revenue.
Consider what clients valued (brevity, documentation, tests, simplicity).

Return ONLY the new prompt, no explanation.
"""

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": mutation_instruction}],
            max_tokens=512
        )

        return response.content[0].text.strip()

    async def evolve_generation(self, agents: List[SimpleAgent], db) -> SimpleAgent:
        """
        Crea nuevo agente variant:
        1. Selecciona padre (greedy + epsilon)
        2. Muta prompt del padre
        3. Crea nuevo agente
        """
        parent = self.select_parent(agents)

        # Obtener feedback de últimas transacciones del padre
        feedback = db.get_recent_feedback(parent.config.agent_id, limit=5)

        performance_data = {
            'total_revenue': parent.config.total_revenue,
            'transaction_count': parent.config.transaction_count,
            'avg_price': parent.config.total_revenue / max(1, parent.config.transaction_count),
            'feedback_samples': '\n'.join([f"- {f}" for f in feedback])
        }

        # Mutar prompt
        new_prompt = await self.mutate_prompt(parent.config.system_prompt, performance_data)

        # Crear nuevo agente
        new_config = AgentConfig(
            agent_id=f"agent_gen{parent.config.generation + 1}_{random.randint(1000, 9999)}",
            generation=parent.config.generation + 1,
            parent_id=parent.config.agent_id,
            system_prompt=new_prompt
        )

        new_agent = SimpleAgent(new_config)

        # Guardar en DB
        db.save_agent(new_config)

        return new_agent
```

**Criterios de aceptación**:
- [ ] Selecciona padre con 80% greedy, 20% random
- [ ] Genera prompt modificado usando Claude
- [ ] Nuevo agente tiene generation incrementado y parent_id correcto

**Tests**:
- `test_select_parent_greedy_bias`: 10 selecciones → agente top revenue seleccionado ≥7 veces
- `test_mutate_prompt_changes_text`: Prompt mutado ≠ prompt original
- `test_evolve_increments_generation`: Parent gen=2 → child gen=3

**LOC esperado**: ~60-80

---

### Componente 5: Persistence (SQLite)

**Responsabilidades**: Guardar agentes, transacciones, tracking de lineage

**Schema**:
```sql
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    parent_id TEXT,
    system_prompt TEXT NOT NULL,
    total_revenue REAL DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    code_generated TEXT NOT NULL,
    price_paid REAL NOT NULL,
    client_name TEXT NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX idx_agent_revenue ON agents(total_revenue DESC);
CREATE INDEX idx_transactions_agent ON transactions(agent_id);
```

**Código**:
```python
import sqlite3
from typing import List, Optional

class Database:
    def __init__(self, db_path: str = "celula_madre.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        with open('schema.sql', 'r') as f:
            self.conn.executescript(f.read())

    def save_agent(self, config: AgentConfig):
        self.conn.execute("""
            INSERT INTO agents (agent_id, generation, parent_id, system_prompt, total_revenue, transaction_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (config.agent_id, config.generation, config.parent_id, config.system_prompt,
              config.total_revenue, config.transaction_count))
        self.conn.commit()

    def update_agent_revenue(self, agent_id: str, revenue_delta: float):
        self.conn.execute("""
            UPDATE agents
            SET total_revenue = total_revenue + ?,
                transaction_count = transaction_count + 1
            WHERE agent_id = ?
        """, (revenue_delta, agent_id))
        self.conn.commit()

    def save_transaction(self, tx: Transaction):
        self.conn.execute("""
            INSERT INTO transactions (request_id, agent_id, code_generated, price_paid, client_name, feedback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tx.request_id, tx.agent_id, tx.code_generated, tx.price_paid, tx.client_name, tx.feedback))
        self.conn.commit()

    def get_all_agents(self) -> List[AgentConfig]:
        rows = self.conn.execute("SELECT * FROM agents ORDER BY total_revenue DESC").fetchall()
        return [AgentConfig(**dict(row)) for row in rows]

    def get_recent_feedback(self, agent_id: str, limit: int = 5) -> List[str]:
        rows = self.conn.execute("""
            SELECT feedback FROM transactions
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, limit)).fetchall()
        return [row['feedback'] for row in rows]
```

**Criterios de aceptación**:
- [ ] DB persiste agentes con lineage (parent_id)
- [ ] Actualiza revenue atómicamente
- [ ] Retorna agentes ordenados por revenue

**Tests**:
- `test_save_and_load_agent`: Guardar agent → cargar → config idéntico
- `test_update_revenue_atomic`: Update concurrente → sin race conditions
- `test_get_recent_feedback`: 10 txs guardadas → últimas 5 retornadas

**LOC esperado**: ~80-100

---

## 4. Script Principal (Orquestación)

```python
# main.py
import asyncio
import random

async def main():
    # Inicializar
    db = Database()

    # Crear población inicial (3 agentes con prompts diferentes)
    initial_prompts = [
        "You are a helpful Python coding assistant. Generate clean, working code.",
        "You are a minimalist coder. Prefer brevity and simplicity.",
        "You are a documentation-focused developer. Always include comprehensive docstrings and comments."
    ]

    agents = []
    for i, prompt in enumerate(initial_prompts):
        config = AgentConfig(
            agent_id=f"agent_gen0_{i}",
            generation=0,
            system_prompt=prompt
        )
        agent = SimpleAgent(config)
        agents.append(agent)
        db.save_agent(config)

    # Inicializar marketplace y evolution
    marketplace = Marketplace(agents)
    evolution_engine = EvolutionaryEngine()

    # Simular 50 transacciones
    for i in range(50):
        request = marketplace.generate_request()
        transaction = await marketplace.process_request(request)

        db.save_transaction(transaction)
        db.update_agent_revenue(transaction.agent_id, transaction.price_paid)

        print(f"[Tx {i+1}] Agent: {transaction.agent_id}, Price: ${transaction.price_paid:.2f}, Client: {transaction.client_name}")

        # Evolucionar cada 10 transacciones
        if (i + 1) % 10 == 0:
            new_agent = await evolution_engine.evolve_generation(agents, db)
            agents.append(new_agent)
            marketplace.agents = agents  # Actualizar marketplace

            print(f"\n🧬 EVOLUTION: New agent created!")
            print(f"   ID: {new_agent.config.agent_id}")
            print(f"   Generation: {new_agent.config.generation}")
            print(f"   Parent: {new_agent.config.parent_id}")
            print(f"   Prompt (first 100 chars): {new_agent.config.system_prompt[:100]}...\n")

    # Resultados finales
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    all_agents = db.get_all_agents()
    for agent in all_agents:
        avg_price = agent.total_revenue / max(1, agent.transaction_count)
        print(f"\nAgent: {agent.agent_id}")
        print(f"  Generation: {agent.generation}")
        print(f"  Total Revenue: ${agent.total_revenue:.2f}")
        print(f"  Transactions: {agent.transaction_count}")
        print(f"  Avg Price: ${avg_price:.2f}")
        print(f"  Prompt: {agent.system_prompt[:80]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

**LOC esperado**: ~80-100

---

## 5. Estructura de Archivos MVP

```
celula-madre-mvp/
├── src/
│   ├── agent.py          # SimpleAgent (~50 LOC)
│   ├── clients.py        # Bot clients (~100 LOC)
│   ├── marketplace.py    # Marketplace (~100 LOC)
│   ├── evolution.py      # EvolutionaryEngine (~80 LOC)
│   └── database.py       # Database (~100 LOC)
├── tests/
│   ├── test_agent.py
│   ├── test_clients.py
│   ├── test_marketplace.py
│   ├── test_evolution.py
│   └── test_database.py
├── schema.sql            # DB schema
├── main.py               # Script principal (~100 LOC)
├── requirements.txt
├── .env
└── README.md
```

**Total: ~530 LOC (excluyendo tests)**

---

## 6. Dependencias

**requirements.txt**:
```txt
anthropic==0.40.0
pydantic==2.10.5
python-dotenv==1.0.1

# Testing
pytest==8.3.4
pytest-asyncio==0.25.2
```

**.env**:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 7. Orden de Implementación

**Día 1**:
1. Database (schema + basic CRUD) → ~2h
2. SimpleAgent (config + solve_request) → ~1h

**Día 2**:
3. Bot Clients (4 evaluators) → ~2h
4. Marketplace (generate + process request) → ~2h

**Día 3**:
5. EvolutionaryEngine (selection + mutation) → ~2h
6. Main script (orchestration) → ~1h

**Día 4**:
7. Testing (unit tests) → ~3h
8. Experimento inicial (50 txs) → ~1h

**Total: ~14-16 horas de implementación**

---

## 8. Experimento de Validación

### Hipótesis a Probar

**H1**: Revenue promedio aumenta con generaciones
- Medir: `avg_price(generation=0)` vs `avg_price(generation≥3)`
- Éxito: Incremento ≥15%

**H2**: Evolución guiada > Random
- Control: Población con mutación random de prompts (no guiada por Claude)
- Experimental: Población con mutación guiada por performance
- Medir: Revenue total después de 50 txs
- Éxito: Experimental > Control por ≥20%

**H3**: Emerge especialización
- Analizar: Prompts de generación 5
- Verificar: ¿Mencionan conceptos específicos? (brevity, documentation, tests)
- Éxito: Al menos 1 agente claramente especializado

### Métricas de Output

Después de ejecutar `python main.py`:

```
Generation 0 (baseline):
- Avg revenue: $10.20
- Best prompt: "helpful Python coding assistant"

Generation 3:
- Avg revenue: $12.50 (+22.5% ✅)
- Best prompt: "minimalist Python developer focusing on clean, brief solutions with essential tests"

Generation 5:
- Avg revenue: $14.10 (+38.2% ✅)
- Best prompt: "Python expert who writes comprehensive docstrings and includes edge-case tests for all functions"

✅ Hypothesis validated: Price signals guide evolution
✅ Specialization emerged: Agents learned to optimize for specific client types
```

---

## 9. Próximos Pasos (Post-MVP)

Si MVP funciona (hipótesis validadas):

**MVP-2** (~2 semanas):
- ✅ Clade-Metaproductivity (CMP) en lugar de greedy
- ✅ Revenue-weighted agent assignment
- ✅ Más clientes bot (6-8 con preferencias complejas)

**MVP-3** (~3 semanas):
- ✅ Múltiples modelos (Opus, Sonnet, Haiku) - agente elige
- ✅ PostgreSQL en lugar de SQLite
- ✅ Web UI básico (dashboard de métricas)

**Visión completa "Célula Madre"** (~2-3 meses):
- ✅ MCP servers variables
- ✅ Tools configurables
- ✅ Arquitectura modificable
- ✅ AP2 protocolo real
- ✅ Marketplace público

---

## 10. Validaciones Finales del Plan MVP

- [x] Plan enfocado en validar hipótesis core
- [x] Scope ultra-simple (solo prompt mutation)
- [x] ~400-500 LOC total
- [x] Clientes bot con evaluación automática
- [x] Sin hardcodear (Claude muta sus propios prompts)
- [x] Greedy + epsilon exploration (no CMP todavía)
- [x] Implementable en 3-4 días
- [x] Métricas claras de éxito
- [x] Escalable hacia visión completa

**Listo para ejecutar** ✅
