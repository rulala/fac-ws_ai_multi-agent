import os
import re
import datetime
from typing import Dict,  Any


def extract_code_from_response(response_text: str) -> str:
    """Extract Python code from markdown code blocks or return raw text."""
    if not response_text:
        return ""

    code_block_pattern = r'```(?:python)?\s*(.*?)\s*```'
    match = re.search(code_block_pattern, response_text, re.DOTALL)
    return match.group(1).strip() if match else response_text.strip()


def sanitise_filename(text: str) -> str:
    """Convert text to safe filename."""
    sanitised = re.sub(r'[^\w\s-]', '', text).strip()
    return re.sub(r'[-\s]+', '_', sanitised).lower()


class CodebaseGenerator:
    def __init__(self, pattern_name: str, task: str):
        self.pattern_name = pattern_name
        self.task = task
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.folder_name = f"generated/{pattern_name}_{self.timestamp}"

    def create_folder(self) -> str:
        """Create timestamped folder for the codebase."""
        os.makedirs(self.folder_name, exist_ok=True)
        return self.folder_name

    def write_python_file(self, filename: str, content: str) -> None:
        """Write Python code to file, extracting from markdown if needed."""
        code = extract_code_from_response(content)
        if code:
            filepath = os.path.join(self.folder_name, f"{filename}.py")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)

    def write_text_file(self, filename: str, content: str) -> None:
        """Write raw text to file."""
        filepath = os.path.join(self.folder_name, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


class SequentialCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        self.write_python_file("original_code", result.get('code', ''))
        self.write_python_file(
            "refactored_code", result.get('refactored_code', ''))

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
```

## Files Generated
- `original_code.py` - Initial implementation
- `refactored_code.py` - Improved version based on review

---
*Generated using LangGraph Sequential Workflow Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(f"✅ Sequential codebase created in: {self.folder_name}/")


class ConditionalCodebase(CodebaseGenerator):
    def generate(self, result: Dict[str, Any]) -> None:
        self.create_folder()

        code_list = result.get('code', [''])
        if isinstance(code_list, str):
            code_list = [code_list]

        final_code = code_list[-1] if code_list else ''
        self.write_python_file("final_code", final_code)

        previous_iterations_section = ""
        if len(code_list) > 1:
            previous_iterations_section = "\n## Previous Iterations\n\n"
            for i, code_version in enumerate(code_list[:-1]):
                iteration_label = "Original Code" if i == 0 else f"Iteration {i}"
                previous_iterations_section += f"""### {iteration_label}
```python
{extract_code_from_response(code_version)}
```

"""

        audit_content = f"""# Conditional Routing Audit Trail

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Pattern:** Conditional Routing
**Final Quality Score:** {result.get('quality_score', 'N/A')}/10
**Iterations:** {result.get('iteration_count', 0)}

## Final Code
```python
{extract_code_from_response(final_code)}
```

## Review Feedback
{result.get('review', 'No review available')}

## Quality Metrics
- **Score:** {result.get('quality_score', 'N/A')}/10
- **Iterations:** {result.get('iteration_count', 0)}
- **Threshold:** 7/10
{previous_iterations_section}
## Files Generated
- `final_code.py` - Quality-approved implementation

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

        # Create separate synthesis report file
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
{result.get('style_analysis', 'No style analysis available')}

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

        # Create separate final analysis file
        final_analysis_content = f"""# Expert Analysis & Recommendations

**Generated:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Task:** {self.task}  
**Analysis Method:** Supervised Expert Consultation

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
            reports_section += f"### Security Expert Report\n{result['security_report']}\n\n"
        if result.get('performance_report'):
            reports_section += f"### Performance Expert Report\n{result['performance_report']}\n\n"
        if result.get('quality_report'):
            reports_section += f"### Quality Expert Report\n{result['quality_report']}\n\n"

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
{result.get('supervisor_notes', 'No supervisor notes available')}

## Individual Expert Reports

{reports_section}## Files Generated
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

        self.write_python_file("final_code", result.get(
            'final_code', result.get('code', '')))

        # Handle simplified evaluation structure
        current_eval = result.get('current_evaluation', {})
        final_score = current_eval.get('score', 'N/A')
        final_feedback = current_eval.get('feedback', 'No feedback available')
        iteration_count = result.get('iteration_count', 0)

        # Create simple iteration history section
        history_section = f"""## Optimisation Summary
- **Total Iterations:** {iteration_count}
- **Final Quality Score:** {final_score}/10
- **Final Feedback:** {final_feedback}
- **Completion Reason:** {'Quality threshold reached' if final_score >= 8 else 'Max iterations reached' if iteration_count >= 3 else 'Evaluator determined completion'}

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

{history_section}## Files Generated
- `final_code.py` - Iteratively optimised implementation

---
*Generated using LangGraph Evaluator-Optimiser Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(
            f"✅ Evaluator-optimiser codebase created in: {self.folder_name}/")


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

{error_section}## Files Generated
- `production_code.py` - Production-ready implementation

---
*Generated using LangGraph Production Ready Pattern*
"""
        self.write_text_file("AUDIT_TRAIL.md", audit_content)
        print(f"✅ Production ready codebase created in: {self.folder_name}/")
