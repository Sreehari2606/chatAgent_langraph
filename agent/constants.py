from enum import Enum
from dataclasses import dataclass
from typing import Optional

class Intent(str, Enum):
    GENERATE = "generate"
    DEBUG = "debug"
    EXPLAIN = "explain"
    FILE_READ = "file_read"
    FILE_EDIT = "file_edit"
    FOLDER_LIST = "folder_list"
    CODE_REVIEW = "code_review"
    REFACTOR = "refactor"
    TEST_GEN = "test_gen"
    DOCUMENTATION = "documentation"
    OPTIMIZE = "optimize"
    COMMON = "common"

BLOCKED_PATHS = ["/etc", "/usr", ".env", ".ssh", "C:\\Windows", "C:\\Program Files", "node_modules", "__pycache__", ".git"]

CODE_EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "javascript",
    ".tsx": "typescript", ".java": "java", ".cpp": "cpp", ".c": "c", ".cs": "csharp",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php", ".html": "html",
    ".css": "css", ".sql": "sql", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown",
}

FILE_PATTERNS = [r'read.*file', r'analyze.*file', r'open.*file', r'file:?\s*[A-Za-z]:\\', r'[A-Za-z]:\\.*\.(py|js|ts|html|css|json|txt|md)', r'read and analyze', r'check.*file', r'review.*file']
REVIEW_PATTERNS = [r'review.*code', r'code.*review', r'check.*quality', r'best.*practice', r'code.*smell']
REFACTOR_PATTERNS = [r'refactor', r'improve.*code', r'clean.*up', r'restructure', r'simplify']
TEST_PATTERNS = [r'generate.*test', r'write.*test', r'create.*test', r'unit.*test', r'test.*case']
DOC_PATTERNS = [r'add.*docstring', r'document.*code', r'add.*comment', r'generate.*doc', r'documentation']
OPTIMIZE_PATTERNS = [r'optimize', r'performance', r'faster', r'efficient', r'speed.*up']

@dataclass
class NodeResult:
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
