# Building Multi-Agent Workflows with LangGraph Workshop

A progressive, hands-on tutorial for building multi-agent code review systems using LangGraph architectural patterns.

## Workshop Philosophy

This workshop teaches LangGraph through architectural patterns, not copy-paste code. You'll understand **when** and **why** to choose different approaches, progressing from simple workflows to sophisticated multi-agent systems.

## Prerequisites

- Python 3.9+ or Anaconda/Miniconda
- OpenAI/Anthropic API key
- Basic understanding of Python and AI concepts

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

**Key Concepts:**

- StateGraph basics
- Sequential execution
- State management

### Part 2: Adding Intelligence - Conditional Routing

**Pattern**: Routing based on code quality
**When to use**: Different paths based on evaluation
**File**: `02_conditional_routing.py`

Add quality gates that route code based on review scores. Poor code gets additional refinement cycles.

**Key Concepts:**

- Conditional edges
- Quality evaluation
- Branching logic

### Part 3: Efficiency - Parallel Processing

**Pattern**: Concurrent analysis
**When to use**: Independent, parallelizable tasks
**File**: `03_parallel_processing.py`

Run code analysis, security scanning, and performance checks simultaneously.

**Key Concepts:**

- Parallel execution
- Result aggregation
- Performance optimization

### Part 4: Specialisation - Multi-Agent Supervisor

**Pattern**: Supervisor with specialized agents
**When to use**: Complex tasks requiring domain expertise
**File**: `04_supervisor_agents.py`

A supervisor coordinates specialized agents: security expert, performance analyst, code quality checker.

**Key Concepts:**

- Agent specialization
- Supervisor pattern
- Dynamic agent selection

### Part 5: Reliability - Evaluator-Optimizer Loop

**Pattern**: Continuous improvement through feedback
**When to use**: When output quality can be iteratively improved
**File**: `05_evaluator_optimizer.py`

Add a feedback loop where an evaluator scores outputs and provides improvement suggestions.

**Key Concepts:**

- Feedback loops
- Quality assessment
- Iterative refinement

### Part 6: Production Readiness

**Pattern**: Error handling, persistence, monitoring
**When to use**: Real-world deployment
**File**: `06_production_ready.py`

Add error handling, state persistence, human-in-the-loop, and monitoring.

**Key Concepts:**

- Error recovery
- State persistence
- Human oversight
- Monitoring and debugging

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
| Supervisor          | Complex, specialized tasks | Simple workflows        |
| Evaluator-Optimizer | Improvable outputs         | Time-critical tasks     |

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
- **Evaluator-Optimizer**: AI content generation

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
