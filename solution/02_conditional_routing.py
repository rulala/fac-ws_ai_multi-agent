from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal, List
from dotenv import load_dotenv
from utils import ConditionalCodebase

load_dotenv()


class CodeAnalysisState(TypedDict):
    input: str
    code: str
    route_decision: str
    route_decisions: List[str]  # For multi-expert routing
    specialist_analysis: str
    database_analysis: str
    security_analysis: str
    performance_analysis: str
    general_analysis: str
    final_report: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write clean Python code, and ONLY output the Python code."),
    ("human", "{input}")
])

router_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an Intelligent Router. Analyze both the task description AND the code content to determine which experts should review it. Consider:\n- Security issues (auth, validation, encryption)\n- Performance concerns (algorithms, scalability)\n- Database operations (SQL, schema, queries)\n- General code quality\n\nFor complex code with multiple concerns, you can route to multiple experts. Respond with a comma-separated list from: 'security', 'performance', 'database', 'general'."),
    ("human", "Task: {input}\n\nCode to route:\n{code}")
])

security_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Expert. Focus on vulnerabilities, authentication, authorization, input validation, and secure coding practices."),
    ("human", "Provide security analysis for:\n{code}")
])

performance_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Performance Expert. Focus on algorithmic complexity, optimization, resource usage, and scalability."),
    ("human", "Provide performance analysis for:\n{code}")
])

general_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a General Code Expert. Focus on code quality, maintainability, readability, and best practices."),
    ("human", "Provide general code analysis for:\n{code}")
])

database_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Database Expert. Focus on SQL optimization, schema design, query performance, data integrity, and database security."),
    ("human", "Provide database analysis for:\n{code}")
])

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Technical Lead. Synthesize multiple specialist analyses into comprehensive actionable recommendations."),
    ("human",
     "Expert Analyses:\n{all_analyses}\n\nRouted to: {experts_consulted}\n\nProvide final integrated recommendations:")
])


def coder_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content}


def router_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(router_prompt.format_messages(
        input=state["input"],
        code=state["code"]
    ))

    # Parse multiple routes
    routes_text = response.content.strip().lower()
    routes = [r.strip() for r in routes_text.split(',')]

    # Validate routes
    valid_routes = []
    for route in routes:
        if route in ["security", "performance", "database", "general"]:
            valid_routes.append(route)

    # Default to general if no valid routes
    if not valid_routes:
        valid_routes = ["general"]

    print(f"🎯 Router decision: {', '.join(valid_routes)}")
    return {"route_decision": valid_routes[0], "route_decisions": valid_routes}


def security_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        security_expert_prompt.format_messages(code=state["code"]))
    print("🔒 Security expert analyzing code")
    return {"security_analysis": response.content}


def performance_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        performance_expert_prompt.format_messages(code=state["code"]))
    print("⚡ Performance expert analyzing code")
    return {"performance_analysis": response.content}


def general_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        general_expert_prompt.format_messages(code=state["code"]))
    print("📋 General expert analyzing code")
    return {"general_analysis": response.content}


def database_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        database_expert_prompt.format_messages(code=state["code"]))
    print("🗄️ Database expert analyzing code")
    return {"database_analysis": response.content}


def synthesis_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    # Collect all available analyses
    analyses = []
    experts_used = []

    if state.get("security_analysis"):
        analyses.append(f"Security Analysis:\n{state['security_analysis']}")
        experts_used.append("security")

    if state.get("performance_analysis"):
        analyses.append(
            f"Performance Analysis:\n{state['performance_analysis']}")
        experts_used.append("performance")

    if state.get("database_analysis"):
        analyses.append(f"Database Analysis:\n{state['database_analysis']}")
        experts_used.append("database")

    if state.get("general_analysis"):
        analyses.append(f"General Analysis:\n{state['general_analysis']}")
        experts_used.append("general")

    # Fallback to any specialist_analysis for backward compatibility
    if not analyses and state.get("specialist_analysis"):
        analyses.append(
            f"Specialist Analysis:\n{state['specialist_analysis']}")
        experts_used.append("specialist")

    all_analyses = "\n\n".join(analyses)

    response = llm.invoke(synthesis_prompt.format_messages(
        all_analyses=all_analyses,
        experts_consulted=", ".join(experts_used)
    ))

    print(
        f"🎯 Synthesis complete - consulted {', '.join(experts_used)} experts")
    return {"final_report": response.content, "specialist_analysis": all_analyses}


def route_to_specialists(state: CodeAnalysisState) -> List[str]:
    """Route to multiple specialists based on multi-expert routing decisions"""
    routes = state.get("route_decisions", [
                       state.get("route_decision", "general")])
    return [f"{route}_expert" for route in routes]


def determine_next_steps(state: CodeAnalysisState) -> str:
    """Determine if we should continue to more experts or go to synthesis"""
    routes = state.get("route_decisions", [])
    completed_experts = []

    # Check which experts have completed
    if state.get("security_analysis"):
        completed_experts.append("security")
    if state.get("performance_analysis"):
        completed_experts.append("performance")
    if state.get("database_analysis"):
        completed_experts.append("database")
    if state.get("general_analysis"):
        completed_experts.append("general")

    # Find next expert to route to
    for route in routes:
        if route not in completed_experts:
            return f"{route}_expert"

    # All experts completed, go to synthesis
    return "synthesis"


builder = StateGraph(CodeAnalysisState)
builder.add_node("coder", coder_agent)
builder.add_node("router", router_agent)
builder.add_node("security_expert", security_expert_agent)
builder.add_node("performance_expert", performance_expert_agent)
builder.add_node("database_expert", database_expert_agent)
builder.add_node("general_expert", general_expert_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "router")
builder.add_conditional_edges(
    "router",
    determine_next_steps,
    {
        "security_expert": "security_expert",
        "performance_expert": "performance_expert",
        "database_expert": "database_expert",
        "general_expert": "general_expert",
        "synthesis": "synthesis"
    }
)

# Add conditional edges from each expert to either next expert or synthesis
builder.add_conditional_edges(
    "security_expert",
    determine_next_steps,
    {
        "performance_expert": "performance_expert",
        "database_expert": "database_expert",
        "general_expert": "general_expert",
        "synthesis": "synthesis"
    }
)

builder.add_conditional_edges(
    "performance_expert",
    determine_next_steps,
    {
        "security_expert": "security_expert",
        "database_expert": "database_expert",
        "general_expert": "general_expert",
        "synthesis": "synthesis"
    }
)

builder.add_conditional_edges(
    "database_expert",
    determine_next_steps,
    {
        "security_expert": "security_expert",
        "performance_expert": "performance_expert",
        "general_expert": "general_expert",
        "synthesis": "synthesis"
    }
)

builder.add_conditional_edges(
    "general_expert",
    determine_next_steps,
    {
        "security_expert": "security_expert",
        "performance_expert": "performance_expert",
        "database_expert": "database_expert",
        "synthesis": "synthesis"
    }
)
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a secure API function that handles user authentication and stores data in a PostgreSQL database with proper validation and performance optimization"

    print("Running intelligent multi-expert routing...")
    result = workflow.invoke({"input": task})

    experts_used = []
    if result.get("security_analysis"):
        experts_used.append("Security")
    if result.get("performance_analysis"):
        experts_used.append("Performance")
    if result.get("database_analysis"):
        experts_used.append("Database")
    if result.get("general_analysis"):
        experts_used.append("General")

    print(f"\n👥 Experts consulted: {', '.join(experts_used)}")
    print(f"🧠 Multi-expert analysis completed")

    codebase = ConditionalCodebase("02_conditional_routing", task)
    codebase.generate(result)

    print("=== MULTI-EXPERT WORKFLOW COMPLETED ===")
