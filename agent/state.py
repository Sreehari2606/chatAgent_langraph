from typing import TypedDict, Optional, List

class CodeAgentState(TypedDict, total=False):
    user_query: str
    intent: Optional[str]
    understood_problem: Optional[str]
    plan: Optional[str]
    code: Optional[str]
    explanation: Optional[str]
    llm_result: Optional[str]
    file_path: Optional[str]
    file_content: Optional[str]
    updated_content: Optional[str]
    language: Optional[str]
    error: Optional[str]
    conversation_history: Optional[List[dict]]