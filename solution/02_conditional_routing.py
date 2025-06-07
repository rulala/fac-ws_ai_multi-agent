from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
from dotenv import load_dotenv
from utils import ConditionalCodebase
import json

load_dotenv()


class CodeAnalysisState(TypedDict):
    input: str
    code: str
    route_decisions: List[str]
    confidence: float
    specialist_analysis: str
    final_report: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write clean Python code."),
    ("human", "{input}")
])

router_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Router. Analyse the task description and code snippet.\n"
        "Decide which experts should analyse it: security, performance, database, general.\n"
        "Return a JSON object with keys 'routes' (list) and 'confidence' (0-1).\n"
        "If unsure, include 'general' and lower the confidence."
    ),
    ("human", "Task: {input}\n\nCode:\n{code}")
])

security_expert_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Security Expert. Focus on vulnerabilities, authentication,"
        " authorization and secure coding practices."
    ),
    ("human", "Provide security analysis for:\n{code}")
])

performance_expert_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Performance Expert. Focus on algorithmic complexity,"
        " optimisation and resource usage."
    ),
    ("human", "Provide performance analysis for:\n{code}")
])

database_expert_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Database Expert. Focus on SQL injections, schema design,"
        " and query optimisation."
    ),
    ("human", "Provide database analysis for:\n{code}")
])

general_expert_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a General Code Expert. Focus on maintainability and best practices."
    ),
    ("human", "Provide general code analysis for:\n{code}")
])

synthesis_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a Technical Lead. Synthesise specialist feedback into final recommendations."
    ),
    (
        "human",
        "Specialist Analysis:\n{specialist_analysis}\n\nProvide final recommendations:"
    )
])


def coder_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content}


def router_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        router_prompt.format_messages(input=state["input"], code=state["code"])
    )

    try:
        data = json.loads(response.content)
        routes = [r.lower() for r in data.get("routes", [])]
        confidence = float(data.get("confidence", 0.5))
    except Exception:
        routes = [response.content.strip().lower()]
        confidence = 0.5

    if not routes:
        routes = ["general"]
    if confidence < 0.6 and "general" not in routes:
        routes.append("general")

    print(f"🎯 Router decisions: {routes} (confidence {confidence:.2f})")
    return {"route_decisions": routes, "confidence": confidence}


def specialists_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    analyses = []
    for route in state.get("route_decisions", []):
        if route == "security":
            resp = llm.invoke(security_expert_prompt.format_messages(code=state["code"]))
            analyses.append(f"### Security Expert\n{resp.content}")
        elif route == "performance":
            resp = llm.invoke(performance_expert_prompt.format_messages(code=state["code"]))
            analyses.append(f"### Performance Expert\n{resp.content}")
        elif route == "database":
            resp = llm.invoke(database_expert_prompt.format_messages(code=state["code"]))
            analyses.append(f"### Database Expert\n{resp.content}")
        else:
            resp = llm.invoke(general_expert_prompt.format_messages(code=state["code"]))
            analyses.append(f"### General Expert\n{resp.content}")
    combined = "\n\n".join(analyses)
    print("🔍 Specialists completed analysis")
    return {"specialist_analysis": combined}


def synthesis_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        synthesis_prompt.format_messages(specialist_analysis=state["specialist_analysis"])
    )
    routes = ", ".join(state.get("route_decisions", []))
    print(f"🎯 Synthesis complete - routed via {routes}")
    return {"final_report": response.content}


builder = StateGraph(CodeAnalysisState)
builder.add_node("coder", coder_agent)
builder.add_node("router", router_agent)
builder.add_node("specialists", specialists_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "router")
builder.add_edge("router", "specialists")
builder.add_edge("specialists", "synthesis")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a function that processes user data with error handling"

    print("Running conditional routing...")
    result = workflow.invoke({"input": task})

    codebase = ConditionalCodebase("02_conditional_routing", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")

