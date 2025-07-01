import os
import re
import datetime
import time
import functools
from typing import Dict, Any, Callable


def extract_code_from_response(response_text: str) -> str:
    if not response_text:
        return ""

    code_block_pattern = r'```(?:python)?\s*(.*?)\s*```'
    match = re.search(code_block_pattern, response_text, re.DOTALL)
    return match.group(1).strip() if match else response_text.strip()


def sanitise_filename(text: str) -> str:
    sanitised = re.sub(r'[^\w\s-]', '', text).strip()
    return re.sub(r'[-\s]+', '_', sanitised).lower()


def time_agent_execution(func: Callable) -> Callable:
    """
    Decorator to time agent execution. Pre-built utility for workshop exercises.

    Usage:
        @time_agent_execution
        def my_agent(state):
            # agent logic
            return state
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"🔄 Starting {func.__name__}...")
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        print(f"✅ {func.__name__} completed in {execution_time:.2f}s")
        return result
    return wrapper


def log_workflow_step(step_name: str, details: str = "") -> None:
    """
    Simple logging utility for workflow steps. Pre-built utility for workshop exercises.

    Usage:
        log_workflow_step("agent_started", "Processing user input")
        log_workflow_step("agent_completed", "Generated 150 lines of code")
    """
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] {step_name}"
    if details:
        message += f": {details}"
    print(f"📝 {message}")


def create_workflow_summary(metrics: Dict[str, Any]) -> str:
    """
    Create a formatted summary of workflow execution. Pre-built utility for workshop exercises.

    Usage:
        summary = create_workflow_summary({
            "total_time": 25.4,
            "agents_used": ["coder", "reviewer", "refactorer"],
            "iterations": 3
        })
    """
    summary_lines = ["=" * 50, "🎯 WORKFLOW EXECUTION SUMMARY", "=" * 50]

    for key, value in metrics.items():
        if key == "total_time":
            summary_lines.append(f"⏱️  Total execution time: {value:.2f}s")
        elif key == "agents_used":
            summary_lines.append(f"🤖 Agents involved: {', '.join(value)}")
        elif key == "iterations":
            summary_lines.append(f"🔄 Iterations completed: {value}")
        else:
            summary_lines.append(f"📊 {key}: {value}")

    summary_lines.append("=" * 50)
    return "\n".join(summary_lines)


class CodebaseGenerator:
    def __init__(self, pattern_name: str, task: str):
        self.pattern_name = pattern_name
        self.task = task
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.folder_name = f"generated/{pattern_name}_{self.timestamp}"

    def create_folder(self) -> str:
        os.makedirs(self.folder_name, exist_ok=True)
        return self.folder_name

    def write_python_file(self, filename: str, content: str) -> None:
        code = extract_code_from_response(content)
        if code:
            filepath = os.path.join(self.folder_name, f"{filename}.py")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)

    def write_text_file(self, filename: str, content: str) -> None:
        filepath = os.path.join(self.folder_name, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


class SequentialCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        self.write_python_file("original_code", result.get('code', ''))
        self.write_python_file(
            "refactored_code", result.get('refactored_code', ''))

        if result.get('tests'):
            self.write_python_file("tests", result.get('tests', ''))

        tests_section = ""
        if result.get('tests'):
            tests_section = f"""

## Unit Tests
```python
{extract_code_from_response(result.get('tests', 'No unit tests generated'))}
```"""

        files_generated = "- `original_code.py` - Initial implementation\n- `refactored_code.py` - Improved version based on review"
        if result.get('tests'):
            files_generated += "\n- `tests.py` - Comprehensive test suite"

        audit_content = f"""# Sequential Workflow Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Sequential Workflow

## Original Code
```python
{extract_code_from_response(result.get('code', 'No code generated'))}
```

## Review Feedback
{result.get('review', 'No review available')}

## Refactored Code
```python
{extract_code_from_response(result.get('refactored_code', 'No refactored code available'))}
```{tests_section}

## Files Generated
{files_generated}

---
*Generated using LangGraph Sequential Workflow Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(f"✅ Sequential codebase created in: {self.folder_name}/")


class ConditionalCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()
        self.write_python_file("generated_code", result.get('code', ''))

        # Exercise 1: Database expert detection
        route_decision = result.get("route_decision", "unknown")
        route_decisions = result.get("route_decisions", [route_decision])
        specialist_analysis = result.get("specialist_analysis", "")
        final_report = result.get("final_report", "")

        # Exercise 2: Smart routing - check if task description was used
        smart_routing_used = "input" in str(result.get(
            "router_debug", "")) or len(route_decisions) > 1

        # Exercise 3: Multi-expert routing detection
        multiple_experts = len(route_decisions) > 1
        experts_consulted = []

        # Collect all expert analyses
        expert_analyses = []
        if result.get("security_analysis"):
            experts_consulted.append("Security")
            expert_analyses.append(
                f"### Security Expert Analysis\n{result['security_analysis']}")
        if result.get("performance_analysis"):
            experts_consulted.append("Performance")
            expert_analyses.append(
                f"### Performance Expert Analysis\n{result['performance_analysis']}")
        if result.get("database_analysis"):
            experts_consulted.append("Database")
            expert_analyses.append(
                f"### Database Expert Analysis\n{result['database_analysis']}")
        if result.get("general_analysis"):
            experts_consulted.append("General")
            expert_analyses.append(
                f"### General Expert Analysis\n{result['general_analysis']}")

        # Build specialist section with enhanced information
        if multiple_experts and expert_analyses:
            specialist_section = f"""
## Multi-Expert Analysis
**Experts Consulted:** {', '.join(experts_consulted)}

{chr(10).join(expert_analyses)}"""
        elif specialist_analysis:
            specialist_section = f"""
## Specialist Analysis ({route_decision.title()} Expert)
{specialist_analysis}"""
        else:
            specialist_section = ""

        recommendations_section = ""
        if final_report:
            recommendations_section = f"""
## Final Recommendations
{final_report}"""

        # Exercise enhancements section
        enhancements_section = ""
        if multiple_experts or smart_routing_used or result.get("database_analysis"):
            enhancements_section = f"""
## Exercise Implementations Detected
"""
            if result.get("database_analysis"):
                enhancements_section += "- ✅ **Exercise 1**: Database expert added and utilized\n"
            if smart_routing_used:
                enhancements_section += "- ✅ **Exercise 2**: Smart routing considers task description + code content\n"
            if multiple_experts:
                enhancements_section += f"- ✅ **Exercise 3**: Multi-expert routing ({len(experts_consulted)} experts consulted)\n"

        # Dynamic workflow execution based on what was implemented
        workflow_steps = [
            "1. **Coder Agent** → Generated initial code",
            "2. **Router Agent** → Analyzed content" +
            (" and task description" if smart_routing_used else "") +
            f" and selected expert(s)"
        ]

        if multiple_experts:
            workflow_steps.append(
                f"3. **Multiple Experts** → {', '.join(experts_consulted)} experts provided specialized analysis")
        else:
            workflow_steps.append(
                f"3. **{route_decision.title()} Expert** → Provided domain-specific analysis")

        workflow_steps.append(
            "4. **Synthesis Agent** → Created final integrated recommendations")

        # Dynamic routing flow
        if multiple_experts:
            routing_flow = f"Coder → Router → [{', '.join(experts_consulted)} Experts] → Synthesis"
        else:
            routing_flow = f"Coder → Router → {route_decision.title()} Expert → Synthesis"

        files_generated = "- `generated_code.py` - Code routed through specialist review"

        audit_content = f"""# Conditional Routing Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Task:** {self.task}
**Pattern:** Conditional Routing
**Routing Strategy:** {"Multi-expert routing" if multiple_experts else "Single expert routing"}

## Generated Code
```python
{extract_code_from_response(result.get('code', 'No code generated'))}
```

## Routing Decision
**Primary Expert:** {route_decision}
**All Routes:** {', '.join(route_decisions) if multiple_experts else route_decision}{specialist_section}{recommendations_section}{enhancements_section}

## Workflow Execution
{chr(10).join(workflow_steps)}

## Routing Flow
```
{routing_flow}
```

## Files Generated
{files_generated}

---
*Generated using LangGraph Conditional Routing Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(
            f"✅ Conditional routing codebase created in: {self.folder_name}/")


class ParallelCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        self.write_python_file("main_code", result.get('code', ''))

        synthesis_content = f"""# Code Analysis Synthesis Report

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Analysis Method:** Parallel Expert Review

## Executive Summary

{result.get('final_report', 'No synthesis report available')}

---
*Generated using LangGraph Parallel Processing Pattern*
"""
        self.write_text_file("SYNTHESIS_REPORT.md", synthesis_content)

        documentation_section = ""
        if result.get('documentation_analysis'):
            documentation_section = f"""

### Documentation Analysis
{result.get('documentation_analysis', 'No documentation analysis available')}"""

        audit_content = f"""# Parallel Processing Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Parallel Processing

## Generated Code
```python
{extract_code_from_response(result.get('code', 'No code generated'))}
```

## Expert Analysis Reports

### Security Analysis
{result.get('security_analysis', 'No security analysis available')}

### Performance Analysis
{result.get('performance_analysis', 'No performance analysis available')}

### Style Analysis
{result.get('style_analysis', 'No style analysis available')}{documentation_section}

## Files Generated
- `main_code.py` - Analysed implementation
- `SYNTHESIS_REPORT.md` - **KEY DELIVERABLE:** Aggregated expert recommendations

---
*Generated using LangGraph Parallel Processing Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(
            f"✅ Parallel processing codebase created in: {self.folder_name}/")
        print(f"📊 Key deliverable: {self.folder_name}/SYNTHESIS_REPORT.md")


class SupervisorCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        self.write_python_file("main_code", result.get('code', ''))

        task_analysis_section = ""
        if result.get('task_type'):
            task_analysis_section = f"""

## Task Analysis
- **Task Type:** {result['task_type']}
- **Routing Strategy:** {'Priority security routing' if result['task_type'] == 'authentication' else 'Standard expert routing'}"""

        final_analysis_content = f"""# Expert Analysis & Recommendations

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Analysis Method:** Supervised Expert Consultation{task_analysis_section}

## Executive Summary

{result.get('final_analysis', 'No final analysis available')}

## Expert Consultation Process

**Agents Consulted:** {', '.join(result.get('completed_agents', []))}

### Supervisor Decision Log
{result.get('supervisor_notes', 'No supervisor decisions recorded')}

---
*Generated using LangGraph Supervisor Agents Pattern*
"""
        self.write_text_file("EXPERT_ANALYSIS.md", final_analysis_content)

        completed_agents = result.get('completed_agents', [])
        reports_section = ""

        if result.get('security_report'):
            context_note = " (with quality context)" if result.get(
                'quality_report') else ""
            reports_section += f"### Security Expert Report{context_note}\n{result['security_report']}\n\n"
        if result.get('quality_report'):
            reports_section += f"### Quality Expert Report\n{result['quality_report']}\n\n"
        if result.get('database_report'):
            reports_section += f"### Database Expert Report\n{result['database_report']}\n\n"

        supervisor_notes = "Supervisor coordinated expert consultation based on task analysis and code content."
        if result.get('task_type') == 'authentication':
            supervisor_notes += " Priority routing applied for authentication task - security expert consulted first."
        if result.get('database_report'):
            supervisor_notes += " Database expert added based on code analysis showing SQL/database operations."

        smart_routing_section = ""
        if result.get('database_report') or result.get('task_type') == 'authentication':
            smart_routing_section = f"""

## Smart Routing Features
- **Content-based routing:** Database expert consulted based on code analysis
- **Task-type prioritisation:** {'Security-first routing for authentication tasks' if result.get('task_type') == 'authentication' else 'Standard routing applied'}
- **Expert collaboration:** Security expert reviewed quality findings"""

        audit_content = f"""# Supervisor Agents Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Supervisor Agents
**Agents Consulted:** {', '.join(completed_agents)}

## Generated Code
```python
{extract_code_from_response(result.get('code', 'No code generated'))}
```

## Supervisor Decision Process
{supervisor_notes}

## Individual Expert Reports

{reports_section}{smart_routing_section}

## Files Generated
- `main_code.py` - Expert-reviewed implementation  
- `EXPERT_ANALYSIS.md` - **KEY DELIVERABLE:** Synthesised expert recommendations

---
*Generated using LangGraph Supervisor Agents Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(f"✅ Supervisor agents codebase created in: {self.folder_name}/")
        print(f"🎯 Key deliverable: {self.folder_name}/EXPERT_ANALYSIS.md")


class EvaluatorCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        # Write final code
        self.write_python_file("final_code", result.get(
            'final_code', result.get('code', '')))

        final_score = result.get('score', 'N/A')
        iteration_count = result.get('iteration_count', 0)
        code_list = result.get('code', [])
        scores = result.get('scores', [])

        # Write each iteration as separate Python file
        files_generated = "- `final_code.py` - Iteratively optimised implementation"
        if isinstance(code_list, list) and len(code_list) > 0:
            for i, code_version in enumerate(code_list):
                if i == 0:
                    filename = "initial_code"
                    files_generated += f"\n- `initial_code.py` - Original implementation"
                else:
                    filename = f"iteration_{i}"
                    files_generated += f"\n- `iteration_{i}.py` - Iteration {i} improvement"

                self.write_python_file(filename, code_version)

        # Determine completion reason
        completion_reason = "Max iterations reached" if iteration_count >= 3 else "Quality threshold reached"

        # Build iterations section
        iterations_section = ""
        if isinstance(code_list, list) and len(code_list) > 1:
            iterations_section = "\n## Code Evolution\n\n"
            for i, code_version in enumerate(code_list):
                iteration_label = "Initial Code" if i == 0 else f"Iteration {i}"
                score_info = ""
                if i < len(scores):
                    score_info = f" (Score: {scores[i]}/10)"

                iterations_section += f"""### {iteration_label}{score_info}
```python
{extract_code_from_response(code_version)}
```

"""

        history_section = f"""## Optimisation Summary
- **Total Iterations:** {iteration_count}
- **Final Quality Score:** {final_score}/10
- **Completion Reason:** {completion_reason}

"""

        audit_content = f"""# Evaluator-Optimiser Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Evaluator-Optimiser
**Total Iterations:** {iteration_count}
**Final Score:** {final_score}/10

## Final Code
```python
{extract_code_from_response(result.get('final_code', result.get('code', 'No code generated')))}
```

{history_section}{iterations_section}## Files Generated
{files_generated}

---
*Generated using LangGraph Evaluator-Optimiser Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(
            f"✅ Evaluator-optimiser codebase created in: {self.folder_name}/")


class OrchestratorCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        self.write_python_file("final_code", result.get('final_result', ''))

        subtasks_section = ""
        if result.get('subtasks'):
            subtasks_section = "\n## Task Breakdown\n\n"
            for i, subtask in enumerate(result['subtasks'], 1):
                if isinstance(subtask, dict):
                    deps = ", ".join(subtask.get('dependencies', [])) if subtask.get(
                        'dependencies') else "None"
                    priority = subtask.get('priority', 'N/A')
                    subtasks_section += f"""### Subtask {i}: {subtask.get('name', f'Task {i}')}
**Type:** {subtask.get('type', 'Unknown')}  
**Priority:** {priority}  
**Dependencies:** {deps}  
**Description:** {subtask.get('description', 'No description')}

"""
                else:
                    subtasks_section += f"""### Subtask {i}
{subtask}

"""

        worker_specialisation_section = ""
        worker_types = set()
        if result.get('worker_outputs'):
            for output in result['worker_outputs']:
                if output.startswith('FRONTEND'):
                    worker_types.add('Frontend')
                elif output.startswith('BACKEND'):
                    worker_types.add('Backend')
                elif output.startswith('DATABASE'):
                    worker_types.add('Database')
                elif output.startswith('TESTING'):
                    worker_types.add('Testing')

        if worker_types:
            worker_specialisation_section = f"""

## Worker Specialisation
**Specialised workers used:** {', '.join(sorted(worker_types))}"""

        dependency_handling_section = ""
        if result.get('subtasks') and any(subtask.get('dependencies') for subtask in result.get('subtasks', [])):
            dependency_handling_section = f"""

## Dependency Management
**Dependency-aware execution:** Subtasks executed in correct order based on dependencies"""

        # Exercise detection logic
        exercise_1_completed = False
        exercise_2_completed = False
        exercise_3_completed = False

        # Exercise 1: Smart task detection - check if subtasks have diverse types
        if result.get('subtasks'):
            task_types = set()
            for subtask in result['subtasks']:
                if isinstance(subtask, dict) and subtask.get('type'):
                    task_types.add(subtask['type'])
            # Consider completed if we have specialized types beyond just 'implementation'
            specialized_types = task_types - \
                {'implementation', 'testing', 'documentation'}
            if specialized_types or len(task_types) > 2:
                exercise_1_completed = True

        # Exercise 2: Worker specialisation - check if worker outputs use specialized prefixes
        if worker_types:  # worker_types was calculated earlier from output prefixes
            exercise_2_completed = True

        # Exercise 3: Dependency handling - check if subtasks have dependencies
        if result.get('subtasks') and any(subtask.get('dependencies') for subtask in result.get('subtasks', [])):
            exercise_3_completed = True

        # Exercise enhancements section
        enhancements_section = ""
        if exercise_1_completed or exercise_2_completed or exercise_3_completed:
            enhancements_section = f"""

## Exercise Implementations Detected
"""
            if exercise_1_completed:
                task_type_list = list(
                    task_types) if 'task_types' in locals() else []
                enhancements_section += f"- ✅ **Exercise 1**: Smart task detection implemented (task types: {', '.join(task_type_list)})\n"
            if exercise_2_completed:
                enhancements_section += f"- ✅ **Exercise 2**: Worker specialisation implemented ({', '.join(sorted(worker_types))} workers)\n"
            if exercise_3_completed:
                enhancements_section += "- ✅ **Exercise 3**: Dependency handling implemented\n"

        worker_outputs_section = ""
        if result.get('worker_outputs'):
            worker_outputs_section = "\n## Worker Outputs\n\n"
            for i, output in enumerate(result['worker_outputs'], 1):
                worker_outputs_section += f"""### Worker {i} Output
```python
{extract_code_from_response(output)}
```

"""

        orchestrator_report = f"""# Orchestrator Process Report

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Analysis Method:** Dynamic Task Decomposition{worker_specialisation_section}{dependency_handling_section}{enhancements_section}

## Executive Summary

The orchestrator successfully broke down the complex task into {len(result.get('subtasks', []))} manageable subtasks, executed them through specialised workers, and synthesised the results into a cohesive solution.

## Process Overview

1. **Task Analysis**: Orchestrator analysed the input requirements
2. **Dynamic Decomposition**: Created {len(result.get('subtasks', []))} specialised subtasks
3. **Dependency Resolution**: Executed subtasks in correct order
4. **Specialised Execution**: Workers processed subtasks independently
5. **Result Synthesis**: Combined worker outputs into final solution

{subtasks_section}

---
*Generated using LangGraph Orchestrator-Worker Pattern*
"""
        self.write_text_file("ORCHESTRATOR_REPORT.md", orchestrator_report)

        audit_content = f"""# Orchestrator-Worker Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Orchestrator-Worker
**Subtasks Created:** {len(result.get('subtasks', []))}
**Workers Executed:** {len(result.get('worker_outputs', []))}

## Final Code
```python
{extract_code_from_response(result.get('final_result', 'No code generated'))}
```

{subtasks_section}{enhancements_section}{worker_outputs_section}## Files Generated
- `final_code.py` - Synthesised final implementation
- `ORCHESTRATOR_REPORT.md` - **KEY DELIVERABLE:** Orchestration process breakdown

---
*Generated using LangGraph Orchestrator-Worker Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(
            f"✅ Orchestrator-worker codebase created in: {self.folder_name}/")
        print(f"🎯 Key deliverable: {self.folder_name}/ORCHESTRATOR_REPORT.md")


class ProductionCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        self.write_python_file("production_code", result.get(
            'refactored_code', result.get('code', '')))

        metrics_section = f"""## Production Metrics
- **Session ID:** {result.get('session_id', 'N/A')}
- **Execution Time:** {result.get('execution_time', 0):.2f}s
- **Retry Count:** {result.get('retry_count', 0)}
- **Human Approval Required:** {result.get('human_approval_needed', False)}
"""

        audit_content = f"""# Production Ready Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Production Ready

## Production Code
```python
{extract_code_from_response(result.get('refactored_code', result.get('code', 'No code generated')))}
```

{metrics_section}

## Review Feedback
{result.get('review', 'No review available')}

## Files Generated
- `production_code.py` - Production-ready implementation

---
*Generated using LangGraph Production Ready Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(f"✅ Production ready codebase created in: {self.folder_name}/")
