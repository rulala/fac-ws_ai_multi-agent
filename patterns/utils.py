import os
import re
import datetime
import shutil
from typing import Dict, Any, Optional


def extract_code_from_response(response_text: str) -> str:
    if not response_text:
        return ""

    code_block_pattern = r'```(?:python)?\s*(.*?)\s*```'
    match = re.search(code_block_pattern, response_text, re.DOTALL)
    return match.group(1).strip() if match else response_text.strip()


def sanitise_filename(text: str) -> str:
    sanitised = re.sub(r'[^\w\s-]', '', text).strip()
    return re.sub(r'[-\s]+', '_', sanitised).lower()


def find_test_key(result: Dict[str, Any]) -> Optional[str]:
    """Return the first key containing 'test' if present."""
    for key in result:
        if 'test' in key.lower():
            return key
    return None


def find_compliance_key(result: Dict[str, Any]) -> Optional[str]:
    """Return the first key containing 'compliance' if present."""
    for key in result:
        if 'compliance' in key.lower():
            return key
    return None


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

        tests_key = find_test_key(result)
        if tests_key and result.get(tests_key):
            self.write_python_file("unit_tests", result.get(tests_key, ""))

        unit_tests_section = ""
        if tests_key and result.get(tests_key):
            unit_tests_section = f"""

## Unit Tests
```python
{extract_code_from_response(result.get(tests_key, 'No tests generated'))}
```"""

        files_generated = "- `original_code.py` - Initial implementation\n- `refactored_code.py` - Improved version based on review"
        if tests_key and result.get(tests_key):
            files_generated += "\n- `unit_tests.py` - Comprehensive test suite"

        performance_section = ""
        if 'performance_metrics' in str(result):
            performance_section = f"""

## Performance Metrics
Execution timing analysis available in debug output."""

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
```{unit_tests_section}{performance_section}

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

        route_decision = result.get("route_decision", "unknown")
        specialist_analysis = result.get("specialist_analysis", "")
        final_report = result.get("final_report", "")

        specialist_section = ""
        if specialist_analysis:
            specialist_section = f"""
## Specialist Analysis ({route_decision.title()} Expert)
{specialist_analysis}"""

        recommendations_section = ""
        if final_report:
            recommendations_section = f"""
## Final Recommendations
{final_report}"""

        files_generated = "- `generated_code.py` - Code routed through specialist review"

        audit_content = f"""# Conditional Routing Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Task:** {self.task}
**Pattern:** Conditional Routing

## Generated Code
```python
{extract_code_from_response(result.get('code', 'No code generated'))}
```

## Routing Decision
**Selected Expert:** {route_decision}{specialist_section}{recommendations_section}

## Workflow Execution
1. **Coder Agent** → Generated initial code
2. **Router Agent** → Analyzed content and selected `{route_decision}` expert
3. **{route_decision.title()} Expert** → Provided domain-specific analysis
4. **Synthesis Agent** → Created final recommendations

## Routing Flow
```
Coder → Router → {route_decision.title()} Expert → Synthesis
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

        performance_comparison = ""
        if result.get('sequential_time') and result.get('parallel_time'):
            seq_time = result['sequential_time']
            par_time = result['parallel_time']
            speedup = seq_time / par_time if par_time > 0 else 0
            performance_comparison = f"""

## Performance Analysis
- **Sequential execution:** {seq_time:.2f}s
- **Parallel execution:** {par_time:.2f}s  
- **Speedup achieved:** {speedup:.2f}x"""

        synthesis_content = f"""# Code Analysis Synthesis Report

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Analysis Method:** Parallel Expert Review{performance_comparison}

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

        error_handling_section = ""
        if any("failed" in str(result.get(key, "")) for key in ['security_analysis', 'performance_analysis', 'style_analysis', 'documentation_analysis']):
            error_handling_section = f"""

## Error Handling
Some agents encountered errors during execution but the workflow continued gracefully."""

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
{result.get('style_analysis', 'No style analysis available')}{documentation_section}{error_handling_section}

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

        final_score = result.get('quality_score', 'N/A')
        iteration_count = result.get('iteration_count', 0)
        code_list = result.get('code', [])
        quality_scores = result.get('quality_scores', [])

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
        completion_reason = "Quality threshold reached"
        if iteration_count >= 3:
            completion_reason = "Max iterations reached"
        elif final_score >= 7:
            completion_reason = "Quality threshold reached"
        else:
            completion_reason = "Optimization complete"

        # Build iterations section
        iterations_section = ""
        if isinstance(code_list, list) and len(code_list) > 1:
            iterations_section = "\n## Code Evolution\n\n"
            for i, code_version in enumerate(code_list):
                iteration_label = "Initial Code" if i == 0 else f"Iteration {i}"
                score_info = ""
                if i < len(quality_scores):
                    score_info = f" (Score: {quality_scores[i]}/10)"

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

        validation_section = ""
        if result.get('validation_result'):
            validation = result['validation_result']
            validation_section = f"""

## Integration Validation
- **Can combine:** {validation.get('can_combine', 'Unknown')}
- **Issues found:** {len(validation.get('issues', []))}
- **Suggestions:** {len(validation.get('suggestions', []))}"""

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
**Analysis Method:** Dynamic Task Decomposition{worker_specialisation_section}{dependency_handling_section}{validation_section}

## Executive Summary

The orchestrator successfully broke down the complex task into {len(result.get('subtasks', []))} manageable subtasks, executed them through specialised workers, and synthesised the results into a cohesive solution.

## Process Overview

1. **Task Analysis**: Orchestrator analysed the input requirements
2. **Dynamic Decomposition**: Created {len(result.get('subtasks', []))} specialised subtasks
3. **Dependency Resolution**: Executed subtasks in correct order
4. **Specialised Execution**: Workers processed subtasks independently
5. **Integration Validation**: Checked compatibility before synthesis
6. **Result Synthesis**: Combined worker outputs into final solution

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

{subtasks_section}{worker_outputs_section}## Files Generated
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

        error_section = ""
        if result.get('error_log'):
            error_section = f"""## Error Log
```
{result['error_log']}
```

"""

        compliance_section = ""
        compliance_key = find_compliance_key(result)
        if compliance_key and result.get(compliance_key):
            compliance_section = f"""## Compliance Report
{result[compliance_key]}"""

        if result.get('workflow_log') and os.path.exists(result['workflow_log']):
            shutil.copy(result['workflow_log'], os.path.join(self.folder_name, 'workflow.log'))
            log_line = "\n- `workflow.log` - Execution trace"
        else:
            log_line = ""

        audit_content = f"""# Production Ready Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Production Ready

## Production Code
```python
{extract_code_from_response(result.get('refactored_code', result.get('code', 'No code generated')))}
```

{metrics_section}

{compliance_section}

## Review Feedback
{result.get('review', 'No review available')}

{error_section}## Files Generated
- `production_code.py` - Production-ready implementation{log_line}

---
*Generated using LangGraph Production Ready Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(f"✅ Production ready codebase created in: {self.folder_name}/")
