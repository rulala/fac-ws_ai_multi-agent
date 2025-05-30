from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Literal
from pydantic import BaseModel, Field
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionState(TypedDict):
    input: str
    code: str
    review: str
    refactored_code: str
    error_log: str
    retry_count: int
    human_approval_needed: bool
    execution_time: float
    session_id: str


class HumanApproval(BaseModel):
    approved: bool = Field(
        description="Whether the code is approved for production")
    feedback: str = Field(description="Human feedback or concerns")


llm = ChatOpenAI(model="gpt-4o", max_retries=3, timeout=30)


def robust_llm_call(prompt_template, **kwargs):
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = llm.invoke(prompt_template.format_messages(**kwargs))
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                raise Exception(
                    f"LLM call failed after {max_retries} attempts: {str(e)}")


coder_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Software Engineer. Write production-ready Python code with:
    - Proper error handling and logging
    - Input validation
    - Type hints
    - Documentation
    - Security considerations"""),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Code Reviewer. Focus on production readiness:
    - Error handling completeness
    - Security vulnerabilities
    - Performance implications
    - Maintainability concerns
    - Testing requirements"""),
    ("human", "Review this code for production readiness:\n{code}")
])

human_approval_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are simulating human oversight. Evaluate if this code is ready for production deployment."),
    ("human",
     "Code:\n{code}\n\nReview:\n{review}\n\nIs this ready for production?")
])


def coder_agent(state: ProductionState) -> ProductionState:
    start_time = time.time()
    session_id = state.get("session_id", f"session_{int(time.time())}")

    try:
        logger.info(f"[{session_id}] Starting code generation")
        code = robust_llm_call(coder_prompt, input=state["input"])

        execution_time = time.time() - start_time
        logger.info(
            f"[{session_id}] Code generation completed in {execution_time:.2f}s")

        return {
            "code": code,
            "session_id": session_id,
            "execution_time": execution_time,
            "retry_count": 0
        }

    except Exception as e:
        error_msg = f"Code generation failed: {str(e)}"
        logger.error(f"[{session_id}] {error_msg}")

        return {
            "error_log": state.get("error_log", "") + error_msg + "\n",
            "retry_count": state.get("retry_count", 0) + 1,
            "session_id": session_id
        }


def reviewer_agent(state: ProductionState) -> ProductionState:
    session_id = state["session_id"]

    try:
        logger.info(f"[{session_id}] Starting code review")
        review = robust_llm_call(reviewer_prompt, code=state["code"])

        logger.info(f"[{session_id}] Code review completed")
        return {"review": review}

    except Exception as e:
        error_msg = f"Code review failed: {str(e)}"
        logger.error(f"[{session_id}] {error_msg}")

        return {
            "error_log": state.get("error_log", "") + error_msg + "\n",
            "retry_count": state.get("retry_count", 0) + 1
        }


def human_approval_agent(state: ProductionState) -> ProductionState:
    session_id = state["session_id"]

    try:
        logger.info(f"[{session_id}] Requesting human approval simulation")

        structured_llm = llm.with_structured_output(HumanApproval)
        approval = structured_llm.invoke(human_approval_prompt.format_messages(
            code=state["code"], review=state["review"]))

        logger.info(f"[{session_id}] Human approval: {approval.approved}")

        if not approval.approved:
            logger.warning(
                f"[{session_id}] Human rejected code: {approval.feedback}")
            return {
                "human_approval_needed": True,
                "error_log": state.get("error_log", "") + f"Human rejection: {approval.feedback}\n"
            }

        return {"human_approval_needed": False}

    except Exception as e:
        error_msg = f"Human approval process failed: {str(e)}"
        logger.error(f"[{session_id}] {error_msg}")

        return {
            "error_log": state.get("error_log", "") + error_msg + "\n",
            "human_approval_needed": True
        }


def error_recovery_agent(state: ProductionState) -> ProductionState:
    session_id = state["session_id"]
    retry_count = state.get("retry_count", 0)

    logger.warning(
        f"[{session_id}] Error recovery triggered (retry {retry_count})")

    if retry_count >= 3:
        logger.error(
            f"[{session_id}] Max retries exceeded, escalating to human")
        return {
            "human_approval_needed": True,
            "error_log": state.get("error_log", "") + "Max retries exceeded - human intervention required\n"
        }

    logger.info(f"[{session_id}] Attempting recovery")
    return {"retry_count": retry_count}


def finalise_agent(state: ProductionState) -> ProductionState:
    session_id = state["session_id"]
    execution_time = state.get("execution_time", 0)

    logger.info(f"[{session_id}] Finalising production-ready code")
    logger.info(f"[{session_id}] Total execution time: {execution_time:.2f}s")

    final_code = state["code"]
    timestamp = datetime.now().isoformat()

    production_header = f"""# Production Code Generated: {timestamp}
# Session ID: {session_id}
# Execution Time: {execution_time:.2f}s
# Quality Checks: Passed

"""

    return {"refactored_code": production_header + final_code}


def should_retry(state: ProductionState) -> Literal["retry", "human_review", "continue"]:
    error_log = state.get("error_log", "")
    retry_count = state.get("retry_count", 0)

    if error_log and retry_count < 3:
        return "retry"
    elif error_log or state.get("human_approval_needed", False):
        return "human_review"
    else:
        return "continue"


def needs_human_approval(state: ProductionState) -> Literal["human_approval", "finalise"]:
    if state.get("human_approval_needed", False):
        return "human_approval"
    return "finalise"


checkpointer = MemorySaver()

builder = StateGraph(ProductionState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("human_approval", human_approval_agent)
builder.add_node("error_recovery", error_recovery_agent)
builder.add_node("finalise", finalise_agent)

builder.add_edge(START, "coder")
builder.add_conditional_edges(
    "coder",
    should_retry,
    {
        "retry": "error_recovery",
        "human_review": "human_approval",
        "continue": "reviewer"
    }
)
builder.add_edge("error_recovery", "coder")
builder.add_edge("reviewer", "human_approval")
builder.add_conditional_edges(
    "human_approval",
    needs_human_approval,
    {
        "human_approval": "error_recovery",
        "finalise": "finalise"
    }
)
builder.add_edge("finalise", END)

workflow = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    task = "Write a secure user authentication service with rate limiting and audit logging"

    config = {"configurable": {"thread_id": f"thread_{int(time.time())}"}}

    print("=== PRODUCTION DEPLOYMENT PIPELINE ===")
    logger.info("Starting production code generation pipeline")

    try:
        result = workflow.invoke({"input": task}, config=config)

        print("\n=== SESSION SUMMARY ===")
        print(f"Session ID: {result.get('session_id', 'N/A')}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        print(f"Retry Count: {result.get('retry_count', 0)}")

        if result.get("error_log"):
            print("\n=== ERROR LOG ===")
            print(result["error_log"])

        print("\n=== REVIEW ===")
        print(result.get("review", "No review available"))

        print("\n=== PRODUCTION-READY CODE ===")
        print(result.get("refactored_code", "No final code available"))

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        print(f"Pipeline failed: {str(e)}")
