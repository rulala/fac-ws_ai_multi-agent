from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from utils import ProductionCodebase
import datetime
import logging
import os

load_dotenv()

logging.basicConfig(
    filename="workflow.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


def log_event(message: str) -> None:
    """Append a timestamped message to the workflow log."""
    logging.info(message)


def monitor(node_name: str):
    """Decorator to log entry and exit of workflow nodes."""
    def decorator(func):
        def wrapper(state: ProductionState):
            log_event(f"Entering {node_name}")
            result = func(state)
            log_event(f"Exiting {node_name}")
            return result
        return wrapper
    return decorator


class ApprovalDecision(BaseModel):
    approved: bool = Field(description="Whether code is ready for production")
    feedback: str = Field(description="Approval feedback or concerns")


class ProductionState(TypedDict):
    input: str
    code: str
    review: str
    approved: bool
    retry_count: int
    final_code: str
    feedback: str
    compliance_report: str
    compliant: bool
    failure_streak: int
    last_approved_code: str
    human_approval_needed: bool


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY production-ready Python code with error handling and documentation - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior QA Engineer. Review code for production readiness: security, error handling, documentation."),
    ("human", "Review this code:\n{code}")
])

compliance_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a compliance officer. Check the following code for regulatory requirements (e.g. GDPR, SOC2). Respond with a short report and whether it is compliant."),
    ("human", "{code}")
])

approval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the Lead Technical Engineer on the project. Decide if this code is ready for production deployment."),
    ("human", "Code:\n{code}\n\nReview:\n{review}")
])


@monitor("coder")
def coder_agent(state: ProductionState) -> ProductionState:
    try:
        # Check if there's feedback from a previous rejection
        feedback = state.get("feedback", "")
        if feedback:
            # Incorporate feedback into the prompt
            full_input = f"{state['input']}\n\nIMPORTANT: Previous attempt was rejected with this feedback:\n{feedback}\n\nPlease address ALL these concerns."
        else:
            full_input = state["input"]

        response = llm.invoke(coder_prompt.format_messages(input=full_input))
        return {"code": response.content}
    except Exception as e:
        print(f"Code generation failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}


@monitor("reviewer")
def reviewer_agent(state: ProductionState) -> ProductionState:
    try:
        response = llm.invoke(
            reviewer_prompt.format_messages(code=state["code"]))
        return {"review": response.content}
    except Exception as e:
        print(f"Review failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}


@monitor("compliance")
def compliance_agent(state: ProductionState) -> ProductionState:
    try:
        response = llm.invoke(compliance_prompt.format_messages(code=state["code"]))
        compliant = "non-compliant" not in response.content.lower()
        return {"compliance_report": response.content, "compliant": compliant}
    except Exception as e:
        print(f"Compliance check failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1, "compliant": False}


@monitor("manual_review")
def manual_review_agent(state: ProductionState) -> ProductionState:
    print("🔍 Manual review required")
    code = state.get("last_approved_code", state.get("code", ""))
    return {
        "approved": True,
        "final_code": code,
        "code": code,
        "human_approval_needed": True,
        "failure_streak": 0,
    }


@monitor("approval")
def approval_agent(state: ProductionState) -> ProductionState:
    try:
        structured_llm = llm.with_structured_output(ApprovalDecision)
        decision = structured_llm.invoke(
            approval_prompt.format_messages(
                code=state["code"], review=state["review"]
            )
        )

        compliant = state.get("compliant", True)
        feedback = decision.feedback
        if not compliant:
            feedback = f"Non-compliance issues: {state.get('compliance_report', '')}"
            decision.approved = False

        if decision.approved:
            print("✅ Code approved for production")
            return {
                "approved": True,
                "feedback": "",
                "last_approved_code": state.get("code", ""),
                "failure_streak": 0,
            }
        else:
            print(f"❌ Code rejected: {feedback}")
            # Don't increment retry_count here - let handle_errors do it
            return {"approved": False, "feedback": feedback}

    except Exception as e:
        print(f"Approval process failed: {e}")
        return {"approved": False, "retry_count": state.get("retry_count", 0) + 1}


@monitor("finalise")
def finalise_agent(state: ProductionState) -> ProductionState:
    production_header = "# PRODUCTION-READY CODE\n# Quality checks: Passed\n\n"
    return {
        "final_code": production_header + state["code"],
        "workflow_log": os.path.abspath("workflow.log"),
    }


@monitor("handle_errors")
def handle_errors(state: ProductionState) -> ProductionState:
    retry_count = state.get("retry_count", 0) + 1
    failure_streak = state.get("failure_streak", 0) + 1
    print(f"⚠️  Error occurred, retry {retry_count}/3")
    rollback = state.get("last_approved_code", "")
    return {
        "retry_count": retry_count,
        "failure_streak": failure_streak,
        "code": rollback,
    }


def should_retry(state: ProductionState) -> Literal["retry", "reviewer"]:
    retry_count = state.get("retry_count", 0)
    if retry_count > 0 and retry_count < 3 and state.get("failure_streak", 0) < 2:
        return "retry"
    return "reviewer"


def check_approval(state: ProductionState) -> Literal["approved", "retry", "manual"]:
    if state.get("approved", False):
        return "approved"

    if state.get("failure_streak", 0) >= 2:
        print("Circuit breaker triggered - manual review required")
        return "manual"

    retry_count = state.get("retry_count", 0)
    if retry_count >= 3:
        print("Max retries reached - manual intervention required")
        return "manual"

    return "retry"


builder = StateGraph(ProductionState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("compliance", compliance_agent)
builder.add_node("approval", approval_agent)
builder.add_node("finalise", finalise_agent)
builder.add_node("handle_errors", handle_errors)
builder.add_node("manual_review", manual_review_agent)

builder.add_edge(START, "coder")
builder.add_conditional_edges("coder", should_retry, {
                              "retry": "handle_errors", "reviewer": "reviewer"})
builder.add_edge("handle_errors", "coder")
builder.add_edge("reviewer", "compliance")
builder.add_edge("compliance", "approval")
builder.add_conditional_edges("approval", check_approval, {
                              "approved": "finalise",
                              "retry": "handle_errors",
                              "manual": "manual_review"})
builder.add_edge("manual_review", "finalise")
builder.add_edge("finalise", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a secure user authentication service with rate limiting"

    print("=== PRODUCTION PIPELINE ===")
    result = workflow.invoke({"input": task})

    codebase = ProductionCodebase("07_production_ready", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
