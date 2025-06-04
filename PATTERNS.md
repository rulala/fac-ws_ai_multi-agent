# Multi-Agent Patterns: Practical Guide

## Visual Pattern Progression

```mermaid
graph LR
    Start[Prototype] -.->|Simple| A[Sequential]
    A -.->|Intelligence| B[Conditional]
    B -.->|Speed| C[Parallel]
    C -.->|Expertise| D[Supervisor]
    D -.->|Quality| E[Evaluator]
    E -.->|Flexibility| F[Orchestrator]
    F -.->|Deploy| G[Production]
```

### Pattern Decision Logic

```mermaid
graph LR
    Start[Start Simple] --> Need{What do you need?}

    Need -->|Quality Gates| AddIntelligence[Add Intelligence<br/>Conditional Routing]
    Need -->|Speed| ScalePerformance[Scale Performance<br/>Parallel Processing]
    Need -->|Domain Knowledge| GainExpertise[Gain Expertise<br/>Supervisor Agents]
    Need -->|Perfect Output| EnsureQuality[Ensure Quality<br/>Evaluator-Optimiser]
    Need -->|Dynamic Tasks| AddFlexibility[Add Flexibility<br/>Orchestrator-Worker]
    Need -->|Real Deployment| DeploySafely[Deploy Safely<br/>Production Ready]

    AddIntelligence --> Need
    ScalePerformance --> Need
    GainExpertise --> Need
    EnsureQuality --> Need
    AddFlexibility --> Need
    DeploySafely --> Production[Production System]
```

## Pattern 1: Sequential Workflow

- **When to use**: Tasks with fixed steps that must run in order
- **Workflow**: [Prompt chaining](https://www.anthropic.com/engineering/building-effective-agents#workflow-prompt-chaining)
- **File**: `01_sequential_workflow.py`
- **Description**: Linear pipeline: coder → reviewer → refactorer
- **Best for**: Simple, predictable workflows
- **Complexity**: Low
- **Execution**: Fast
- **Use cases**: Basic automation, Simple validation, Learning LangGraph

```mermaid
graph LR
    START --> Coder
    Coder --> Reviewer
    Reviewer --> Refactorer
    Refactorer --> END
```

```python
# Key structure
builder.add_edge(START, "coder")
builder.add_edge("coder", "reviewer")
builder.add_edge("reviewer", "refactorer")
builder.add_edge("refactorer", END)
```

**Real example**: Code generation → Review → Refactor <br /> <br />

**Pros**: Simple, predictable, easy to debug <br />
**Cons**: No parallelism, no dynamic routing <br />

## Pattern 2: Conditional Routing

- **When to use**: Different code types need different expert analysis
- **Workflow**: [Routing](https://www.anthropic.com/engineering/building-effective-agents#workflow-routing)
- **File**: `02_conditional_routing.py`
- **Description**: Content-based routing to specialist agents
- **Best for**: Domain-specific expert selection
- **Complexity**: Medium
- **Execution**: Fast (single path)
- **Use cases**: Expert systems, Domain-specific analysis, Intelligent routing

```mermaid
graph LR
    START --> Coder
    Coder --> Router
    Router --> RouteDecision{Content Type?}
    RouteDecision -->|Security| SecurityExpert
    RouteDecision -->|Performance| PerformanceExpert
    RouteDecision -->|General| GeneralExpert
    SecurityExpert --> Synthesis
    PerformanceExpert --> Synthesis
    GeneralExpert --> Synthesis
    Synthesis --> END
```

```python
# Key structure
def route_to_specialist(state):
    route = state["route_decision"]
    return f"{route}_expert"

builder.add_conditional_edges("router", route_to_specialist,
    {"security_expert": "security_expert",
     "performance_expert": "performance_expert",
     "general_expert": "general_expert"})
```

**Real example**: Router analyzes code → Routes authentication code to security expert → Expert provides domain analysis

**Pros**: Efficient expert utilization, intelligent content-based routing
**Cons**: Limited to predefined expert domains, single expert per execution

## Pattern 3: Parallel Processing

- **When to use**: Multiple independent analyses needed
- **Workflow**: [Parallelisation](https://www.anthropic.com/engineering/building-effective-agents#workflow-parallelization)
- **File**: `03_parallel_processing.py`
- **Description**: Concurrent analysis by multiple specialists
- **Best for**: Independent, parallelisable tasks
- **Complexity**: Medium
- **Execution**: Fast (parallel)
- **Use cases**: Document processing, Multi-aspect analysis, Performance optimisation

```mermaid
graph LR
    START --> Coder
    Coder --> SecurityAgent
    Coder --> PerformanceAgent
    Coder --> StyleAgent
    SecurityAgent --> Synthesis
    PerformanceAgent --> Synthesis
    StyleAgent --> Synthesis
    Synthesis --> END
```

```python
# Key structure
builder.add_edge("coder", "security_agent")
builder.add_edge("coder", "performance_agent")
builder.add_edge("coder", "style_agent")
# All run simultaneously
```

**Real example**: Security, performance, and style checks running concurrently <br /> <br />

**Pros**: Faster execution, independent failures <br />
**Cons**: Harder to debug, needs result aggregation <br />

## Pattern 4: Supervisor-Agents

- **When to use**: Dynamic expert selection based on content
- **Workflow**: [OAgent Supervisor](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/)
- **File**: `04_supervisor_agents.py`
- **Description**: Intelligent coordination of specialist agents
- **Best for**: Complex tasks requiring expertise
- **Complexity**: High
- **Execution**: Efficient
- **Use cases**: Complex analysis, Domain expertise, Dynamic workflows

```mermaid
graph TD
    START --> Coder
    Coder --> Supervisor
    Supervisor --> Decision{Which Expert?}

    Decision -->|Security| SecurityExpert
    Decision -->|Quality| QualityExpert
    Decision -->|Complete| Synthesis

    SecurityExpert --> Supervisor
    QualityExpert --> Supervisor

    Synthesis --> END
```

```python
# Key structure
def route_to_expert(state):
    if "security" in state["needs"]:
        return "security_expert"
    elif "performance" in state["needs"]:
        return "performance_expert"
```

**Real example**: Supervisor analyses code, routes to relevant experts only <br /> <br />

**Pros**: Efficient expert usage, intelligent routing <br />
**Cons**: Complex supervisor logic, coordination overhead <br />

## Pattern 5: Evaluator-Optimiser

- **When to use**: Output quality improves with iteration
- **Workflow**: [Evaluator-Optimiser](https://www.anthropic.com/engineering/building-effective-agents#workflow-evaluator-optimizer)
- **File**: `05_evaluator_optimiser.py`
- **Description**: Continuous improvement through feedback loops
- **Best for**: Iteratively improvable outputs
- **Complexity**: High
- **Execution**: Slow (iterative)
- **Use cases**: Content generation, Optimisation tasks, Quality refinement

```mermaid
graph LR
    START --> Generator
    Generator --> Evaluator
    Evaluator --> Continue{Score >= 8?}
    Continue -->|No| Optimiser
    Continue -->|Yes| Finalise
    Optimiser --> Evaluator
    Finalise --> END
```

```python
# Key structure
def should_continue(state):
    if state["score"] >= 8 or state["iterations"] >= 3:
        return "finalise"
    return "optimise"
```

**Real example**: Generate → Evaluate → Optimise loop until quality met <br /> <br />

**Pros**: Continuous improvement, clear termination <br />
**Cons**: Slow, may hit iteration limit before quality <br />

## Pattern 6: Orchestrator-Worker

- **When to use**: Tasks requiring dynamic decomposition into subtasks
- **Workflow**: [Orchestrator-Workers](https://www.anthropic.com/engineering/building-effective-agents#workflow-orchestrator-workers)
- **File**: `06_orchestrator_worker.py`
- **Description**: Dynamic task breakdown with isolated worker execution
- **Best for**: Complex, unpredictable task structures
- **Complexity**: Very High
- **Execution**: Dynamic (scales with task complexity)
- **Use cases**: Complex software projects, Research tasks, Multi-step workflows

```mermaid
graph TD
    START --> Orchestrator
    Orchestrator --> TaskBreakdown{Create Subtasks}
    TaskBreakdown -->|Send| Worker1[Worker]
    TaskBreakdown -->|Send| Worker2[Worker]
    TaskBreakdown -->|Send| Worker3[Worker]
    Worker1 --> Collect[Collect Results]
    Worker2 --> Collect
    Worker3 --> Collect
    Collect --> Synthesis
    Synthesis --> END
```

```python
# Key structure
def create_workers(state):
    return [Send("worker", {"task": task}) for task in state["subtasks"]]

builder.add_conditional_edges("orchestrator", create_workers, ["worker"])
```

**Real example**: "Build a web app" → [Create DB schema, Build API, Design frontend, Write tests] <br /> <br />

**Pros**: Maximum flexibility, dynamic scaling, isolated execution <br />
**Cons**: Most complex, harder to predict execution flow <br />

## Production Ready Implementation

- **When to use**: Real deployment with error handling needed, appended to your multi-agent system
- **File**: `07_production_ready.py`
- **Description**: Enterprise features: error handling, persistence, monitoring
- **Best for**: Real-world deployment
- **Complexity**: Very High
- **Execution**: Robust
- **Use cases**: Production systems, Enterprise deployment, Mission-critical tasks

```mermaid
graph TD
    START --> Coder
    Coder --> ErrorCheck{Error?}
    ErrorCheck -->|Yes| HandleErrors
    ErrorCheck -->|No| Reviewer
    HandleErrors --> RetryCheck{Retries < 3?}
    RetryCheck -->|Yes| Coder
    RetryCheck -->|No| ManualReview
    Reviewer --> Approval
    Approval --> ApprovalCheck{Approved?}
    ApprovalCheck -->|Yes| Finalise
    ApprovalCheck -->|No| HandleErrors
    Finalise --> END
    ManualReview --> END
```

```python
# Key structure
def check_approval(state):
    if state["approved"]:
        return "deploy"
    if state["retries"] < 3:
        return "retry"
    return "manual_review"
```

**Real implementation**: ANY pattern + error handling + retries + approval gates <br /> <br />

**What it adds**:

- Error handling and recovery
- Retry mechanisms with backoff
- Approval workflows
- State persistence
- Monitoring and logging
- Circuit breakers
- Rollback capabilities

**Important**: This is NOT a distinct architectural pattern but a set of concerns you apply to patterns 1-6 for production deployment

## Pattern Complexity & Performance

```mermaid
graph TD
    subgraph "Architectural Complexity"
        Sequential[Sequential<br/>★☆☆☆☆]
        Conditional[Conditional<br/>★★☆☆☆]
        Parallel[Parallel<br/>★★★☆☆]
        Supervisor[Supervisor<br/>★★★★☆]
        Evaluator[Evaluator<br/>★★★★☆]
        Orchestrator[Orchestrator<br/>★★★★★]
    end

    subgraph "Operational Complexity"
        Production[Production Ready<br/>★★★★★<br/>Applied to any pattern]
    end
```

| Pattern            | Latency | Reliability | Use When                   |
| ------------------ | ------- | ----------- | -------------------------- |
| Sequential         | 1x      | High        | Order matters              |
| Conditional        | 1-3x    | Medium      | Quality gates needed       |
| Parallel           | 0.3x    | Medium      | Speed critical             |
| Supervisor         | 1.2x    | High        | Complex coordination       |
| Evaluator          | 3-10x   | High        | Quality critical           |
| Orchestrator       | 2-20x   | Medium      | Dynamic task decomposition |
| + Production Ready | +50%    | Very High   | Deploying ANY pattern live |

## Combining Patterns

```mermaid
graph TD
    subgraph "Pattern Combinations"
        A[Conditional + Parallel]
        B[Supervisor + Evaluator]
        C[Orchestrator + Supervisor]
        D[Any Pattern + Production]

        A --> E[Quality gate triggers<br/>parallel analysis]
        B --> F[Supervisor picks experts,<br/>evaluator ensures quality]
        C --> G[Orchestrator creates tasks,<br/>supervisor routes to experts]
        D --> H[Base pattern with<br/>error handling & monitoring]
    end
```

Patterns can be mixed:

1. **Conditional + Parallel**: Quality gate triggers parallel analysis
2. **Supervisor + Evaluator**: Supervisor picks experts, evaluator ensures quality
3. **Orchestrator + Supervisor**: Orchestrator breaks down tasks, supervisor routes to domain experts
4. **Any Pattern + Production**: Add operational concerns to any architecture

## Implementation Guide

### Decision Matrix

| Scenario                          | Recommended Pattern | Complexity | Execution Time | Reason                                                 |
| --------------------------------- | ------------------- | ---------- | -------------- | ------------------------------------------------------ |
| Simple blog post review           | Sequential          | Low        | Fast           | Predictable workflow, no complex logic needed          |
| Code security analysis            | Parallel Processing | Medium     | Fast           | Multiple independent analyses can run concurrently     |
| Complex enterprise system review  | Supervisor Agents   | High       | Efficient      | Requires domain expertise and intelligent coordination |
| Creative content generation       | Evaluator-Optimiser | High       | Slow           | Benefits from iterative feedback and improvement       |
| Building complex software project | Orchestrator-Worker | Very High  | Variable       | Requires dynamic task decomposition and coordination   |
| Mission-critical financial system | Production Ready    | Very High  | Robust         | Requires robust error handling and monitoring          |
| Learning/prototyping              | Sequential          | Low        | Fast           | Simple to understand and implement                     |
| Quality assurance pipeline        | Conditional Routing | Medium     | Variable       | Quality gates determine workflow paths                 |
| Document processing at scale      | Parallel Processing | Medium     | Fast           | Independent tasks benefit from concurrency             |
| Multi-domain analysis             | Supervisor Agents   | High       | Efficient      | Dynamic expert selection based on content              |
| AI content refinement             | Evaluator-Optimiser | High       | Slow           | Continuous improvement through feedback                |
| Research with unknown scope       | Orchestrator-Worker | Very High  | Variable       | Cannot predict subtasks upfront                        |

### Simple vs Full Patterns

**Simple** (`patterns_simple/`):

- Minimal state
- Basic prompts
- Direct execution
- No output generation

**Full** (`patterns/`):

- Rich state management
- Detailed prompts
- Utils for output generation
- Audit trails

### State Management Evolution

```python
# Simple
class State(TypedDict):
    input: str
    code: str

# Full
class State(TypedDict):
    input: str
    code: str
    review: str
    refactored_code: str
    iteration_count: int
    quality_score: int

# Orchestrator (adds dynamic workers)
class OrchestratorState(TypedDict):
    input: str
    subtasks: List[dict]
    worker_outputs: List[str]
    final_result: str

# Production (adds to any pattern)
class ProductionState(TypedDict):
    # ... existing state fields ...
    retry_count: int
    error_log: str
    approved: bool
    rollback_state: dict
```

### Common Pitfalls

❌ **Using Supervisor for simple tasks** - Overkill, use Sequential <br />
❌ **Parallel without aggregation** - Results get lost <br />
❌ **Conditional without max iterations** - Infinite loops <br />
❌ **Evaluator for time-critical tasks** - Too slow <br />
❌ **Orchestrator for predictable tasks** - Unnecessary complexity <br />
❌ **Deploying without production concerns** - No error recovery <br />

### Decision Framework

Ask yourself:

1. **Is order important?** → Sequential
2. **Need quality assurance?** → Conditional or Evaluator
3. **Can tasks run together?** → Parallel
4. **Need smart coordination?** → Supervisor
5. **Unknown task structure?** → Orchestrator
6. **Deploying to production?** → Add Production concerns to chosen pattern

Start simple, add complexity only when needed. Add production concerns before deploying.

### Key Architectural Differences

| Pattern          | Coordination    | Agent Creation | State Sharing | When to Use                |
| ---------------- | --------------- | -------------- | ------------- | -------------------------- |
| **Parallel**     | None            | Static         | Shared        | Speed through independence |
| **Supervisor**   | Central routing | Static         | Shared        | Expert selection           |
| **Orchestrator** | Task breakdown  | Dynamic        | Isolated      | Unknown task structure     |

Understanding these differences helps you choose the right pattern for your specific use case.
