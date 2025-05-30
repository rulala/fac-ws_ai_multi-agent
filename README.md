# Building Multi-Agent Workflows with LangGraph Workshop

A progressive, hands-on tutorial for building multi-agent code review systems using LangGraph architectural patterns.

## Workshop Philosophy

This workshop teaches LangGraph through architectural patterns, not copy-paste code. You'll understand **when** and **why** to choose different approaches, progressing from simple workflows to sophisticated multi-agent systems.

## Prerequisites

- Python 3.9+ or Anaconda/Miniconda
- OpenAI API key
- Basic understanding of Python and AI concepts
- Read about the [architectural patterns](PATTERNS.md)

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

   - **with conda** (recommended):

   ```bash
   conda env create -f environment.yml
   conda activate multi-agent
   ```

   - **with pip only:**

   ```bash
   pip install langchain-openai langgraph python-dotenv
   ```

## Workshop Structure

### Part 1: Foundation - Simple Sequential Workflow

**Pattern**: Linear code review pipeline
**When to use**: Predictable, sequential tasks
**File**: `01_sequential_workflow.py`

Build a basic coder → reviewer → refactorer pipeline. Learn LangGraph fundamentals: states, nodes, edges.

#### Key Concepts

- StateGraph basics
- Sequential execution
- State management

#### Challenges

1. Try different coding tasks
2. Modify prompts to change agent behaviour
3. Add a 'tester' agent that writes unit tests
4. **Discussion**: When would you use this pattern vs others?

### Part 2: Adding Intelligence - Conditional Routing

**Pattern**: Routing based on code quality
**When to use**: Different paths based on evaluation
**File**: `02_conditional_routing.py`

Add quality gates that route code based on review scores. Poor code gets additional refinement cycles.

#### Key Concepts

- Conditional edges
- Quality evaluation
- Branching logic

#### Challenges

1. Adjust quality threshold and see how it affects iterations
2. Add different quality criteria (security, performance)
3. Create a 'fast track' for simple code that skips some steps
4. **Discussion**: When would conditional routing be better than sequential flow?

### Part 3: Efficiency - Parallel Processing

**Pattern**: Concurrent analysis
**When to use**: Independent, parallelisable tasks
**File**: `03_parallel_processing.py`

Run code analysis, security scanning, and performance checks simultaneously.

#### Key Concepts

- Parallel execution
- Result aggregation
- Performance optimisation

#### Challenges

1. Add a testing agent that runs in parallel
2. Compare execution time vs sequential approach
3. Add error handling for failed parallel tasks
4. **Discussion**: When is parallel processing most beneficial?

### Part 4: Specialisation - Multi-Agent Supervisor

**Pattern**: Supervisor with specialised agents
**When to use**: Complex tasks requiring domain expertise
**File**: `04_supervisor_agents.py`

A supervisor coordinates specialised agents: security expert, performance analyst, code quality checker.

#### Key Concepts

- Agent specialisation
- Supervisor pattern
- Dynamic agent selection

#### Challenges

1. Add domain-specific experts (e.g., database, API design)
2. Make supervisor more intelligent about expert selection
3. Add expert-to-expert communication
4. **Discussion**: When is supervision better than parallel processing?

### Part 5: Reliability - Evaluator-Optimiser Loop

**Pattern**: Continuous improvement through feedback
**When to use**: When output quality can be iteratively improved
**File**: `05_evaluator_optimiser.py`

Add a feedback loop where an evaluator scores outputs and provides improvement suggestions.

#### Key Concepts

- Feedback loops
- Quality assessment
- Iterative refinement

#### Challenges

1. Add specific evaluation criteria (e.g., test coverage)
2. Create different optimisation strategies based on issue type
3. Add human-in-the-loop evaluation
4. **Discussion**: When is iterative optimisation most valuable?

### Part 6: Production Readiness

**Pattern**: Error handling, persistence, monitoring
**When to use**: Real-world deployment
**File**: `06_production_ready.py`

Add error handling, state persistence, human-in-the-loop, and monitoring.

#### Key Concepts

- Error recovery
- State persistence
- Human oversight
- Monitoring and debugging

#### Challenges

## Hands-On Exercises

Each part includes:

1. **Build**: Implement the pattern
2. **Experiment**: Modify prompts, add features
3. **Analyse**: Compare with previous approaches
4. **Decide**: When would you use this pattern?

## Pattern Decision Guide

| Pattern             | Best For                   | Avoid When              |
| ------------------- | -------------------------- | ----------------------- |
| Sequential          | Predictable workflows      | Dynamic requirements    |
| Conditional         | Quality-dependent paths    | Complex decision trees  |
| Parallel            | Independent tasks          | Sequential dependencies |
| Supervisor          | Complex, specialised tasks | Simple workflows        |
| Evaluator-Optimiser | Improvable outputs         | Time-critical tasks     |

## Architecture Progression

```
Sequential → Conditional → Parallel → Multi-Agent → Self-Improving
   ↓            ↓           ↓          ↓            ↓
 Simple      Quality     Speed    Expertise    Excellence
```

## Real-World Applications

- **Sequential**: Basic automation workflows
- **Conditional**: Content moderation systems
- **Parallel**: Document processing pipelines
- **Supervisor**: Complex analysis platforms
- **Evaluator-Optimiser**: AI content generation

## Next Steps

After completing this workshop:

1. **Experiment** with combining patterns
2. **Build** your own use case using appropriate patterns
3. **Deploy** using LangGraph Platform
4. **Monitor** and optimise in production

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Academy](https://github.com/langchain-ai/langchain-academy)
- [Production Examples](https://blog.langchain.dev/top-5-langgraph-agents-in-production-2024/)

---

**Remember**: Choose the simplest pattern that solves your problem. Complexity should be justified by requirements, not excitement about features.

## Author

[**TandemCreativeDev**](https://github.com/TandemCreativeDev) - hello@runintandem.com
