from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv
from utils import SequentialCodebase
import json
import os
import datetime
import time

load_dotenv()


class CodeReviewState(TypedDict):
    input: str
    code: str
    review: str
    refactored_code: str
    unit_tests: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security-Focused Software Engineer. Write Python code with security as the primary concern. Include input validation, error handling, and secure coding practices."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Code Reviewer. Identify security vulnerabilities, injection risks, authentication flaws, and data exposure issues. Focus exclusively on security concerns."),
    ("human", "Security review this code:\n{code}")
])

refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Refactoring Expert. Fix security vulnerabilities identified in the review. Prioritise security over performance or readability. Write ONLY Python code - no bash commands, no installation instructions, just the Python implementation."),
    ("human",
     "Original code:\n{code}\n\nSecurity review:\n{review}\n\nRefactor to address security issues:")
])

tester_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Testing Expert. Write security-focused unit tests using pytest. Include tests for input validation, boundary conditions, injection attempts, and error handling."),
    ("human", "Generate security tests for this code:\n{refactored_code}")
])

performance_metrics = {}


def save_state_to_file(state: CodeReviewState, node_name: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_folder = f"generated/01_sequential_workflow_{timestamp}/debug"
    os.makedirs(debug_folder, exist_ok=True)

    filename = f"{debug_folder}/state_after_{node_name}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def time_node_execution(node_name: str):
    def decorator(func):
        def wrapper(state):
            start_time = time.time()
            print(f"🔄 Starting {node_name}...")

            result = func(state)

            end_time = time.time()
            execution_time = end_time - start_time
            performance_metrics[node_name] = execution_time

            print(f"✅ {node_name} completed in {execution_time:.2f}s")
            return result
        return wrapper
    return decorator


@time_node_execution("coder")
def coder_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    new_state = {"code": response.content}
    return new_state


@time_node_execution("reviewer")
def reviewer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(reviewer_prompt.format_messages(code=state["code"]))
    new_state = {"review": response.content}
    return new_state


@time_node_execution("refactorer")
def refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]))
    new_state = {"refactored_code": response.content}
    return new_state


@time_node_execution("tester")
def tester_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(tester_prompt.format_messages(
        refactored_code=state["refactored_code"]))
    new_state = {"tests": response.content}
    save_state_to_file({**state, **new_state}, "tester")
    return new_state


def print_performance_summary():
    total_time = sum(performance_metrics.values())
    print("\n" + "="*50)
    print("📊 PERFORMANCE SUMMARY")
    print("="*50)

    for node, duration in performance_metrics.items():
        percentage = (duration / total_time) * 100
        print(f"{node:12} | {duration:6.2f}s | {percentage:5.1f}%")

    print("-" * 50)
    print(f"{'TOTAL':12} | {total_time:6.2f}s | 100.0%")
    print("="*50)


builder = StateGraph(CodeReviewState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("refactorer", refactorer_agent)
builder.add_node("tester", tester_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "reviewer")
builder.add_edge("reviewer", "refactorer")
builder.add_edge("refactorer", "tester")
builder.add_edge("tester", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a function that validates email addresses using regex"

    print("Running sequential workflow with tester...")
    result = workflow.invoke({"input": task})

    codebase = SequentialCodebase("01_sequential_workflow", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
