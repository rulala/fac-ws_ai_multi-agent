from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()


class CodeAnalysisState(TypedDict):
    input: str
    code: str
    security_analysis: str
    performance_analysis: str
    style_analysis: str
    final_report: str


llm = ChatOpenAI(model="gpt-4o")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write production-ready Python code."),
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

synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Technical Lead. Synthesise analysis reports into actionable recommendations with priorities."),
    ("human",
     "Security Analysis:\n{security}\n\nPerformance Analysis:\n{performance}\n\nStyle Analysis:\n{style}\n\nProvide prioritised recommendations:")
])


def coder_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    return {"code": response.content}


def security_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(security_prompt.format_messages(code=state["code"]))
    return {"security_analysis": response.content}


def performance_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(
        performance_prompt.format_messages(code=state["code"]))
    return {"performance_analysis": response.content}


def style_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(style_prompt.format_messages(code=state["code"]))
    return {"style_analysis": response.content}


def synthesis_agent(state: CodeAnalysisState) -> CodeAnalysisState:
    response = llm.invoke(synthesis_prompt.format_messages(
        security=state["security_analysis"],
        performance=state["performance_analysis"],
        style=state["style_analysis"]
    ))
    return {"final_report": response.content}


builder = StateGraph(CodeAnalysisState)
builder.add_node("coder", coder_agent)
builder.add_node("security_agent", security_agent)
builder.add_node("performance_agent", performance_agent)
builder.add_node("style_agent", style_agent)
builder.add_node("synthesis", synthesis_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "security_agent")
builder.add_edge("coder", "performance_agent")
builder.add_edge("coder", "style_agent")
builder.add_edge("security_agent", "synthesis")
builder.add_edge("performance_agent", "synthesis")
builder.add_edge("style_agent", "synthesis")
builder.add_edge("synthesis", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a web API endpoint that processes user uploads and stores them in a database"

    print("Running parallel analysis...")
    result = workflow.invoke({"input": task})

    print("=== GENERATED CODE ===")
    print(result["code"])
    print("\n=== SECURITY ANALYSIS ===")
    print(result["security_analysis"])
    print("\n=== PERFORMANCE ANALYSIS ===")
    print(result["performance_analysis"])
    print("\n=== STYLE ANALYSIS ===")
    print(result["style_analysis"])
    print("\n=== SYNTHESIS REPORT ===")
    print(result["final_report"])

    print("\n=== EXERCISE ===")
    print("1. Add a testing agent that runs in parallel")
    print("2. Compare execution time vs sequential approach")
    print("3. Add error handling for failed parallel tasks")
    print("4. When is parallel processing most beneficial?")
