from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class TaskAssignment(BaseModel):
    agent: Literal["security_expert", "performance_expert", "quality_expert", "complete"] = Field(
        description="Which expert should handle this task or 'complete' if analysis is sufficient"
    )
    reasoning: str = Field(description="Why this agent was chosen")


class SupervisorState(TypedDict):
    input: str
    code: str
    security_report: str
    performance_report: str
    quality_report: str
    supervisor_notes: str
    final_analysis: str
    completed_agents: list


llm = ChatOpenAI(model="gpt-4o")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write production-ready Python code with proper error handling."),
    ("human", "{input}")
])

supervisor_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Technical Supervisor managing a team of experts:
    - security_expert: Identifies vulnerabilities, injection attacks, data exposure
    - performance_expert: Analyses algorithmic complexity, bottlenecks, scalability
    - quality_expert: Reviews code structure, maintainability, best practices

    Based on the code and completed analyses, decide which expert should review next or if analysis is complete."""),
    ("human", """Code:\n{code}

Completed agents: {completed_agents}

Security report: {security_report}
Performance report: {performance_report}
Quality report: {quality_report}

What should happen next?""")
])

security_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Expert. Focus on authentication, authorisation, input validation, data protection, and potential attack vectors."),
    ("human", "Conduct security analysis:\n{code}")
])

performance_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Performance Expert. Analyse computational complexity, memory usage, database queries, and scalability concerns."),
    ("human", "Conduct performance analysis:\n{code}")
])

quality_expert_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Quality Expert. Review code structure, design patterns, maintainability, testability, and adherence to SOLID principles."),
    ("human", "Conduct quality analysis:\n{code}")
])

final_synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Technical Lead. Synthesise expert reports into executive summary with prioritised recommendations."),
    ("human", """Security Analysis:\n{security_report}

Performance Analysis:\n{performance_report}

Quality Analysis:\n{quality_report}

Supervisor Notes:\n{supervisor_notes}

Create a comprehensive final analysis with prioritised action items.""")
])


def coder_agent(state: SupervisorState) -> SupervisorState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content, "completed_agents": []}


def supervisor_agent(state: SupervisorState) -> SupervisorState:
    structured_llm = llm.with_structured_output(TaskAssignment)
    response = structured_llm.invoke(supervisor_prompt.format_messages(
        code=state["code"],
        completed_agents=state.get("completed_agents", []),
        security_report=state.get("security_report", "Not yet analysed"),
        performance_report=state.get("performance_report", "Not yet analysed"),
        quality_report=state.get("quality_report", "Not yet analysed")
    ))

    current_notes = state.get("supervisor_notes", "")
    new_note = f"Decision: {response.agent} - {response.reasoning}\n"

    return {
        "supervisor_notes": current_notes + new_note,
        "next_agent": response.agent
    }


def security_expert_agent(state: SupervisorState) -> SupervisorState:
    response = llm.invoke(
        security_expert_prompt.format_messages(code=state["code"]))
    completed = state.get("completed_agents", [])
    completed.append("security_expert")
    return {"security_report": response.content, "completed_agents": completed}


def performance_expert_agent(state: SupervisorState) -> SupervisorState:
    response = llm.invoke(
        performance_expert_prompt.format_messages(code=state["code"]))
    completed = state.get("completed_agents", [])
    completed.append("performance_expert")
    return {"performance_report": response.content, "completed_agents": completed}


def quality_expert_agent(state: SupervisorState) -> SupervisorState:
    response = llm.invoke(
        quality_expert_prompt.format_messages(code=state["code"]))
    completed = state.get("completed_agents", [])
    completed.append("quality_expert")
    return {"quality_report": response.content, "completed_agents": completed}


def synthesis_agent(state: SupervisorState) -> SupervisorState:
    response = llm.invoke(final_synthesis_prompt.format_messages(
        security_report=state.get("security_report", "Not analysed"),
        performance_report=state.get("performance_report", "Not analysed"),
        quality_report=state.get("quality_report", "Not analysed"),
        supervisor_notes=state.get("supervisor_notes", "")
    ))
    return {"final_analysis": response.content}


def route_to_expert(state: SupervisorState) -> Literal["security_expert", "performance_expert", "quality_expert", "synthesis"]:
    next_agent = state.get("next_agent", "complete")
    if next_agent == "complete":
        return "synthesis"
    return next_agent


builder = StateGraph(SupervisorState)
builder.add_node("coder", coder_agent)
builder.add_node("supervisor", supervisor_agent)
builder.add_node("security_expert", security_expert_agent)
builder.add_node("performance_expert", performance_expert_agent)
builder.add_node("quality_expert", quality_expert_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_to_expert,
    {
        "security_expert": "security_expert",
        "performance_expert": "performance_expert",
        "quality_expert": "quality_expert",
        "synthesis": "synthesis"
    }
)
builder.add_edge("security_expert", "supervisor")
builder.add_edge("performance_expert", "supervisor")
builder.add_edge("quality_expert", "supervisor")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a user authentication system with password hashing and session management"

    print("Starting supervised code review...")
    result = workflow.invoke({"input": task})

    print("=== GENERATED CODE ===")
    print(result["code"])
    print("\n=== SUPERVISOR DECISIONS ===")
    print(result["supervisor_notes"])
    print("\n=== COMPLETED ANALYSES ===")
    print(f"Agents consulted: {result['completed_agents']}")

    if result.get("security_report"):
        print("\n=== SECURITY EXPERT ===")
        print(result["security_report"])

    if result.get("performance_report"):
        print("\n=== PERFORMANCE EXPERT ===")
        print(result["performance_report"])

    if result.get("quality_report"):
        print("\n=== QUALITY EXPERT ===")
        print(result["quality_report"])

    print("\n=== FINAL ANALYSIS ===")
    print(result["final_analysis"])
