"""
State definition for the Coding Agent.
Uses TypedDict for type-safe state management.
"""
from typing import TypedDict, Optional, List


class CodeAgentState(TypedDict, total=False):
    """
    Complete state for the code agent workflow.
    
    Attributes:
        user_query: The original user request
        intent: Detected intent type (from Intent enum)
        understood_problem: LLM's understanding of the problem
        plan: Step-by-step plan to solve the problem
        code: Generated or modified code
        explanation: Explanation of code/concepts
        llm_result: Final result to display to user
        
        # File operations
        file_path: Path to file being worked on
        file_content: Original content of file
        updated_content: Modified content to write
        language: Detected programming language
        
        # Error handling
        error: Error message if something failed
        
        # Conversation
        conversation_history: List of previous messages
    """
    # Core fields
    user_query: str
    intent: Optional[str]
    understood_problem: Optional[str]
    plan: Optional[str]
    code: Optional[str]
    explanation: Optional[str]
    llm_result: Optional[str]
    
    # File operations
    file_path: Optional[str]
    file_content: Optional[str]
    updated_content: Optional[str]
    language: Optional[str]
    
    # Error handling
    error: Optional[str]
    
    # Conversation history
    conversation_history: Optional[List[dict]]