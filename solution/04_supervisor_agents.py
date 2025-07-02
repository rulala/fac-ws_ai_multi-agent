from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv
from utils import SupervisorCodebase

load_dotenv()


class SupervisorState(TypedDict):
    input: str
    code: str
    security_report: str
    quality_report: str
    database_report: str
    completed_agents: list
    final_analysis: str
    task_type: str
    next_agent: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY production-ready Python code with proper error handling - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Analyse task type and code content. For authentication tasks, prioritise security expert first. Choose next expert: 'security_expert', 'quality_expert', 'database_expert', or 'complete'. Completed: {completed_agents}. Task type: {task_type}"),
    ("human", "Code needs analysis:\n{code}")
])

security_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Expert. Focus on vulnerabilities and security best practices. If quality report available, consider those findings too."),
    ("human",
     "Security analysis for:\n{code}\n\nQuality report context: {quality_report}")
])

quality_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Quality Expert. Review code structure and maintainability."),
    ("human", "Quality analysis for:\n{code}")
])

database_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Database Expert. Review SQL queries, schema design, and database interactions for security, performance, and best practices."),
    ("human", "Database analysis for:\n{code}")
])

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "Create final analysis summary with key recommendations based on all expert reports."),
    ("human",
     "Security: {security_report}\n\nQuality: {quality_report}\n\nDatabase: {database_report}")
])


def coder_agent(state: SupervisorState) -> SupervisorState:
    print("👨‍💻 Generating code...")
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))

    task_lower = state["input"].lower()
    if any(keyword in task_lower for keyword in ["authentication", "login", "auth", "password", "security"]):
        task_type = "authentication"
    elif any(keyword in task_lower for keyword in ["database", "sql", "query", "schema", "db"]):
        task_type = "database"
    else:
        task_type = "general"

    print(f"🎯 Task type detected: {task_type}")
    return {
        "code": response.content,
        "completed_agents": [],
        "task_type": task_type,
        "security_report": "",
        "quality_report": "",
        "database_report": ""
    }


def supervisor_agent(state: SupervisorState) -> SupervisorState:
    completed = state.get("completed_agents", [])
    code = state.get("code", "")
    task_type = state.get("task_type", "general")

    print(f"🎯 Supervisor: Task type: {task_type}, Completed: {completed}")

    if task_type == "authentication" and "security_expert" not in completed:
        print("🔒 Routing to security expert (authentication priority)")
        return {"next_agent": "security_expert"}
    elif any(keyword in code.lower() for keyword in ["sql", "database", "query", "schema", "db"]) and "database_expert" not in completed:
        print("🗄️ Routing to database expert (code content analysis)")
        return {"next_agent": "database_expert"}
    elif "security_expert" not in completed:
        print("🔒 Routing to security expert")
        return {"next_agent": "security_expert"}
    elif "quality_expert" not in completed:
        print("✨ Routing to quality expert")
        return {"next_agent": "quality_expert"}
    else:
        print("✅ All experts consulted, proceeding to synthesis")
        return {"next_agent": "complete"}


def security_expert_agent(state: SupervisorState) -> SupervisorState:
    print("🔒 Security expert analyzing code...")
    quality_context = state.get(
        "quality_report", "No quality analysis available yet")
    response = llm.invoke(security_expert_prompt.format_messages(
        code=state["code"],
        quality_report=quality_context
    ))
    completed = state.get("completed_agents", []).copy()
    completed.append("security_expert")
    print(f"✅ Security analysis complete. Agents now completed: {completed}")
    return {"security_report": response.content, "completed_agents": completed}


def quality_expert_agent(state: SupervisorState) -> SupervisorState:
    print("✨ Quality expert analyzing code...")
    response = llm.invoke(
        quality_expert_prompt.format_messages(code=state["code"]))
    completed = state.get("completed_agents", []).copy()
    completed.append("quality_expert")
    print(f"✅ Quality analysis complete. Agents now completed: {completed}")
    return {"quality_report": response.content, "completed_agents": completed}


def database_expert_agent(state: SupervisorState) -> SupervisorState:
    print("🗄️ Database expert analyzing code...")
    response = llm.invoke(
        database_expert_prompt.format_messages(code=state["code"]))
    completed = state.get("completed_agents", []).copy()
    completed.append("database_expert")
    print(f"✅ Database analysis complete. Agents now completed: {completed}")
    return {"database_report": response.content, "completed_agents": completed}


def synthesis_agent(state: SupervisorState) -> SupervisorState:
    print("📊 Synthesizing expert reports...")
    security_report = state.get("security_report", "Not analysed")
    quality_report = state.get("quality_report", "Not analysed")
    database_report = state.get("database_report", "Not analysed")

    print(f"📋 Available reports: Security: {'✅' if security_report != 'Not analysed' else '❌'}, "
          f"Quality: {'✅' if quality_report != 'Not analysed' else '❌'}, "
          f"Database: {'✅' if database_report != 'Not analysed' else '❌'}")

    response = llm.invoke(synthesis_prompt.format_messages(
        security_report=security_report,
        quality_report=quality_report,
        database_report=database_report
    ))
    return {"final_analysis": response.content}


def route_to_expert(state: SupervisorState) -> Literal["security_expert", "quality_expert", "database_expert", "synthesis"]:
    next_agent = state.get("next_agent", "complete")
    if next_agent == "complete":
        return "synthesis"
    return next_agent


builder = StateGraph(SupervisorState)
builder.add_node("coder", coder_agent)
builder.add_node("supervisor", supervisor_agent)
builder.add_node("security_expert", security_expert_agent)
builder.add_node("quality_expert", quality_expert_agent)
builder.add_node("database_expert", database_expert_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_to_expert,
    {
        "security_expert": "security_expert",
        "quality_expert": "quality_expert",
        "database_expert": "database_expert",
        "synthesis": "synthesis"
    }
)
builder.add_edge("security_expert", "supervisor")
builder.add_edge("quality_expert", "supervisor")
builder.add_edge("database_expert", "supervisor")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a user authentication system with database integration"

    print("Starting supervised code review...")
    result = workflow.invoke({"input": task})

    codebase = SupervisorCodebase("04_supervisor_agents", task)
    codebase.generate(result)

    print("=== SUPERVISOR AGENTS WORKFLOW COMPLETED ===")
