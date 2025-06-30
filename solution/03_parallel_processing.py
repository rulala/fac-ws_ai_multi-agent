from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv
from utils import ParallelCodebase

load_dotenv()


class CodeAnalysisState(TypedDict):
    input: str
    code: str
    security_analysis: str
    performance_analysis: str
    style_analysis: str
    documentation_analysis: str
    general_fallback_analysis: str
    final_report: str
    failed_agents: list


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

security_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Expert. Analyse code for security vulnerabilities, input validation, and potential attack vectors."),
    ("human", "Analyse this code for security issues:\n{code}")
])

performance_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Performance Expert. Analyse code for efficiency, algorithmic complexity, and optimisation opportunities."),
    ("human", "Analyse this code for performance issues:\n{code}")
])

style_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Code Style Expert. Analyse code for PEP 8 compliance, naming conventions, and code organisation."),
    ("human", "Analyse this code for style and readability issues:\n{code}")
])

documentation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Documentation Expert. Generate comprehensive docstrings, comments, and documentation for code."),
    ("human", "Generate documentation and docstrings for this code:\n{code}")
])

general_fallback_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a General Code Expert providing fallback analysis. Provide comprehensive code review covering all aspects."),
    ("human", "Provide general analysis for this code (fallback mode):\n{code}")
])

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Technical Lead. Synthesise analysis reports into actionable recommendations with priorities. IMPORTANT: Give security recommendations 2x weight in your final prioritization."),
    ("human", "Analysis Reports:\n{all_analyses}\n\nFailed Agents (if any): {failed_agents}\n\nProvide weighted recommendations with security issues prioritized:")
])


def coder_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content}


def security_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    try:
        response = llm.invoke(security_prompt.format_messages(code=state["code"]))
        print("🔒 Security analysis completed")
        return {"security_analysis": response.content}
    except Exception as e:
        print(f"⚠️ Security agent failed: {e}")
        failed_agents = state.get("failed_agents", [])
        failed_agents.append("security")
        return {"failed_agents": failed_agents}


def performance_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    try:
        response = llm.invoke(performance_prompt.format_messages(code=state["code"]))
        print("⚡ Performance analysis completed")
        return {"performance_analysis": response.content}
    except Exception as e:
        print(f"⚠️ Performance agent failed: {e}")
        failed_agents = state.get("failed_agents", [])
        failed_agents.append("performance")
        return {"failed_agents": failed_agents}


def style_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    try:
        response = llm.invoke(style_prompt.format_messages(code=state["code"]))
        print("🎨 Style analysis completed")
        return {"style_analysis": response.content}
    except Exception as e:
        print(f"⚠️ Style agent failed: {e}")
        failed_agents = state.get("failed_agents", [])
        failed_agents.append("style")
        return {"failed_agents": failed_agents}

def documentation_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    try:
        response = llm.invoke(documentation_prompt.format_messages(code=state["code"]))
        print("📝 Documentation analysis completed")
        return {"documentation_analysis": response.content}
    except Exception as e:
        print(f"⚠️ Documentation agent failed: {e}")
        failed_agents = state.get("failed_agents", [])
        failed_agents.append("documentation")
        return {"failed_agents": failed_agents}

def general_fallback_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    try:
        response = llm.invoke(general_fallback_prompt.format_messages(code=state["code"]))
        print("🔄 General fallback analysis completed")
        return {"general_fallback_analysis": response.content}
    except Exception as e:
        print(f"⚠️ General fallback agent failed: {e}")
        return {"general_fallback_analysis": "Fallback analysis unavailable"}


def synthesis_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    # Collect all available analyses
    analyses = []
    failed_agents = state.get("failed_agents", [])
    
    # Add security analysis with 2x weight emphasis
    if state.get("security_analysis"):
        analyses.append(f"SECURITY ANALYSIS (HIGH PRIORITY - 2X WEIGHT):\n{state['security_analysis']}")
    elif "security" in failed_agents:
        analyses.append("SECURITY ANALYSIS: FAILED - HIGH PRIORITY ISSUE")
    
    if state.get("performance_analysis"):
        analyses.append(f"Performance Analysis:\n{state['performance_analysis']}")
    elif "performance" in failed_agents:
        analyses.append("Performance Analysis: FAILED")
    
    if state.get("style_analysis"):
        analyses.append(f"Style Analysis:\n{state['style_analysis']}")
    elif "style" in failed_agents:
        analyses.append("Style Analysis: FAILED")
    
    if state.get("documentation_analysis"):
        analyses.append(f"Documentation Analysis:\n{state['documentation_analysis']}")
    elif "documentation" in failed_agents:
        analyses.append("Documentation Analysis: FAILED")
    
    # Add fallback analysis if any agents failed
    if failed_agents and state.get("general_fallback_analysis"):
        analyses.append(f"General Fallback Analysis (covering failed agents: {', '.join(failed_agents)}):\n{state['general_fallback_analysis']}")
    
    all_analyses = "\n\n".join(analyses)
    
    response = llm.invoke(synthesis_prompt.format_messages(
        all_analyses=all_analyses,
        failed_agents=", ".join(failed_agents) if failed_agents else "None"
    ))
    
    print(f"🎯 Weighted synthesis completed (Security 2x priority)")
    if failed_agents:
        print(f"🔄 Fallback analysis covered: {', '.join(failed_agents)}")
    
    return {"final_report": response.content}


def check_for_failures(state: CodeAnalysisState) -> str:
    """Check if any agents failed and route to fallback if needed"""
    failed_agents = state.get("failed_agents", [])
    if failed_agents:
        return "general_fallback"
    return "synthesis"


builder = StateGraph(CodeAnalysisState)
builder.add_node("coder", coder_agent)
builder.add_node("security_agent", security_agent)
builder.add_node("performance_agent", performance_agent)
builder.add_node("style_agent", style_agent)
builder.add_node("documentation_agent", documentation_agent)
builder.add_node("general_fallback", general_fallback_agent)
builder.add_node("synthesis", synthesis_agent)

# All experts run in parallel after coder
builder.add_edge(START, "coder")
builder.add_edge("coder", "security_agent")
builder.add_edge("coder", "performance_agent")
builder.add_edge("coder", "style_agent")
builder.add_edge("coder", "documentation_agent")

# All agents check for failures before proceeding
builder.add_conditional_edges(
    "security_agent",
    check_for_failures,
    {
        "general_fallback": "general_fallback",
        "synthesis": "synthesis"
    }
)
builder.add_conditional_edges(
    "performance_agent",
    check_for_failures,
    {
        "general_fallback": "general_fallback",
        "synthesis": "synthesis"
    }
)
builder.add_conditional_edges(
    "style_agent",
    check_for_failures,
    {
        "general_fallback": "general_fallback",
        "synthesis": "synthesis"
    }
)
builder.add_conditional_edges(
    "documentation_agent",
    check_for_failures,
    {
        "general_fallback": "general_fallback",
        "synthesis": "synthesis"
    }
)

builder.add_edge("general_fallback", "synthesis")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a secure web API endpoint that processes user file uploads, validates them, and stores metadata in a database with proper error handling"

    print("Running parallel processing with fallback protection...")
    result = workflow.invoke({"input": task, "failed_agents": []})
    
    # Display results
    completed_analyses = []
    if result.get("security_analysis"): completed_analyses.append("Security")
    if result.get("performance_analysis"): completed_analyses.append("Performance")
    if result.get("style_analysis"): completed_analyses.append("Style")
    if result.get("documentation_analysis"): completed_analyses.append("Documentation")
    
    failed_agents = result.get("failed_agents", [])
    
    print(f"\n✅ Completed analyses: {', '.join(completed_analyses)}")
    if failed_agents:
        print(f"🔄 Failed agents (fallback used): {', '.join(failed_agents)}")
    print(f"⚖️ Security analysis weighted 2x in final recommendations")

    codebase = ParallelCodebase("03_parallel_processing", task)
    codebase.generate(result)

    print("=== PARALLEL WORKFLOW WITH FALLBACK COMPLETED ===")
