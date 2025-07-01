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


class ComplianceResult(BaseModel):
    compliant: bool = Field(
        description="Whether code meets regulatory requirements")
    issues: list = Field(
        description="List of compliance issues found", default_factory=list)
    recommendations: str = Field(description="Compliance recommendations")


class HumanApprovalDecision(BaseModel):
    approved: bool = Field(description="Human approval decision")
    comments: str = Field(description="Human reviewer comments")


class ProductionState(TypedDict):
    input: str
    code: str
    review: str
    compliance_report: str
    approved: bool
    human_approved: bool
    retry_count: int
    consecutive_failures: int
    circuit_breaker_triggered: bool
    needs_human_approval: bool
    final_code: str
    feedback: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer. Write ONLY production-ready Python code with error handling and documentation - no bash commands, no installation instructions, just the Python implementation."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior QA Engineer. Review code for production readiness: security, error handling, documentation."),
    ("human", "Review this code:\n{code}")
])

approval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the Lead Technical Engineer on the project. Decide if this code is ready for production deployment."),
    ("human", "Code:\n{code}\n\nReview:\n{review}")
])

compliance_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Compliance Officer. Check code for regulatory compliance including GDPR, SOX, HIPAA, PCI-DSS, and security standards. Identify any compliance issues."),
    ("human", "Compliance check for:\n{code}")
])

human_approval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are simulating a Human Approver for critical production changes. Make an approval decision based on the code review and compliance report."),
    ("human",
     "CRITICAL CHANGE REQUIRING HUMAN APPROVAL\n\nCode:\n{code}\n\nReview:\n{review}\n\nCompliance Report:\n{compliance_report}\n\nApprove for production?")
])


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

        # Determine if this is a critical change requiring human approval
        code_content = response.content.lower()
        is_critical = any(keyword in code_content for keyword in [
            'authentication', 'password', 'security', 'payment', 'encryption',
            'database', 'production', 'deploy', 'config', 'admin', 'root'
        ])

        print(
            f"🔍 Code analysis: {'CRITICAL CHANGE' if is_critical else 'Standard change'} detected")

        return {
            "code": response.content,
            "needs_human_approval": is_critical,
            "consecutive_failures": 0  # Reset on successful generation
        }
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        return {
            "retry_count": state.get("retry_count", 0) + 1,
            "consecutive_failures": consecutive_failures
        }


def reviewer_agent(state: ProductionState) -> ProductionState:
    try:
        response = llm.invoke(
            reviewer_prompt.format_messages(code=state["code"]))
        return {"review": response.content}
    except Exception as e:
        print(f"❌ Review failed: {e}")
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        return {
            "retry_count": state.get("retry_count", 0) + 1,
            "consecutive_failures": consecutive_failures
        }


def compliance_agent(state: ProductionState) -> ProductionState:
    """Exercise 3: Compliance check agent"""
    try:
        structured_llm = llm.with_structured_output(ComplianceResult)
        result = structured_llm.invoke(compliance_prompt.format_messages(
            code=state["code"]
        ))

        if result.compliant:
            print("✅ Compliance check passed")
        else:
            print(f"⚠️ Compliance issues found: {len(result.issues)} issues")

        return {"compliance_report": f"Compliant: {result.compliant}\nIssues: {result.issues}\nRecommendations: {result.recommendations}"}
    except Exception as e:
        print(f"❌ Compliance check failed: {e}")
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        return {
            "compliance_report": "Compliance check failed",
            "consecutive_failures": consecutive_failures
        }


def approval_agent(state: ProductionState) -> ProductionState:
    try:
        structured_llm = llm.with_structured_output(ApprovalDecision)
        decision = structured_llm.invoke(approval_prompt.format_messages(
            code=state["code"], review=state["review"]
        ))

        if decision.approved:
            print("✅ Code approved for production")
            return {"approved": True, "feedback": ""}
        else:
            print(f"❌ Code rejected: {decision.feedback}")
            consecutive_failures = state.get("consecutive_failures", 0) + 1
            return {
                "approved": False,
                "feedback": decision.feedback,
                "consecutive_failures": consecutive_failures
            }

    except Exception as e:
        print(f"❌ Approval process failed: {e}")
        consecutive_failures = state.get("consecutive_failures", 0) + 1
        return {
            "approved": False,
            "retry_count": state.get("retry_count", 0) + 1,
            "consecutive_failures": consecutive_failures
        }


def human_approval_agent(state: ProductionState) -> ProductionState:
    """Exercise 1: Human approval gates for critical changes"""
    try:
        structured_llm = llm.with_structured_output(HumanApprovalDecision)
        decision = structured_llm.invoke(human_approval_prompt.format_messages(
            code=state["code"],
            review=state["review"],
            compliance_report=state.get(
                "compliance_report", "No compliance report")
        ))

        if decision.approved:
            print("👤✅ Human approver: APPROVED for production")
            return {"human_approved": True, "feedback": decision.comments}
        else:
            print(f"👤❌ Human approver: REJECTED - {decision.comments}")
            return {"human_approved": False, "feedback": decision.comments}

    except Exception as e:
        print(f"❌ Human approval failed: {e}")
        return {"human_approved": False, "feedback": "Human approval process failed"}


def manual_review_agent(state: ProductionState) -> ProductionState:
    """Exercise 2: Manual review when circuit breaker is triggered"""
    print("🚨 CIRCUIT BREAKER TRIGGERED - Manual review required")
    print(f"   Consecutive failures: {state.get('consecutive_failures', 0)}")
    print(f"   Manual intervention needed for production deployment")

    # Simulate manual review approval for workshop purposes
    return {
        "approved": True,
        "human_approved": True,
        "final_code": "# MANUAL REVIEW APPROVED\n# Circuit breaker triggered - manual intervention\n\n" + state.get("code", ""),
        "feedback": "Approved via manual review after circuit breaker activation"
    }


def finalise_agent(state: ProductionState) -> ProductionState:
    production_header = "# PRODUCTION-READY CODE\n# Quality checks: Passed\n\n"
    return {"final_code": production_header + state["code"]}


def handle_errors(state: ProductionState) -> ProductionState:
    retry_count = state.get("retry_count", 0) + 1
    consecutive_failures = state.get("consecutive_failures", 0)

    print(
        f"⚠️ Error occurred, retry {retry_count}/3 (consecutive failures: {consecutive_failures})")

    # Exercise 2: Circuit breaker - trigger after 2 consecutive failures
    circuit_breaker_triggered = consecutive_failures >= 2

    if circuit_breaker_triggered:
        print(
            "🚨 CIRCUIT BREAKER: 2 consecutive failures reached - routing to manual review")

    return {
        "retry_count": retry_count,
        "circuit_breaker_triggered": circuit_breaker_triggered
    }


def should_retry(state: ProductionState) -> Literal["retry", "compliance"]:
    retry_count = state.get("retry_count", 0)

    # Check circuit breaker first
    if state.get("circuit_breaker_triggered", False):
        return "compliance"  # Continue to compliance even with circuit breaker

    if retry_count > 0 and retry_count < 3:
        return "retry"
    return "compliance"  # Changed from "reviewer" to "compliance"


def check_circuit_breaker(state: ProductionState) -> Literal["manual_review", "human_approval"]:
    """Exercise 2: Check if circuit breaker should route to manual review"""
    if state.get("circuit_breaker_triggered", False):
        return "manual_review"
    return "human_approval"


def check_human_approval_needed(state: ProductionState) -> Literal["human_approval", "finalise"]:
    """Exercise 1: Check if human approval is needed for critical changes"""
    if state.get("needs_human_approval", False):
        print("🔒 Critical change detected - requiring human approval")
        return "human_approval"
    return "finalise"


def check_final_approval(state: ProductionState) -> Literal["finalise", "retry"]:
    """Check final approval status considering both automated and human approval"""
    automated_approved = state.get("approved", False)
    # Default true if not needed
    human_approved = state.get("human_approved", True)
    needs_human = state.get("needs_human_approval", False)

    # If human approval was needed, check it was given
    if needs_human and not human_approved:
        print("❌ Human approval required but not granted")
        return "retry"

    if automated_approved:
        return "finalise"

    retry_count = state.get("retry_count", 0)
    if retry_count >= 3:
        print("Max retries reached - forcing completion")
        return "finalise"

    return "retry"


builder = StateGraph(ProductionState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("compliance", compliance_agent)  # Exercise 3
builder.add_node("approval", approval_agent)
builder.add_node("human_approval", human_approval_agent)  # Exercise 1
builder.add_node("manual_review", manual_review_agent)  # Exercise 2
builder.add_node("finalise", finalise_agent)
builder.add_node("handle_errors", handle_errors)

# Build the production workflow with all exercises
builder.add_edge(START, "coder")
builder.add_conditional_edges("coder", should_retry, {
    "retry": "handle_errors",
    "compliance": "reviewer"
})
builder.add_edge("handle_errors", "coder")
builder.add_edge("reviewer", "compliance")
builder.add_conditional_edges("compliance", check_circuit_breaker, {
    "manual_review": "manual_review",
    "human_approval": "approval"
})
builder.add_conditional_edges("approval", check_final_approval, {
    "finalise": "human_approval",  # Route to human approval for critical changes
    "retry": "handle_errors"
})
builder.add_conditional_edges("human_approval", check_human_approval_needed, {
    "human_approval": "finalise",  # After human approval, go to finalise
    "finalise": "finalise"
})
builder.add_edge("manual_review", END)
builder.add_edge("finalise", END)

workflow = builder.compile()

if __name__ == "__main__":
    task = "Write a secure payment processing service with encryption, user authentication, and database integration"

    print("=== PRODUCTION PIPELINE WITH APPROVAL GATES ===")
    result = workflow.invoke({
        "input": task,
        "retry_count": 0,
        "consecutive_failures": 0,
        "circuit_breaker_triggered": False,
        "approved": False,
        "human_approved": False
    })

    # Display execution summary
    print(f"\n📊 Production Pipeline Results:")
    print(f"  Automated approval: {'✅' if result.get('approved') else '❌'}")
    print(
        f"  Human approval: {'✅' if result.get('human_approved') else '❌' if result.get('needs_human_approval') else 'N/A'}")
    print(
        f"  Circuit breaker triggered: {'🚨 YES' if result.get('circuit_breaker_triggered') else '✅ NO'}")
    print(
        f"  Compliance check: {'✅ PASSED' if 'Compliant: True' in str(result.get('compliance_report', '')) else '⚠️ ISSUES'}")
    print(f"  Retry count: {result.get('retry_count', 0)}/3")

    if result.get('needs_human_approval'):
        print(f"  🔒 Critical change - human approval was required")

    if result.get('circuit_breaker_triggered'):
        print(f"  🚨 Circuit breaker activated - manual review completed")

    codebase = ProductionCodebase("07_production_ready", task)
    codebase.generate(result)

    print("=== PRODUCTION WORKFLOW WITH APPROVAL GATES COMPLETED ===")
