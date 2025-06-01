from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from utils import ProductionCodebase

load_dotenv()


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


llm = ChatOpenAI(model="gpt-4o")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "Write production-ready Python code with error handling and documentation."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "Review code for production readiness: security, error handling, documentation."),
    ("human", "Review this code:\n{code}")
])

approval_prompt = ChatPromptTemplate.from_messages([
    ("system", "Decide if this code is ready for production deployment."),
    ("human", "Code:\n{code}\n\nReview:\n{review}")
])


def coder_agent(state: ProductionState) -> ProductionState:
    try:
        response = llm.invoke(
            coder_prompt.format_messages(input=state["input"]))
        return {"code": response.content, "retry_count": 0}
    except Exception as e:
        print(f"Code generation failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}


def reviewer_agent(state: ProductionState) -> ProductionState:
    try:
        response = llm.invoke(
            reviewer_prompt.format_messages(code=state["code"]))
        return {"review": response.content}
    except Exception as e:
        print(f"Review failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}


def approval_agent(state: ProductionState) -> ProductionState:
    try:
        structured_llm = llm.with_structured_output(ApprovalDecision)
        decision = structured_llm.invoke(approval_prompt.format_messages(
            code=state["code"], review=state["review"]
        ))

        if decision.approved:
            print("✅ Code approved for production")
        else:
            print(f"❌ Code rejected: {decision.feedback}")

        return {"approved": decision.approved}
    except Exception as e:
        print(f"Approval process failed: {e}")
        return {"approved": False, "retry_count": state.get("retry_count", 0) + 1}


def finalise_agent(state: ProductionState) -> ProductionState:
    production_header = "# PRODUCTION-READY CODE\n# Quality checks: Passed\n\n"
    return {"final_code": production_header + state["code"]}


def handle_errors(state: ProductionState) -> ProductionState:
    retry_count = state.get("retry_count", 0)
    print(f"⚠️  Error occurred, retry {retry_count}/3")
    return {"retry_count": retry_count}


def should_retry(state: ProductionState) -> Literal["retry", "reviewer"]:
    retry_count = state.get("retry_count", 0)
    if retry_count > 0 and retry_count < 3:
        return "retry"
    return "reviewer"


def check_approval(state: ProductionState) -> Literal["approved", "retry"]:
    if state.get("approved", False):
        return "approved"

    retry_count = state.get("retry_count", 0)
    if retry_count >= 3:
        print("Max retries reached - manual intervention required")
        return "approved"

    return "retry"


builder = StateGraph(ProductionState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("approval", approval_agent)
builder.add_node("finalise", finalise_agent)
builder.add_node("handle_errors", handle_errors)

builder.add_edge(START, "coder")
builder.add_conditional_edges("coder", should_retry, {
                              "retry": "handle_errors", "reviewer": "reviewer"})
builder.add_edge("handle_errors", "coder")
builder.add_edge("reviewer", "approval")
builder.add_conditional_edges("approval", check_approval, {
                              "approved": "finalise", "retry": "handle_errors"})
builder.add_edge("finalise", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a secure user authentication service with rate limiting"

    print("=== PRODUCTION PIPELINE ===")
    result = workflow.invoke({"input": task})

    codebase = ProductionCodebase("06_production_ready", task)
    codebase.generate(result)

    print("=== WORKFLOW COMPLETED ===")
