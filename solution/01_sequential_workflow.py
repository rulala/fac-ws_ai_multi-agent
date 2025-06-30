from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv
from utils import SequentialCodebase

load_dotenv()


class CodeReviewState(TypedDict):
    input: str
    code: str
    review: str
    refactored_code: str
    tests: str
    code_type: str


llm = ChatOpenAI(model="gpt-4.1-nano")

coder_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Senior Software Engineer with expertise in secure coding. Write clean, well-structured Python code that prioritizes security and follows security best practices. ONLY output the Python code."),
    ("human", "{input}")
])

reviewer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security-focused Code Reviewer. Provide constructive feedback focusing on security vulnerabilities, potential attack vectors, input validation, and secure coding practices."),
    ("human", "Review this code for security issues:\n{code}")
])

web_refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Web Security Refactoring Expert. Implement security improvements for web applications, focusing on XSS prevention, CSRF protection, and secure HTTP handling."),
    ("human",
     "Original web code:\n{code}\n\nSecurity review:\n{review}\n\nRefactor for web security:")
])

api_refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an API Security Refactoring Expert. Implement security improvements for APIs, focusing on authentication, authorization, input validation, and rate limiting."),
    ("human",
     "Original API code:\n{code}\n\nSecurity review:\n{review}\n\nRefactor for API security:")
])

data_refactorer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Data Security Refactoring Expert. Implement security improvements for data processing, focusing on data sanitization, encryption, and secure data handling."),
    ("human",
     "Original data processing code:\n{code}\n\nSecurity review:\n{review}\n\nRefactor for data security:")
])

tester_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a Security Testing Expert. Generate comprehensive unit tests that include security test cases, edge cases, and validation tests."),
    ("human", "Generate unit tests for this code:\n{refactored_code}")
])


def determine_code_type(task_input: str, code_content: str) -> str:
    """
    Enhanced code type detection using weighted scoring.
    Analyzes both task description and generated code for accurate classification.
    """
    # Combine task and code for analysis
    combined_text = f"{task_input} {code_content}".lower()

    # Weighted scoring for better accuracy
    scores = {"api": 0, "web": 0, "data": 0}

    # API indicators (REST APIs, endpoints, web services)
    api_keywords = {
        "api": 3, "rest": 3, "endpoint": 3, "fastapi": 3, "restful": 3,
        "json": 2, "request": 2, "response": 2, "route": 2, "service": 2,
        "authentication": 2, "authorization": 2, "validate": 2, "registration": 2,
        "post": 1, "get": 1, "put": 1, "delete": 1, "http": 1
    }

    # Web frontend indicators (HTML, CSS, forms, DOM manipulation)
    web_keywords = {
        "html": 3, "css": 3, "javascript": 3, "dom": 3, "frontend": 3,
        "template": 2, "form": 2, "render": 2, "page": 2, "browser": 2,
        "flask": 1, "django": 1, "web": 1, "url": 1, "view": 1
    }

    # Data processing indicators
    data_keywords = {
        "dataframe": 3, "pandas": 3, "csv": 3, "sql": 3, "database": 3,
        "query": 2, "table": 2, "schema": 2, "etl": 2, "analytics": 2,
        "data": 1, "processing": 1, "transform": 1, "load": 1
    }

    # Calculate scores
    for keyword, weight in api_keywords.items():
        if keyword in combined_text:
            scores["api"] += weight

    for keyword, weight in web_keywords.items():
        if keyword in combined_text:
            scores["web"] += weight

    for keyword, weight in data_keywords.items():
        if keyword in combined_text:
            scores["data"] += weight

    # Determine winner
    max_score = max(scores.values())
    if max_score == 0:
        return "general"

    # Get type with highest score
    winning_type = max(scores, key=scores.get)

    # Debug output
    print(f"🔍 Code type analysis:")
    print(f"   Task: '{task_input[:50]}...'")
    print(
        f"   Scores: API={scores['api']}, Web={scores['web']}, Data={scores['data']}")
    print(f"   Decision: {winning_type.upper()}")

    return winning_type


def coder_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(coder_prompt.format_messages(input=state["input"]))

    # Enhanced code type detection
    code_type = determine_code_type(state["input"], response.content)

    return {"code": response.content, "code_type": code_type}


def reviewer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(reviewer_prompt.format_messages(code=state["code"]))
    return {"review": response.content}


def determine_refactorer_route(state: CodeReviewState) -> str:
    """Route to appropriate refactorer based on code type"""
    code_type = state.get("code_type", "general")
    if code_type == "web":
        return "web_refactorer"
    elif code_type == "api":
        return "api_refactorer"
    elif code_type == "data":
        return "data_refactorer"
    else:
        return "api_refactorer"  # Default fallback


def web_refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(web_refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]))
    return {"refactored_code": response.content}


def api_refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(api_refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]))
    return {"refactored_code": response.content}


def data_refactorer_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(data_refactorer_prompt.format_messages(
        code=state["code"], review=state["review"]))
    return {"refactored_code": response.content}


def tester_agent(state: CodeReviewState) -> CodeReviewState:
    response = llm.invoke(tester_prompt.format_messages(
        refactored_code=state["refactored_code"]))
    return {"tests": response.content}


builder = StateGraph(CodeReviewState)
builder.add_node("coder", coder_agent)
builder.add_node("reviewer", reviewer_agent)
builder.add_node("web_refactorer", web_refactorer_agent)
builder.add_node("api_refactorer", api_refactorer_agent)
builder.add_node("data_refactorer", data_refactorer_agent)
builder.add_node("tester", tester_agent)

builder.add_edge(START, "coder")
builder.add_edge("coder", "reviewer")
builder.add_conditional_edges(
    "reviewer",
    determine_refactorer_route,
    {
        "web_refactorer": "web_refactorer",
        "api_refactorer": "api_refactorer",
        "data_refactorer": "data_refactorer"
    }
)
builder.add_edge("web_refactorer", "tester")
builder.add_edge("api_refactorer", "tester")
builder.add_edge("data_refactorer", "tester")
builder.add_edge("tester", END)

workflow = builder.compile()

if __name__ == "__main__":
    # Test cases to verify improved code type detection
    test_cases = [
        "Write a secure API function that validates email addresses and handles user registration with proper input validation",
        "Create a web page with HTML forms for user login and CSS styling",
        "Build a data processing pipeline that reads CSV files and transforms them into a SQL database"
    ]

    # Run the main API task
    task = test_cases[0]  # API task

    print("Running security-focused sequential workflow...")
    print(f"📋 Task: {task}")
    result = workflow.invoke({"input": task})

    print(f"\n🔍 Code type detected: {result.get('code_type', 'unknown')}")
    print(f"🛡️ Security review completed")
    print(
        f"🔧 Refactored using {result.get('code_type', 'general')} security specialist")
    print(f"✅ Security tests generated")

    codebase = SequentialCodebase("01_sequential_workflow", task)
    codebase.generate(result)

    print("=== SECURITY WORKFLOW COMPLETED ===")

    # Optional: Test other task types (commented out to avoid multiple runs)
    # print("\n" + "="*60)
    # print("🧪 TESTING OTHER TASK TYPES:")
    # for i, test_task in enumerate(test_cases[1:], 2):
    #     print(f"\nTest {i}: {test_task}")
    #     test_result = workflow.invoke({"input": test_task})
    #     print(f"Result: {test_result.get('code_type', 'unknown')} specialist selected")
