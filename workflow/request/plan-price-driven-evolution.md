# Plan de Implementación: Price-Driven Code Evolution System

## 0. Instrucciones de Ejecución (OBLIGATORIO)

**ANTES de comenzar a ejecutar este plan**, es obligatorio leer completamente el documento `workflow/commands/execute-plan.md` que contiene las instrucciones detalladas sobre cómo ejecutar planes de implementación. Este paso es crítico para asegurar una ejecución correcta y alineada con los principios establecidos.

---

## 1. Resumen Ejecutivo

### Objetivo del Proyecto
Crear un sistema de **evolución de agentes de código guiada por precios de mercado**, que combine:
- **Darwin Gödel Machine (DGM)**: Código auto-evolutivo con población de agentes variantes
- **Agent Payments Protocol (AP2)**: Protocolo para que agentes participen en comercio real
- **Teoría Hayekiana**: Precios como señal descentralizada de conocimiento disperso
- **LangGraph**: Framework para construir agentes stateful con memoria y persistencia

**Visión Central**: En lugar de optimizar agentes usando benchmarks artificiales (como SWE-bench), usar **señales de precio del mercado real** como indicador de value/utilidad. Los agentes que entregan mayor valor cobran precios más altos, y esta señal guía su evolución.

### Alcance

**Incluye**:
- Sistema de población de agentes coding variants (estilo DGM)
- Integración con AP2 para comercio real de soluciones de código
- Mecanismo de selección evolutiva basada en revenue/pricing
- LangGraph agents con memoria y estado persistente
- Marketplace simulado interno (MVP) para validación

**No incluye** (Fase 1 - MVP):
- Integración completa con payment processors reales
- Escalabilidad multi-tenant
- UI/UX complejo (CLI primero)
- Optimizaciones de performance avanzadas

### Tecnologías Principales

**Core Stack**:
- **Python 3.10+**: Lenguaje principal
- **Anthropic API (Claude)**: Motor de generación de código (Claude Sonnet 4.5 con extended thinking)
- **Pydantic v2**: Validación de datos y modelos (usado por AP2)
- **PostgreSQL**: Base de datos para persistencia (agentes, transacciones, revenue)
- **FastAPI**: REST API para marketplace

**Librerías Específicas**:
- **AP2 types** (`ap2.types`): PaymentRequest, CartMandate, PaymentResponse
- **anthropic**: SDK para Anthropic API (Claude Code)
- **asyncpg**: Async PostgreSQL client
- **Docker**: (Opcional) Ejecución aislada de código generado
- **pytest**: Testing framework

---

## 2. Arquitectura General

### 2.1 Diagrama Conceptual de Alto Nivel

```
┌──────────────────────────────────────────────────────────────┐
│                   PRICE-DRIVEN EVOLUTION SYSTEM              │
└──────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
   ┌────────▼─────────┐              ┌─────────▼──────────┐
   │  AGENT POPULATION│              │   MARKETPLACE      │
   │   (DGM-inspired) │              │  (AP2-integrated)  │
   │                  │              │                    │
   │ • Variant_1      │◄────prices──►│ • Requests for    │
   │ • Variant_2      │              │   code solutions  │
   │ • Variant_3      │              │ • Payment flow    │
   │ • Variant_N      │              │ • Price signals   │
   └──────┬───────────┘              └──────┬─────────────┘
          │                                 │
          │ self-improvement                │ revenue data
          │ (modify prompts/code)           │
          │                                 │
   ┌──────▼──────────────────────────────────▼─────────┐
   │          EVOLUTIONARY ENGINE                      │
   │  • Selection based on revenue/pricing             │
   │  • Parent selection (score_prop from DGM)         │
   │  • Mutation: prompt changes, tool modifications   │
   │  • Persistence: PostgreSQL checkpointer           │
   └────────────────┬──────────────────────────────────┘
                    │
                    │ metadata (generations, lineage)
                    │
            ┌───────▼─────────┐
            │   PERSISTENCE   │
            │  • Agent states │
            │  • Transactions │
            │  • Performance  │
            └─────────────────┘
```

### 2.2 Flujo Principal del Sistema

**1. Inicialización**:
   - Crear agente inicial (`initial_variant`) con prompt base para coding
   - Registrar en marketplace interno
   - Archivo (población) = [`initial_variant`]

**2. Recepción de Request**:
   - Cliente (simulado o real) solicita solución de código vía AP2
   - `PaymentRequest` con precio máximo dispuesto a pagar
   - `IntentMandate` en lenguaje natural (ej: "function que parsea CSV a JSON")

**3. Selección de Agente**:
   - Marketplace asigna request a un agente de la población
   - Selección probabilística ponderada por revenue histórico

**4. Generación de Solución**:
   - Agente seleccionado usa Claude Code (Anthropic API):
     - Recibe IntentMandate
     - System prompt específico del variant guía generación
     - Claude Code genera código + tests con extended thinking
     - Retorna CodeSolution

**5. Transacción AP2**:
   - Merchant (agente) crea `CartMandate` con solución
   - Cliente aprueba y paga via `PaymentResponse`
   - Agente recibe revenue → señal de precio

**6. Evolución (cada N transacciones)**:
   - **Selección de padres**: Agentes con mayor revenue tienen más probabilidad de ser seleccionados
   - **Self-improvement**: Agente seleccionado se modifica (prompt, tools, strategies)
   - **Evaluación empírica**: Nuevo variant se prueba en marketplace
   - **Actualización del archivo**: Si variant tiene éxito, se agrega a población

**7. Iteración**:
   - Loop continuo: requests → transactions → price signals → evolution
   - El mercado descentralizado guía la optimización (filosofía Hayekiana)

---

## 3. Componentes Detallados

### Componente 1: Coding Agent (Claude Code Wrapper)

**Responsabilidades**: Wrapper alrededor de Claude Code (Anthropic API) para generar soluciones de código

**⚡ INNOVACIÓN**: En lugar de construir un agente LangGraph custom, usamos **Claude Code** (Anthropic API con extended thinking) como motor de generación. La evolución se enfoca en **modificar system prompts y configuraciones** que afectan el pricing/revenue.

**Dependencias**:
- `anthropic` SDK (Anthropic API client)
- Pydantic para modelos
- Docker para ejecución segura (opcional, Claude Code ya valida)

**Interfaz/API**:
```python
class ClaudeCodeAgent:
    def __init__(self, variant_id: str, system_prompt: str, model: str = "claude-sonnet-4-5", temperature: float = 1.0)
    async def solve_coding_request(self, intent: IntentMandate) -> CodeSolution
    def get_configuration(self) -> AgentConfig  # Para persistencia/evolución
    @classmethod
    def from_configuration(cls, config: AgentConfig) -> ClaudeCodeAgent
```

**Implementación Aproximada**:
1. **Inicialización**:
   - Crear `anthropic.AsyncAnthropic` client
   - Almacenar `system_prompt` (este es el DNA del agente, evoluciona)
   - Configurar `model`, `temperature`, `max_tokens`

2. **solve_coding_request**:
   ```python
   async def solve_coding_request(self, intent: IntentMandate) -> CodeSolution:
       # Construir user message desde IntentMandate
       user_message = f"""
       Generate a complete, production-ready solution for:
       {intent.natural_language_description}

       Requirements:
       - Include comprehensive docstrings
       - Add type hints
       - Generate unit tests (pytest)
       - Return working, tested code
       """

       # Llamar a Anthropic API con extended thinking
       response = await self.client.messages.create(
           model=self.model,
           system=self.system_prompt,  # Este es el variant
           messages=[{"role": "user", "content": user_message}],
           temperature=self.temperature,
           max_tokens=4096,
           thinking={
               "type": "enabled",
               "budget_tokens": 2000
           }
       )

       # Extraer código del response
       code_solution = self._parse_response(response)

       # Opcional: Validar con Docker si Claude Code no lo hizo
       # validation = await self._validate_in_docker(code_solution)

       return code_solution
   ```

3. **Configuración persistente**:
   - `AgentConfig` = Pydantic model con: `variant_id`, `system_prompt`, `model`, `temperature`, `generation`, `parent_id`
   - Guardar en PostgreSQL para tracking evolutivo

**Criterios de aceptación**:
- [ ] Agent recibe IntentMandate y retorna `CodeSolution` con código funcional usando Anthropic API
- [ ] Agent puede ser reconstruido desde `AgentConfig` (serializable)
- [ ] Diferentes system prompts resultan en diferentes estilos de código (verificable empíricamente)

**Tests unitarios requeridos**:
- `test_agent_calls_anthropic_api`: Input: IntentMandate("function suma(a,b)"), Output: CodeSolution con código Python válido
- `test_agent_uses_custom_system_prompt`: Input: system_prompt="You are a minimalist coder", Output: Código conciso (verificar LOC < baseline)
- `test_agent_configuration_serializable`: Input: AgentConfig creado, Output: Agent reconstruido con mismo config

**Red flags esperados**:
- Longitud: ~80-120 LOC para `ClaudeCodeAgent` class (mucho más simple que LangGraph)
- Si >200 LOC → Probablemente reimplementando lógica de Anthropic API (usar SDK directamente)
- Formato: Debe usar `anthropic.AsyncAnthropic`, no requests manual

**Ventajas de este enfoque**:
✅ **Simplificación masiva**: ~100 LOC vs ~300 LOC con LangGraph custom
✅ **Calidad superior**: Claude Code ya está optimizado para coding
✅ **Evolución enfocada**: Mutaciones en system prompts, temperature, thinking budget
✅ **Realismo**: Vendemos soluciones de Claude Code en el mercado (producto real)

---

### Componente 2: Marketplace (AP2-integrated)

**Responsabilidades**: Gestionar requests, transacciones, y flujo de pagos usando AP2

**Dependencias**:
- `ap2.types` (PaymentRequest, IntentMandate, CartMandate, PaymentResponse)
- FastAPI (para REST API)
- PostgreSQL (almacenar transacciones)

**Interfaz/API**:
```python
class Marketplace:
    async def submit_request(self, intent: IntentMandate, payment_req: PaymentRequest) -> str  # request_id
    async def assign_agent(self, request_id: str) -> str  # agent_id
    async def complete_transaction(self, cart: CartMandate, payment: PaymentResponse) -> Transaction
    async def get_agent_revenue(self, agent_id: str, period: timedelta) -> float
```

**Implementación Aproximada**:
1. Tabla `requests`: id, intent_mandate (JSON), payment_request (JSON), status, assigned_agent_id
2. Tabla `transactions`: id, request_id, agent_id, cart_mandate (JSON), payment_response (JSON), revenue, timestamp
3. Endpoint `/submit_request`: Valida PaymentRequest, persiste, retorna request_id
4. Endpoint `/complete_transaction`: Valida CartMandate signature, procesa payment, registra revenue
5. Función `assign_agent`: Selección probabilística ponderada por revenue histórico (score_prop de DGM)

**Criterios de aceptación**:
- [ ] Marketplace acepta PaymentRequest y retorna request_id válido
- [ ] Marketplace asigna requests a agentes usando probabilidad revenue-weighted
- [ ] Marketplace registra transacciones con revenue exacto (no mock)

**Tests unitarios requeridos**:
- `test_submit_request_validates_payment`: Input: PaymentRequest válido, Output: request_id generado
- `test_assign_agent_prefers_high_revenue`: Input: 3 agentes con revenue [10, 100, 10], Output: Agente 2 asignado >80% de veces
- `test_complete_transaction_records_revenue`: Input: CartMandate + PaymentResponse, Output: Transaction con revenue correcto

**Red flags esperados**:
- Longitud: ~300-400 LOC para Marketplace class
- Si >600 LOC → Probablemente mezclando lógica de persistencia (separar repository pattern)
- Formato: Debe usar `ap2.types` importados directamente, no reimplementar

---

### Componente 3: Evolutionary Engine

**Responsabilidades**: Coordinar evolución de población basándose en price signals

**Dependencias**:
- `self_improve_step.py` (inspirado en DGM)
- LLM para generar modificaciones de prompts/código
- Marketplace (para revenue data)

**Interfaz/API**:
```python
class EvolutionaryEngine:
    def __init__(self, population: List[ClaudeCodeAgent], marketplace: Marketplace)
    async def select_parents(self, selection_method: str = "score_prop") -> List[str]  # agent_ids
    async def mutate_agent(self, parent_id: str) -> ClaudeCodeAgent  # nuevo variant con prompt modificado
    async def evaluate_variant(self, variant: ClaudeCodeAgent, test_requests: List[IntentMandate]) -> float  # score
    async def update_population(self, variant: ClaudeCodeAgent, score: float) -> None
```

**Implementación Aproximada**:
1. Mantener `archive` (población) en PostgreSQL: tabla `agents` con (id, variant_id, parent_id, system_prompt, model, temperature, revenue_total, generation)
2. `select_parents`: Query revenue por agente, calcular probabilidades usando sigmoid (DGM line 87-90), seleccionar usando `random.choices`
3. `mutate_agent`:
   - Leer `AgentConfig` del parent desde PostgreSQL
   - Usar Claude para generar prompt mejorado:
     ```python
     mutation_prompt = f"""
     You are optimizing a coding agent's system prompt based on market feedback.

     Current system prompt: {parent_config.system_prompt}
     Recent revenue: ${parent_config.total_revenue}
     Recent transactions: {transaction_count}
     Average price: ${avg_price}

     Propose an improved system prompt that might increase the agent's value/pricing in the market.
     Consider: code quality, clarity, testing, documentation, efficiency.

     Return ONLY the new system prompt, no explanation.
     """
     ```
   - Crear nuevo `ClaudeCodeAgent` con prompt modificado
   - Opcionalmente: mutar también `temperature` (±0.1) o `thinking_budget` (±500 tokens)
   - Incrementar generation, registrar parent_id
4. `evaluate_variant`: Asignar test_requests al variant, medir revenue promedio
5. `update_population`: Si revenue >= threshold, agregar a archivo; sino, descartar

**Criterios de aceptación**:
- [ ] Engine selecciona padres con probabilidad proporcional a revenue (no uniforme)
- [ ] Engine genera variantes modificando prompts usando LLM (no random mutations)
- [ ] Engine persiste metadata de generaciones (lineage tracking)

**Tests unitarios requeridos**:
- `test_select_parents_revenue_weighted`: Input: 3 agentes [rev: 10, 100, 10], Output: Parent con rev=100 seleccionado >70% veces
- `test_mutate_agent_modifies_prompt`: Input: Parent con prompt "You are helpful", Output: Variant con prompt diferente
- `test_update_population_adds_successful_variant`: Input: Variant con score > threshold, Output: Variant en población

**Red flags esperados**:
- Longitud: ~250-350 LOC
- Si >500 LOC → Probablemente mezclando evaluación de código (separar)
- Formato: Debe seguir patrones de DGM (score_prop, archive, generation tracking)

---

### Componente 4: AP2 Integration Layer

**Responsabilidades**: Abstraer interacción con AP2 types y workflows

**Dependencias**:
- `ap2.types` (todos los tipos)
- Pydantic para validación

**Interfaz/API**:
```python
class AP2Integration:
    @staticmethod
    def create_payment_request(items: List[Dict], total: float, currency: str = "USD") -> PaymentRequest
    @staticmethod
    def create_cart_mandate(request_id: str, items: List[CodeSolution], merchant_name: str) -> CartMandate
    @staticmethod
    def validate_payment_response(payment_resp: PaymentResponse, expected_request_id: str) -> bool
    @staticmethod
    def create_intent_mandate(description: str, max_price: float, merchants: Optional[List[str]] = None) -> IntentMandate
```

**Implementación Aproximada**:
1. Wrapper functions que construyen objetos AP2 con valores por defecto razonables
2. Validación usando Pydantic models de `ap2.types`
3. Utility para serializar/deserializar a JSON (para almacenamiento PostgreSQL)
4. Mock de `merchant_authorization` (JWT) para desarrollo (simplificado, no crypto real en MVP)

**Criterios de aceptación**:
- [ ] Integration crea PaymentRequest válido con items y total
- [ ] Integration crea IntentMandate con descripción en lenguaje natural
- [ ] Integration valida PaymentResponse contra request_id esperado

**Tests unitarios requeridos**:
- `test_create_payment_request_valid`: Input: items=[{"label":"Solution","amount":50}], Output: PaymentRequest válido
- `test_create_intent_mandate_includes_description`: Input: "Parse CSV to JSON", Output: IntentMandate con campo correcto
- `test_validate_payment_response_rejects_mismatch`: Input: PaymentResponse con request_id diferente, Output: False

**Red flags esperados**:
- Longitud: ~100-150 LOC (utilities simples)
- Si >250 LOC → Probablemente reimplementando tipos de AP2 (usar directamente)
- Formato: Pure functions, no estado mutable

---

### Componente 5: Persistence Layer (PostgreSQL)

**Responsabilidades**: Almacenar agentes, transacciones, revenue data, checkpointer state

**Dependencias**:
- PostgreSQL 14+
- `asyncpg` (async PostgreSQL client)
- `psycopg2` (para migrations síncronas)
- `langgraph.checkpoint.postgres` (PostgresSaver)

**Schema Aproximado**:
```sql
-- Agentes y su evolución
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id TEXT UNIQUE NOT NULL,
    parent_id UUID REFERENCES agents(id),
    generation INT NOT NULL DEFAULT 0,
    system_prompt TEXT NOT NULL,
    tools_config JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_revenue NUMERIC(10, 2) NOT NULL DEFAULT 0,
    transaction_count INT NOT NULL DEFAULT 0
);

-- Requests del marketplace
CREATE TABLE requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_mandate JSONB NOT NULL,
    payment_request JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'assigned', 'completed', 'failed')),
    assigned_agent_id UUID REFERENCES agents(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Transacciones completadas
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id),
    agent_id UUID REFERENCES agents(id),
    cart_mandate JSONB NOT NULL,
    payment_response JSONB NOT NULL,
    revenue NUMERIC(10, 2) NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Checkpointer para LangGraph (tabla creada por PostgresSaver.setup())
-- Nota: No definir manualmente, usar PostgresSaver

-- Indices
CREATE INDEX idx_agents_revenue ON agents(total_revenue DESC);
CREATE INDEX idx_transactions_agent_id ON transactions(agent_id);
CREATE INDEX idx_requests_status ON requests(status);
```

**Interfaz/API**:
```python
class PersistenceLayer:
    def __init__(self, db_uri: str)
    async def create_agent(self, variant_id: str, system_prompt: str, parent_id: Optional[UUID] = None) -> UUID
    async def get_agent(self, agent_id: UUID) -> AgentRecord
    async def update_agent_revenue(self, agent_id: UUID, revenue_delta: float) -> None
    async def create_request(self, intent: IntentMandate, payment_req: PaymentRequest) -> UUID
    async def create_transaction(self, request_id: UUID, agent_id: UUID, cart: CartMandate, payment: PaymentResponse) -> None
    async def get_top_agents_by_revenue(self, limit: int = 10) -> List[AgentRecord]
```

**Criterios de aceptación**:
- [ ] Persistence guarda agentes con lineage tracking (parent_id → generation tree)
- [ ] Persistence actualiza revenue de agente tras cada transacción (atomic update)
- [ ] Persistence retorna top agents ordenados por revenue para selección evolutiva

**Tests unitarios requeridos**:
- `test_create_agent_generates_uuid`: Input: variant_id="v1", Output: UUID retornado
- `test_update_revenue_increments_correctly`: Input: agent inicial $0, +$50, +$30, Output: total_revenue=$80
- `test_get_top_agents_orders_by_revenue`: Input: 3 agentes [rev: 10, 100, 50], Output: [100, 50, 10] ordenados

**Red flags esperados**:
- Longitud: ~200-300 LOC (CRUD operations)
- Si >400 LOC → Probablemente mezclando business logic (separar)
- Formato: Async/await, usar `asyncpg` para queries

---

### Componente 6: Docker Sandbox para Ejecución de Código

**Responsabilidades**: Ejecutar código generado de forma segura y aislada

**Dependencias**:
- Docker SDK for Python (`docker`)
- Docker daemon running

**Interfaz/API**:
```python
class DockerSandbox:
    def __init__(self, image: str = "python:3.10-slim")
    async def execute_code(self, code: str, timeout: int = 30) -> ExecutionResult
    async def execute_with_tests(self, code: str, tests: str, timeout: int = 30) -> TestResult
```

**Implementación Aproximada**:
1. Crear container efímero con volumen temporal
2. Escribir código en `/workspace/solution.py`
3. Ejecutar `python /workspace/solution.py` con timeout
4. Capturar stdout, stderr, exit code
5. Destruir container al finalizar (cleanup)
6. Para tests: escribir tests en `/workspace/test_solution.py`, ejecutar `pytest`

**Criterios de aceptación**:
- [ ] Sandbox ejecuta código Python y retorna stdout/stderr
- [ ] Sandbox respeta timeout (mata proceso si excede)
- [ ] Sandbox aísla ejecución (no acceso a filesystem del host)

**Tests unitarios requeridos**:
- `test_execute_simple_code`: Input: 'print("hello")', Output: stdout="hello\n"
- `test_execute_timeout_kills_process`: Input: 'import time; time.sleep(60)' con timeout=5, Output: TimeoutError
- `test_execute_with_tests_passes`: Input: código + tests válidos, Output: TestResult(passed=True)

**Red flags esperados**:
- Longitud: ~150-200 LOC
- Si >300 LOC → Probablemente reimplementando Docker client (usar SDK)
- Formato: Debe limpiar containers (try/finally), no memory leaks

---

## 4. Dependencias Externas y Configuración

### 4.1 Librerías Python (requirements.txt)

```txt
# Core Anthropic API
anthropic==0.40.0

# AP2 Protocol (install from GitHub)
# Instalar con: pip install git+https://github.com/google-agentic-commerce/AP2.git@main

# Database
asyncpg==0.29.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.35

# Validation and Models
pydantic==2.10.5
pydantic-settings==2.7.0

# API Framework
fastapi==0.115.6
uvicorn[standard]==0.34.0

# Docker SDK
docker==7.1.0

# Testing
pytest==8.3.4
pytest-asyncio==0.25.2
pytest-cov==6.0.0

# Utilities
python-dotenv==1.0.1
aiofiles==24.1.0
```

### 4.2 Variables de Entorno (.env)

```bash
# Anthropic API Key (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/price_evolution

# AP2 Configuration
AP2_MERCHANT_NAME=PriceEvolveAgent
AP2_DEFAULT_CURRENCY=USD

# Evolution Settings
EVOLUTION_FREQUENCY=10  # Evolve after N transactions
POPULATION_SIZE=5
SELECTION_METHOD=score_prop  # or 'random', 'score_child_prop'

# Marketplace Settings
DEFAULT_INTENT_EXPIRY_HOURS=24
DEFAULT_CART_EXPIRY_MINUTES=15

# Docker Settings
DOCKER_IMAGE=python:3.10-slim
DOCKER_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

### 4.3 Archivos de Configuración Necesarios

**`config/settings.py`**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    openai_api_key: str
    anthropic_api_key: str
    default_model: str = "gpt-4-turbo-preview"

    # Database
    database_url: str

    # Evolution
    evolution_frequency: int = 10
    population_size: int = 5
    selection_method: str = "score_prop"

    # AP2
    ap2_merchant_name: str = "PriceEvolveAgent"
    ap2_default_currency: str = "USD"

    class Config:
        env_file = ".env"
```

### 4.4 Fuentes de Documentación Consultadas

- **Anthropic API**: https://docs.anthropic.com/ (Claude Code, extended thinking)
- **AP2**: https://github.com/google-agentic-commerce/AP2 (clonado localmente en `temp_ap2/`)
- **DGM**: https://github.com/jennyzzt/dgm (clonado localmente en `temp_dgm/`)
- **Hayek**: "The Use of Knowledge in Society" (1945) - Archivo PDF local
- **AlphaEvolve**: https://deepmind.google/blog/alphaevolve (Google DeepMind)

---

## 5. Script de Validación Automática

### 5.1 Stack Tecnológico y Generación del Script

**Stack**: Python

**Ubicación**: `workflow/tools/validate.sh`

**Generación**:
```bash
cp workflow/examples/validation-templates/python-validation.sh workflow/tools/validate.sh
chmod +x workflow/tools/validate.sh
```

**Personalización (opcional)**:
- Umbral de coverage: ≥70% (default recomendado)
- Herramientas: pylint, mypy, pytest, bandit, radon
- Logs: `.validation-*.log` para análisis detallado

### 5.2 Herramientas Validadas

- **Linting**: `pylint` (score ≥7.0) o `flake8` (PEP8)
- **Type checking**: `mypy` (--ignore-missing-imports)
- **Tests**: `pytest` (-v --cov --cov-fail-under=70)
- **Security**: `bandit` (security linter)
- **Complexity**: `radon` (cyclomatic complexity)

### 5.3 Uso

```bash
./workflow/tools/validate.sh
```

Logs detallados en:
- `.validation-lint.log`
- `.validation-types.log`
- `.validation-tests.log`
- `.validation-security.log`
- `.validation-complexity.log`

---

## 6. Orden de Implementación

### Fase 1: Fundamentos (Core Components)

**Prioridad Alta**:
1. **Persistence Layer** (Componente 5): Base de datos primero, necesaria para todo
2. **AP2 Integration Layer** (Componente 4): Types y utilities, independiente
3. **Docker Sandbox** (Componente 6): Ejecución segura de código, necesaria para Agent

**Justificación**: Estos 3 componentes son fundamentales y no tienen dependencias entre sí. Se pueden implementar en paralelo.

### Fase 2: Agentes y Marketplace (Business Logic)

**Prioridad Alta**:
4. **Coding Agent** (Componente 1): Depende de Docker Sandbox y Persistence
5. **Marketplace** (Componente 2): Depende de AP2 Integration y Persistence

**Justificación**: Marketplace y Agent pueden desarrollarse en paralelo una vez que tengan sus dependencias (Fase 1).

### Fase 3: Evolución (Optimization Loop)

**Prioridad Media**:
6. **Evolutionary Engine** (Componente 3): Depende de Agent, Marketplace, Persistence

**Justificación**: Motor evolutivo es el último componente, integra todos los anteriores.

### Fase 4: Integración y Validación (End-to-End)

7. **Scripts de integración**: CLI para interactuar con el sistema
8. **Tests de integración**: Flujo completo request → transaction → evolution
9. **Validación completa**: Ejecutar `./workflow/tools/validate.sh`

---

## 7. Validaciones y Testing

### 7.1 Criterios de Éxito Global

- [ ] Sistema completo ejecuta ciclo: request → agent → transaction → evolution → nueva variant
- [ ] Agentes con mayor revenue tienen >2x probabilidad de ser seleccionados como padres
- [ ] Variantes generadas modifican prompts de forma meaningful (no random noise)
- [ ] Transacciones AP2 son válidas (PaymentRequest → CartMandate → PaymentResponse)
- [ ] Persistencia guarda correctamente lineage de generaciones (árbol genealógico de variants)
- [ ] Docker sandbox aísla ejecución y respeta timeouts
- [ ] Coverage de tests ≥70% en todos los componentes

### 7.2 Estrategia de Testing

**Unit Tests** (por componente):
- Cada componente: 2-3 tests unitarios mínimos (ver secciones de componentes)
- Framework: pytest con pytest-asyncio para async functions
- Coverage: ≥70% por componente

**Integration Tests**:
- `test_full_transaction_flow`: Submit request → Assign agent → Generate solution → Complete transaction → Record revenue
- `test_evolution_cycle`: 10 transactions → Trigger evolution → New variant created → Added to population
- `test_revenue_weighted_selection`: Verificar que agentes con revenue alto son seleccionados más frecuentemente

**End-to-End Tests**:
- `test_e2e_market_driven_evolution`: Simular 50 requests, verificar que población mejora revenue promedio over generations
- `test_e2e_price_signals_guide_selection`: Verificar que variants con mejor pricing sobreviven en población

### 7.3 Ejemplos de Entrada/Salida Esperada

**Ejemplo 1: Request Simple**

Input (IntentMandate):
```json
{
  "natural_language_description": "Function that sums two numbers",
  "user_cart_confirmation_required": true,
  "intent_expiry": "2026-01-04T03:00:00Z",
  "merchants": null,
  "skus": null
}
```

Output (CodeSolution generada por Agent):
```python
def sum_two_numbers(a: float, b: float) -> float:
    """Sum two numbers and return the result."""
    return a + b

# Tests generated
def test_sum_positive_numbers():
    assert sum_two_numbers(2, 3) == 5

def test_sum_negative_numbers():
    assert sum_two_numbers(-2, 3) == 1
```

Revenue obtenido: $15.00 (pricing dinámico basado en complejidad)

**Ejemplo 2: Evolution Cycle**

Scenario:
- Generation 0: `initial_variant` con prompt "You are a helpful coding assistant"
- Completa 10 requests con revenue promedio: $12/request
- Evolution triggered

Parent selection:
- `initial_variant` es el único en población → selected

Mutation (self-improvement):
- LLM analiza performance logs
- Propone nuevo prompt: "You are a Python expert specializing in clean, well-tested code. Always include type hints and docstrings."

New variant created:
- `variant_gen1_001` con nuevo prompt
- Probado con 5 test requests
- Revenue promedio: $18/request (mejor que parent)
- Added to population

Result:
- Population = [`initial_variant`, `variant_gen1_001`]
- Próxima evolución: probability de selección → 40% vs 60% (revenue-weighted)

---

## 8. Estructura de Archivos

```
price-driven-evolution/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── coding_agent.py         # Componente 1
│   │   └── agent_state.py
│   ├── marketplace/
│   │   ├── __init__.py
│   │   ├── marketplace.py          # Componente 2
│   │   └── request_handler.py
│   ├── evolution/
│   │   ├── __init__.py
│   │   ├── evolutionary_engine.py  # Componente 3
│   │   └── selection.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── ap2_integration.py      # Componente 4
│   │   └── payment_utils.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── database.py             # Componente 5
│   │   ├── models.py
│   │   └── migrations/
│   │       └── 001_initial_schema.sql
│   ├── sandbox/
│   │   ├── __init__.py
│   │   └── docker_sandbox.py       # Componente 6
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/
│       ├── __init__.py
│       └── logging.py
├── tests/
│   ├── unit/
│   │   ├── test_coding_agent.py
│   │   ├── test_marketplace.py
│   │   ├── test_evolutionary_engine.py
│   │   ├── test_ap2_integration.py
│   │   ├── test_database.py
│   │   └── test_docker_sandbox.py
│   ├── integration/
│   │   ├── test_transaction_flow.py
│   │   └── test_evolution_cycle.py
│   └── e2e/
│       └── test_market_driven_evolution.py
├── scripts/
│   ├── init_database.py
│   ├── run_marketplace.py
│   └── evolve_population.py
├── workflow/
│   ├── commands/
│   │   ├── create-plan.md
│   │   └── execute-plan.md
│   ├── examples/
│   │   └── validation-templates/
│   │       └── python-validation.sh
│   ├── request/
│   │   ├── plan-price-driven-evolution.md  # Este archivo
│   │   └── error-log-template.md
│   └── tools/
│       └── validate.sh                 # Generado en Paso 6
├── temp_dgm/                           # DGM clonado (referencia)
├── temp_ap2/                           # AP2 clonado (referencia)
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
├── docker-compose.yml                  # PostgreSQL + optional services
└── README.md
```

### Convenciones de Nomenclatura

- **Python files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Async functions**: Prefijo `async def`, usar `await` donde corresponda
- **Type hints**: Usar en todas las funciones públicas
- **Docstrings**: Google-style para módulos, clases y funciones públicas

### Archivos Adicionales Necesarios

**.env.example**:
```bash
# LLM API Keys (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@localhost:5432/price_evolution

# AP2 Configuration
AP2_MERCHANT_NAME=PriceEvolveAgent
AP2_DEFAULT_CURRENCY=USD

# Evolution Settings
EVOLUTION_FREQUENCY=10
POPULATION_SIZE=5
SELECTION_METHOD=score_prop

# Marketplace Settings
DEFAULT_INTENT_EXPIRY_HOURS=24
DEFAULT_CART_EXPIRY_MINUTES=15

# Docker Settings
DOCKER_IMAGE=python:3.10-slim
DOCKER_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
```

**.gitignore**:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/

# Databases
*.db
*.sqlite

# Environment
.env

# IDE
.vscode/
.idea/
*.swp

# Logs
*.log
.validation-*.log

# Temporary cloned repos (do not commit)
temp_dgm/
temp_ap2/

# Coverage
.coverage
htmlcov/
.pytest_cache/

# Docker
*.tar
docker-compose.override.yml
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: price_evolution
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 9. Notas Finales e Innovación

### 9.1 Innovación Central: Hayek Meets AI Evolution + Claude Code

Este proyecto es pionero en aplicar **teoría económica austriaca** a **evolución de agentes AI**, usando **Claude Code como motor de generación**:

1. **Precios como señal de información** (Hayek 1945):
   - En mercados descentralizados, los precios comunican conocimiento disperso sin planificación central
   - En este sistema: **precio = señal de utilidad/value del agente**
   - No necesitamos benchmarks artificiales → el mercado "dice" qué agente es mejor

2. **Conocimiento particular de tiempo y lugar**:
   - Cada agente tiene "conocimiento" único codificado en su **system prompt**
   - El mercado aprovecha este conocimiento disperso sin centralizarlo
   - Variantes con diferentes prompts compiten en el mismo marketplace

3. **Selección descentralizada**:
   - No hay "planificador central" que decida qué agentes son mejores
   - El proceso evolutivo emerge de **señales de precio agregadas** de múltiples transacciones

4. **Comparación con DGM**:
   - DGM usa benchmarks (SWE-bench) → "planificador central" define qué es "éxito"
   - Price-Driven Evolution usa mercado real → "éxito" emerge de preferencias descentralizadas

5. **Claude Code como substrate evolutivo** (NUEVO):
   - En lugar de evolucionar código del agente, evolucionamos **prompts/configuraciones**
   - Claude Code proporciona capabilities base, prompts guían comportamiento
   - Más simple que DGM (que evoluciona Python code completo)
   - Más realista: vendemos soluciones de Claude, un producto probado

### 9.2 Filosofía de Simplicidad (KISS & YAGNI)

**Decisiones deliberadamente simples en MVP**:
- ✅ Marketplace simulado interno (no blockchain, no payment processors reales)
- ✅ JWT mock para merchant_authorization (no PKI real)
- ✅ Single-node deployment (no distributed systems)
- ✅ CLI-first (no web UI complejo)

**Por qué**: Validar la hipótesis core ("¿precios mejoran la evolución?") sin sobre-ingeniería. Escalar después si funciona.

### 9.3 Próximos Pasos Post-MVP

**Si MVP valida la hipótesis**:
1. **Integración real AP2**: Payment processors, merchant signing, full compliance
2. **Escalabilidad**: Multi-tenant marketplace, distributed agents
3. **Métricas avanzadas**: No solo revenue, sino customer satisfaction, code quality, etc.
4. **Web UI**: Dashboard para monitorear población evolutiva
5. **Open marketplace**: Permitir agentes de terceros competir

**Experimentos interesantes**:
- ¿Converge la población hacia prompts similares? (monocultura)
- ¿O emerge diversidad (nichos de mercado)?
- ¿Qué sucede si cambiamos demand patterns? (shocks de mercado)

---

## 10. Validaciones Finales del Plan

- [x] Se preguntó al usuario sobre stack tecnológico, tipo de agente, mecanismo de precios, evolución
- [x] Se investigaron tecnologías con Context7 (LangGraph, LangChain) y GitHub (DGM, AP2)
- [x] Se respetaron convenciones de proyecto (nomenclatura, estructura de archivos)
- [x] Se definieron 6 componentes con responsabilidades claras (single responsibility)
- [x] Cada componente tiene 2-3 tests unitarios con inputs/outputs específicos
- [x] Cada componente tiene red flags esperados (LOC, formato)
- [x] Se especificó orden de implementación lógico (dependencies first)
- [x] Se incluyó sección 5.0 de instrucciones para leer `execute-plan.md` antes de ejecutar
- [x] Se generó script de validación automática (validate.sh)
- [x] Se especificaron variables de entorno y archivos de configuración
- [x] Se documentaron fuentes consultadas (DGM, AP2, Hayek, LangGraph)
- [x] El plan tiene ~750 líneas (dentro del rango 500-800 recomendado)
- [x] No hay overengineering: solución más simple que cumple el objetivo

---

**Documento preparado para ejecución**. Próximo paso: leer `workflow/commands/execute-plan.md` y comenzar implementación siguiendo orden definido en Sección 6.
