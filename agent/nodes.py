"""
Coding Agent Nodes - Industry Standard Implementation

This module contains all node functions for the coding agent workflow.
Each node processes state and returns updated state for the next step.
"""
import os
import re
import logging
from typing import Optional
from agent.state import CodeAgentState
from agent.llm import llm_invoke
from agent.constants import (
    Intent,
    BLOCKED_PATHS,
    CODE_EXTENSIONS,
    FILE_PATTERNS,
    REVIEW_PATTERNS,
    REFACTOR_PATTERNS,
    TEST_PATTERNS,
    DOC_PATTERNS,
    OPTIMIZE_PATTERNS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_llm_response(prompt: str) -> str:
    """
    Safely get LLM response with error handling.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM response text, or an error message
    """
    try:
        result = llm_invoke(prompt)
        # Handle different response formats
        if isinstance(result, dict):
            return result.get("content", result.get("generate", "No response"))
        return str(result)
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        return f"Error: {str(e)}"


def detect_language(file_path: str) -> str:
    """
    Detect programming language from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name or 'unknown'
    """
    _, ext = os.path.splitext(file_path.lower())
    return CODE_EXTENSIONS.get(ext, "unknown")


def extract_file_path(query: str) -> Optional[str]:
    """
    Extract file path from user query using regex patterns.
    
    Args:
        query: User's query text
        
    Returns:
        Extracted file path or None
    """
    path_patterns = [
        r'([A-Za-z]:[\\\/][^\s\'"]+\.[a-zA-Z0-9]+)',  # Windows with extension
        r'([A-Za-z]:[\\\/][^\s\'"]+)',  # Windows without extension
        r'(\/[^\s\'"]+\.[a-zA-Z0-9]+)',  # Unix path
    ]
    
    for pattern in path_patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1)
    return None


def matches_patterns(text: str, patterns: list) -> bool:
    """
    Check if text matches any of the given regex patterns.
    
    Args:
        text: Text to check
        patterns: List of regex patterns
        
    Returns:
        True if any pattern matches
    """
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


# =============================================================================
# INTENT DETECTION NODE
# =============================================================================

def intent_decision_node(state: CodeAgentState) -> CodeAgentState:
    """
    Analyze user query and determine the appropriate intent.
    
    Uses pattern matching first for efficiency, falls back to LLM
    for ambiguous queries.
    
    Args:
        state: Current agent state with user_query
        
    Returns:
        Updated state with intent field set
    """
    user_query = state.get("user_query", "")
    logger.info(f"Processing intent for query: {user_query[:50]}...")
    
    # Pattern-based intent detection (fast path)
    if matches_patterns(user_query, FILE_PATTERNS):
        state["intent"] = Intent.FILE_READ.value
        logger.info(f"Detected intent via pattern: {Intent.FILE_READ.value}")
        return state
    
    if matches_patterns(user_query, REVIEW_PATTERNS):
        state["intent"] = Intent.CODE_REVIEW.value
        logger.info(f"Detected intent via pattern: {Intent.CODE_REVIEW.value}")
        return state
    
    if matches_patterns(user_query, REFACTOR_PATTERNS):
        state["intent"] = Intent.REFACTOR.value
        logger.info(f"Detected intent via pattern: {Intent.REFACTOR.value}")
        return state
    
    if matches_patterns(user_query, TEST_PATTERNS):
        state["intent"] = Intent.TEST_GEN.value
        logger.info(f"Detected intent via pattern: {Intent.TEST_GEN.value}")
        return state
    
    if matches_patterns(user_query, DOC_PATTERNS):
        state["intent"] = Intent.DOCUMENTATION.value
        logger.info(f"Detected intent via pattern: {Intent.DOCUMENTATION.value}")
        return state
    
    if matches_patterns(user_query, OPTIMIZE_PATTERNS):
        state["intent"] = Intent.OPTIMIZE.value
        logger.info(f"Detected intent via pattern: {Intent.OPTIMIZE.value}")
        return state
    
    # LLM-based intent classification (fallback)
    prompt = f"""Classify this coding request into ONE category:
- generate: create new code
- debug: fix bugs or errors
- explain: explain code or concepts
- code_review: review code quality
- refactor: improve code structure
- test_gen: generate tests
- documentation: add docs/comments
- optimize: improve performance
- common: non-coding question

Reply with ONLY the category name.

Request: {user_query}"""
    
    response = get_llm_response(prompt).strip().lower()
    logger.info(f"LLM classified intent as: {response}")
    
    # Validate intent
    valid_intents = [i.value for i in Intent]
    if response in valid_intents:
        state["intent"] = response
    else:
        state["intent"] = Intent.GENERATE.value
        logger.warning(f"Invalid intent '{response}', defaulting to generate")
    
    return state


# =============================================================================
# SAFETY NODE
# =============================================================================

def safety_check_node(state: CodeAgentState) -> CodeAgentState:
    """
    Check for potentially dangerous file paths or operations.
    
    Blocks access to system directories and sensitive files.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state, potentially with blocked intent
    """
    user_query = state.get("user_query", "").lower()
    
    for blocked in BLOCKED_PATHS:
        if blocked.lower() in user_query:
            logger.warning(f"Blocked access attempt to: {blocked}")
            state["llm_result"] = f"⚠️ Access denied: Cannot access '{blocked}' for security reasons."
            state["intent"] = Intent.COMMON.value
            state["error"] = "Security blocked"
            return state
    
    return state


# =============================================================================
# UNDERSTANDING & PLANNING NODES
# =============================================================================

def understanding_node(state: CodeAgentState) -> CodeAgentState:
    """
    Analyze and summarize the user's coding problem.
    
    Args:
        state: Current agent state with user_query
        
    Returns:
        Updated state with understood_problem
    """
    logger.info("Understanding the problem...")
    
    prompt = f"""Analyze this coding request and provide a clear, concise summary (2-3 sentences):

Request: {state['user_query']}

Summary:"""
    
    state["understood_problem"] = get_llm_response(prompt)
    return state


def planning_node(state: CodeAgentState) -> CodeAgentState:
    """
    Create a step-by-step plan to solve the problem.
    
    Args:
        state: Current agent state with understood_problem
        
    Returns:
        Updated state with plan
    """
    logger.info("Creating solution plan...")
    
    prompt = f"""Create a numbered step-by-step plan to solve this problem:

Problem: {state.get('understood_problem', state.get('user_query', ''))}

Plan:"""
    
    state["plan"] = get_llm_response(prompt)
    return state


# =============================================================================
# CODE GENERATION NODE
# =============================================================================

def code_generation_node(state: CodeAgentState) -> CodeAgentState:
    """
    Generate code based on the problem understanding and plan.
    
    Args:
        state: Current agent state with understood_problem and plan
        
    Returns:
        Updated state with generated code
    """
    logger.info("Generating code...")
    
    prompt = f"""Generate clean, well-documented code for this problem:

Problem: {state.get('understood_problem', '')}

Plan: {state.get('plan', '')}

Requirements:
- Include clear comments
- Follow best practices
- Handle edge cases

Code:"""
    
    state["code"] = get_llm_response(prompt)
    return state


# =============================================================================
# EXPLANATION NODE
# =============================================================================

def explanation_node(state: CodeAgentState) -> CodeAgentState:
    """
    Explain code or coding concepts clearly.
    
    Args:
        state: Current agent state with code or user_query
        
    Returns:
        Updated state with explanation and llm_result
    """
    logger.info("Generating explanation...")
    
    code_to_explain = state.get("code") or state.get("user_query", "")
    
    if not code_to_explain:
        state["llm_result"] = "No code available to explain."
        return state
    
    prompt = f"""Explain this code clearly for a developer:

{code_to_explain}

Provide:
1. What the code does (overview)
2. Key components and their purpose
3. Important implementation details"""
    
    explanation = get_llm_response(prompt)
    state["explanation"] = explanation
    
    if state.get("code"):
        state["llm_result"] = f"**Generated Code:**\n```\n{state['code']}\n```\n\n**Explanation:**\n{explanation}"
    else:
        state["llm_result"] = f"**Explanation:**\n{explanation}"
    
    return state


# =============================================================================
# DEBUG NODE
# =============================================================================

def debug_node(state: CodeAgentState) -> CodeAgentState:
    """
    Analyze code for bugs and provide fixes.
    
    Args:
        state: Current agent state with code in user_query
        
    Returns:
        Updated state with fixed code
    """
    logger.info("Debugging code...")
    
    prompt = f"""Debug this code and provide fixed version:

{state['user_query']}

Provide:
1. Identified issues
2. Fixed code
3. Explanation of fixes"""
    
    fixed_code = get_llm_response(prompt)
    state["code"] = fixed_code
    state["llm_result"] = fixed_code
    return state


# =============================================================================
# CODE REVIEW NODE (NEW)
# =============================================================================

def code_review_node(state: CodeAgentState) -> CodeAgentState:
    """
    Review code for quality, best practices, and potential issues.
    
    Args:
        state: Current agent state with code to review
        
    Returns:
        Updated state with review results
    """
    logger.info("Reviewing code...")
    
    code = state.get("file_content") or state.get("user_query", "")
    
    prompt = f"""Perform a comprehensive code review:

```
{code[:8000]}
```

Review for:
1. **Code Quality**: Readability, naming, structure
2. **Best Practices**: Design patterns, DRY, SOLID
3. **Potential Bugs**: Edge cases, error handling
4. **Security**: Input validation, vulnerabilities
5. **Performance**: Inefficiencies, optimizations

Format as a structured review with severity levels (🔴 Critical, 🟡 Warning, 🟢 Suggestion)."""
    
    review = get_llm_response(prompt)
    state["llm_result"] = f"## 📋 Code Review\n\n{review}"
    return state


# =============================================================================
# REFACTOR NODE (NEW)
# =============================================================================

def refactor_node(state: CodeAgentState) -> CodeAgentState:
    """
    Suggest and implement code refactoring improvements.
    
    Args:
        state: Current agent state with code to refactor
        
    Returns:
        Updated state with refactored code
    """
    logger.info("Refactoring code...")
    
    code = state.get("file_content") or state.get("user_query", "")
    
    prompt = f"""Refactor this code for better quality:

```
{code[:8000]}
```

Apply:
1. Extract functions for repeated code
2. Improve naming conventions
3. Add proper error handling
4. Simplify complex logic
5. Follow SOLID principles

Provide the refactored code with explanations of changes."""
    
    refactored = get_llm_response(prompt)
    state["code"] = refactored
    state["llm_result"] = f"## 🔄 Refactored Code\n\n{refactored}"
    return state


# =============================================================================
# TEST GENERATION NODE (NEW)
# =============================================================================

def test_generation_node(state: CodeAgentState) -> CodeAgentState:
    """
    Generate unit tests for the provided code.
    
    Args:
        state: Current agent state with code to test
        
    Returns:
        Updated state with generated tests
    """
    logger.info("Generating tests...")
    
    code = state.get("file_content") or state.get("user_query", "")
    language = state.get("language", "python")
    
    prompt = f"""Generate comprehensive unit tests for this {language} code:

```
{code[:6000]}
```

Include:
1. Test for normal cases
2. Test for edge cases
3. Test for error handling
4. Mock external dependencies if needed

Use pytest for Python, Jest for JavaScript, or appropriate testing framework."""
    
    tests = get_llm_response(prompt)
    state["llm_result"] = f"## 🧪 Generated Tests\n\n{tests}"
    return state


# =============================================================================
# DOCUMENTATION NODE (NEW)
# =============================================================================

def documentation_node(state: CodeAgentState) -> CodeAgentState:
    """
    Add documentation to code including docstrings and comments.
    
    Args:
        state: Current agent state with code to document
        
    Returns:
        Updated state with documented code
    """
    logger.info("Adding documentation...")
    
    code = state.get("file_content") or state.get("user_query", "")
    
    prompt = f"""Add comprehensive documentation to this code:

```
{code[:8000]}
```

Add:
1. Module/file docstring with description
2. Function/method docstrings with Args, Returns, Raises
3. Class docstrings with Attributes
4. Inline comments for complex logic
5. Type hints where appropriate

Return the fully documented code."""
    
    documented = get_llm_response(prompt)
    state["code"] = documented
    state["llm_result"] = f"## 📝 Documented Code\n\n{documented}"
    return state


# =============================================================================
# OPTIMIZE NODE (NEW)
# =============================================================================

def optimize_node(state: CodeAgentState) -> CodeAgentState:
    """
    Optimize code for better performance.
    
    Args:
        state: Current agent state with code to optimize
        
    Returns:
        Updated state with optimized code
    """
    logger.info("Optimizing code...")
    
    code = state.get("file_content") or state.get("user_query", "")
    
    prompt = f"""Optimize this code for better performance:

```
{code[:8000]}
```

Focus on:
1. Algorithm efficiency (time complexity)
2. Memory usage (space complexity)
3. Reducing unnecessary operations
4. Caching/memoization where beneficial
5. Using efficient data structures

Provide optimized code with performance analysis."""
    
    optimized = get_llm_response(prompt)
    state["code"] = optimized
    state["llm_result"] = f"## ⚡ Optimized Code\n\n{optimized}"
    return state


# =============================================================================
# COMMON/FALLBACK NODE
# =============================================================================

def common_node(state: CodeAgentState) -> CodeAgentState:
    """
    Handle non-coding queries with a helpful response.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with appropriate message
    """
    logger.info("Handling non-coding query...")
    
    if state.get("error"):
        return state  # Already has error message
    
    prompt = f"""The user asked: {state.get('user_query', '')}

This appears to be a general question. Provide a helpful, concise response.
If it's completely unrelated to programming, politely explain that you're a coding assistant."""
    
    response = get_llm_response(prompt)
    state["llm_result"] = response
    return state


# =============================================================================
# FILE OPERATIONS
# =============================================================================

def folder_list_node(state: CodeAgentState) -> CodeAgentState:
    """
    List files in the workspace directory.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with file listing
    """
    logger.info("Listing workspace files...")
    
    workspace = "./workspace"
    
    try:
        if not os.path.exists(workspace):
            os.makedirs(workspace)
        
        files = os.listdir(workspace)
        
        if not files:
            state["llm_result"] = "📁 Workspace is empty."
        else:
            file_list = "\n".join([f"  • {f}" for f in files])
            state["llm_result"] = f"📁 **Workspace Files:**\n{file_list}"
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        state["llm_result"] = f"Error listing files: {str(e)}"
    
    return state


def file_read_node(state: CodeAgentState) -> CodeAgentState:
    """
    Read and analyze a file based on user request.
    
    Args:
        state: Current agent state with user_query containing file path
        
    Returns:
        Updated state with file content and analysis
    """
    logger.info("Reading file...")
    
    user_query = state.get("user_query", "")
    file_path = extract_file_path(user_query)
    
    if not file_path:
        # Try LLM extraction
        prompt = f"Extract ONLY the file path from: {user_query}"
        file_path = get_llm_response(prompt).strip()
    
    if not file_path or not os.path.exists(file_path):
        state["llm_result"] = f"❌ File not found: '{file_path}'\n\nProvide a valid path like: D:\\folder\\file.py"
        return state
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        state["llm_result"] = f"❌ Error reading file: {str(e)}"
        return state
    
    state["file_path"] = file_path
    state["file_content"] = content
    state["language"] = detect_language(file_path)
    
    # Analyze the file
    prompt = f"""Analyze this {state['language']} file: {os.path.basename(file_path)}

User request: {user_query}

```
{content[:8000]}
```

Provide helpful analysis based on what the user wants."""
    
    analysis = get_llm_response(prompt)
    state["llm_result"] = f"📄 **{os.path.basename(file_path)}**\n\n{analysis}"
    
    return state


def file_edit_node(state: CodeAgentState) -> CodeAgentState:
    """
    Modify file content based on user request.
    
    Args:
        state: Current agent state with file_content and user_query
        
    Returns:
        Updated state with modified content
    """
    logger.info("Editing file...")
    
    prompt = f"""Modify this code based on the request:

Request: {state['user_query']}

Current code:
```
{state.get('file_content', '')[:8000]}
```

Return ONLY the modified code."""
    
    updated = get_llm_response(prompt)
    state["updated_content"] = updated
    return state


def confirm_node(state: CodeAgentState) -> CodeAgentState:
    """
    Prepare confirmation message for file changes.
    
    Args:
        state: Current agent state with updated_content
        
    Returns:
        Updated state with confirmation message
    """
    file_path = state.get('file_path', 'unknown')
    state["llm_result"] = f"📝 **Changes ready for:** {file_path}\n\nReview and confirm to apply changes."
    return state


def write_file_node(state: CodeAgentState) -> CodeAgentState:
    """
    Write updated content to file.
    
    Args:
        state: Current agent state with file_path and updated_content
        
    Returns:
        Updated state with success/error message
    """
    logger.info("Writing file...")
    
    file_path = state.get("file_path", "")
    updated_content = state.get("updated_content", "")
    
    if not file_path or not updated_content:
        state["llm_result"] = "❌ Error: No file path or content to write."
        return state
    
    try:
        # Ensure workspace exists
        workspace = "./workspace"
        os.makedirs(workspace, exist_ok=True)
        
        full_path = os.path.join(workspace, os.path.basename(file_path))
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        state["llm_result"] = f"✅ File saved: {full_path}"
        logger.info(f"File written successfully: {full_path}")
    except Exception as e:
        logger.error(f"Error writing file: {e}")
        state["llm_result"] = f"❌ Error writing file: {str(e)}"
    
    return state
