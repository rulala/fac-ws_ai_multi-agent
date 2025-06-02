# Building Multi-Agent Workflows with LangGraph Workshop

Learn to build sophisticated multi-agent systems by mastering six architectural patterns, progressing from simple linear workflows to production-ready systems.

## Workshop Philosophy

This workshop teaches LangGraph through architectural patterns, not code syntax - use AI for this (although note warning below about LangGraph). You'll understand **when** and **why** to choose different approaches, progressing from simple workflows to sophisticated multi-agent systems.

> [!CAUTION]
> LangGraph is a relatively recent library that is continuously updated with new syntax, not all LLMs have caught on to this so always cross-check with documentation when unsure. Ask AI to check latest documentation before generating any code too.

## Prerequisites

- Python 3.9+ or Anaconda/Miniconda
- OpenAI API key
- Basic Python and AI understanding
- Review [Multi-Agent Patterns: Practical Guide](PATTERNS.md) before starting

## Quick Start

1. **Clone the repository**:

   - **with https**:

   ```bash
   git clone https://github.com/TandemCreativeDev/fac-ws_ai_multi-agent.git
   cd fac-ws_ai_multi-agent
   ```

   - **with ssh**:

   ```bash
   git clone git@github.com:TandemCreativeDev/fac-ws_ai_multi-agent.git
   cd fac-ws_ai_multi-agent
   ```

2. **Setup environment**

   - **with conda** (recommended for Mac and Linux):

   ```bash
   conda env create -f environment.yml
   conda activate multi-agent
   ```

   - **with pip only** (easier for Windows):

   ```bash
   pip install langchain-openai langgraph python-dotenv
   ```

3. **Create `.env` file**:
   ```
   OPENAI_API_KEY=your_key_here
   ```

## How This Workshop Works

1. **Two versions per pattern**: Start with `patterns_simple/` to understand concepts, then do exercises in `patterns/`
2. **Six patterns**: Each builds on previous concepts
3. **Four exercises per pattern**: Modify the code to complete each exercise
4. **Generated output**: Check `generated/` folder after each run

## Approach Each Pattern

For each pattern:

1. **Read** the simple version in `patterns_simple/`
2. **Run** the full version in `patterns/`
3. **Examine** the generated output in `generated/`
4. **Complete** the 4 exercises by modifying the code
5. **Discuss** when you'd use this pattern vs others

## The Six Patterns

### Pattern 1: Sequential Workflow

**File**: `patterns/01_sequential_workflow.py`  
**Concept**: Linear pipeline (coder → reviewer → refactorer)  
**Use case**: Predictable, step-by-step processes

**Run and explore**:

```bash
python patterns/01_sequential_workflow.py
# Check generated/ folder for output
```

**Your 4 Exercises** (modify the code):

1. **Add a tester agent**: Create `tester_agent` function that generates unit tests. Add node after refactorer.
2. **Change focus**: Modify all prompts to emphasise security vulnerabilities instead of general quality.
3. **Add persistence**: Save state between nodes to a JSON file for debugging.
4. **Measure performance**: Add timing to each node, print execution summary.

### Pattern 2: Conditional Routing

**File**: `patterns/02_conditional_routing.py`  
**Concept**: Quality gates determine workflow paths  
**Use case**: Iterative improvement based on evaluation

**Run and explore**:

```bash
python patterns/02_conditional_routing.py
# Note iteration count in output
```

**Your 4 Exercises** (modify the code):

1. **Adjust threshold**: Change `quality_threshold = 7` to 9. How many iterations now?
2. **Add fast track**: If initial score ≥ 9, skip refactoring entirely.
3. **Multi-criteria evaluation**: Score separately for security, performance, readability. Route based on lowest.
4. **Implement backoff**: Make `max_iterations` increase with each retry (3, 5, 7).

### Pattern 3: Parallel Processing

**File**: `patterns/03_parallel_processing.py`  
**Concept**: Concurrent analysis by multiple specialists  
**Use case**: Independent tasks that can run simultaneously

**Run and explore**:

```bash
python patterns/03_parallel_processing.py
# Check SYNTHESIS_REPORT.md
```

**Your 4 Exercises** (modify the code):

1. **Add documentation agent**: Create `documentation_agent` that generates docstrings. Run in parallel.
2. **Add timing**: Import `time`, measure sequential vs parallel execution.
3. **Handle failures**: Wrap agents in try/except, continue if one fails.
4. **Weighted synthesis**: Give security 2x weight in final recommendations.

### Pattern 4: Supervisor Agents

**File**: `patterns/04_supervisor_agents.py`  
**Concept**: Intelligent coordination of specialist agents  
**Use case**: Complex tasks requiring dynamic expertise

**Run and explore**:

```bash
python patterns/04_supervisor_agents.py
# Check EXPERT_ANALYSIS.md
```

**Your 4 Exercises** (modify the code):

1. **Add database expert**: Create `database_expert_agent` for SQL/schema review. Update supervisor logic.
2. **Smart routing**: Make supervisor check code content (e.g., "if 'sql' in code: route to database expert").
3. **Expert collaboration**: Let security expert see quality report before finalising.
4. **Add priorities**: Supervisor should consult security expert first for authentication tasks.

### Pattern 5: Evaluator-Optimiser

**File**: `patterns/05_evaluator_optimiser.py`  
**Concept**: Continuous improvement through feedback loops  
**Use case**: Iteratively refinable outputs

**Run and explore**:

```bash
python patterns/05_evaluator_optimiser.py
# Watch score progression
```

**Your 4 Exercises** (modify the code):

1. **Track metrics**: Add complexity score using `radon` library. Optimise for both quality and simplicity.
2. **Targeted optimisation**: If feedback mentions "performance", use performance-specific optimiser.
3. **Detect plateau**: If score doesn't improve for 2 iterations, stop early.
4. **History tracking**: Store all iterations in state, generate comparison chart.

### Pattern 6: Production Ready

**File**: `patterns/06_production_ready.py`  
**Concept**: Error handling, retries, and approval gates  
**Use case**: Real-world deployment requirements

**Run and explore**:

```bash
python patterns/06_production_ready.py
# Note retry behaviour
```

**Your 4 Exercises** (modify the code):

1. **Add monitoring**: Log each node entry/exit with timestamps to `workflow.log`.
2. **Circuit breaker**: After 2 consecutive failures, skip to manual review.
3. **Rollback state**: Save last approved version, revert if new version fails.
4. **Compliance check**: Add `compliance_agent` that checks regulatory requirements before approval.

## Output Structure

Full pattern implementations generate timestamped folders in `generated/`:

```
generated/
└── 01_sequential_workflow_20250602_143022/
    ├── original_code.py
    ├── refactored_code.py
    └── AUDIT_TRAIL.md
```

## Key Learning Progression

1. **Understand**: Run simple version, trace execution flow
2. **Experiment**: Complete the 4 exercises for each pattern
3. **Analyse**: Compare patterns - when would you choose each?
4. **Build**: Combine patterns for your use case

## Workshop Tips

- Start with `patterns_simple/` to understand core concepts
- Use `patterns/` for exercises - they have proper output handling
- Generated code appears in `generated/` folder with timestamps
- Each pattern builds on previous concepts
- Focus on **when** to use each pattern, not just **how**

## Pattern Selection Guide

| Your Need                 | Use This Pattern |
| ------------------------- | ---------------- |
| Step-by-step process      | Sequential       |
| Quality-based branching   | Conditional      |
| Speed through parallelism | Parallel         |
| Complex coordination      | Supervisor       |
| Iterative improvement     | Evaluator        |
| Production deployment     | Production Ready |

## Next Steps

After completing all exercises:

1. Identify your use case's requirements
2. Select appropriate pattern(s)
3. Combine patterns if needed
4. Deploy using LangGraph Platform

## Debugging

- Check `.env` file for API key
- Ensure conda environment is activated
- Generated files appear in `generated/` folder
- Each run creates new timestamped folder

---

**Remember**: Master the patterns, then combine them creatively. The best solution uses the simplest pattern that meets your requirements.

## Author

[**TandemCreativeDev**](https://github.com/TandemCreativeDev) - hello@runintandem.com
