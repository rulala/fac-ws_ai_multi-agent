from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from dotenv import load_dotenv
from utils import ConditionalCodebase

load_dotenv()


class CodeAnalysisState(TypedDict):
    input: str
    code: str
    route_decision: str
    specialist_analysis: str
    final_report: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write clean Python code."),
    ("human", "{input}")
])

router_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Router. Analyse code and identify if it needs security, performance, or general review. Respond with just: 'security', 'performance', or 'general'."),
    ("human", "Route this code for expert review:\n{code}")
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

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Technical Lead. Synthesize the specialist analysis into actionable recommendations."),
    ("human",
     "Specialist Analysis:\n{specialist_analysis}\n\nProvide final recommendations:")
])


def coder_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content}


def router_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(router_prompt.format_messages(code=state["code"]))
    route = response.content.strip().lower()

    if route not in ["security", "performance", "general"]:
        route = "general"

    print(f"🎯 Router decision: {route}")
    return {"route_decision": route}


def security_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        security_expert_prompt.format_messages(code=state["code"]))
    print("🔒 Security expert analyzing code")
    return {"specialist_analysis": response.content, "route_decision": "security"}


def performance_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        performance_expert_prompt.format_messages(code=state["code"]))
    print("⚡ Performance expert analyzing code")
    return {"specialist_analysis": response.content, "route_decision": "performance"}


def general_expert_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        general_expert_prompt.format_messages(code=state["code"]))
    print("📋 General expert analyzing code")
    return {"specialist_analysis": response.content, "route_decision": "general"}


def synthesis_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(synthesis_prompt.format_messages(
        specialist_analysis=state["specialist_analysis"]
    ))

    route = state.get("route_decision", "unknown")
    print(f"🎯 Synthesis complete - routed via {route} expert")
    return {"final_report": response.content}


def route_to_specialist(state: CodeAnalysisState) -> Literal["security_expert", "performance_expert", "general_expert"]:
    route = state["route_decision"]
    return f"{route}_expert"


builder = StateGraph(CodeAnalysisState)
builder.add_node("coder", coder_agent)
builder.add_node("router", router_agent)
builder.add_node("security_expert", security_expert_agent)
builder.add_node("performance_expert", performance_expert_agent)
builder.add_node("general_expert", general_expert_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "router")
builder.add_conditional_edges(
    "router",
    route_to_specialist,
    {
        "security_expert": "security_expert",
        "performance_expert": "performance_expert",
        "general_expert": "general_expert"
    }
)
builder.add_edge("security_expert", "synthesis")
builder.add_edge("performance_expert", "synthesis")
builder.add_edge("general_expert", "synthesis")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a function that processes user data with error handling"

    print("Running conditional routing...")
    result = workflow.invoke({"input": task})

    codebase = ConditionalCodebase("02_conditional_routing", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
