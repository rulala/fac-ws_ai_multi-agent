from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv
from utils import SequentialCodebase
import json
import os
import datetime

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
    ("system", "You are a Security Refactoring Expert. Fix security vulnerabilities identified in the review. Prioritise security over performance or readability."),
    ("human",
     "Original code:\n{code}\n\nSecurity review:\n{review}\n\nRefactor to address security issues:")
])

tester_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Testing Expert. Write security-focused unit tests using pytest. Include tests for input validation, boundary conditions, injection attempts, and error handling."),
    ("human", "Generate security tests for this code:\n{refactored_code}")
])


def save_state_to_file(state: CodeReviewState, node_name: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_folder = f"generated/01_sequential_workflow_{timestamp}/debug"
    os.makedirs(debug_folder, exist_ok=True)

    filename = f"{debug_folder}/state_after_{node_name}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def coder_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))
    new_state = {"code": response.content}
    save_state_to_file({**state, **new_state}, "coder")
    return new_state


def reviewer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(reviewer_prompt.format_messages(code=state["code"]))
    new_state = {"review": response.content}
    save_state_to_file({**state, **new_state}, "reviewer")
    return new_state


def refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]))
    new_state = {"refactored_code": response.content}
    save_state_to_file({**state, **new_state}, "refactorer")
    return new_state


def tester_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(tester_prompt.format_messages(
        refactored_code=state["refactored_code"]))
    new_state = {"unit_tests": response.content}
    save_state_to_file({**state, **new_state}, "tester")
    return new_state


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
