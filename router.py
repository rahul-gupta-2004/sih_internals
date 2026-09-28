import re
import ollama

# Model pool — all local, all free
MODELS = {
    "general": "llama3.2:1b",
    "code": "qwen2.5-coder:1.5b",
    "vision": "glm-ocr:latest",
    "embedding": "nomic-embed-text:v1.5",
}

# Keyword rules for fast classification
CODE_KEYWORDS = [
    "code", "python", "script", "function", "program", "calculate",
    "compute", "algorithm", "write a", "implement", "debug", "fix this",
]
VISION_KEYWORDS = [
    "scan", "scanned", "image", "drawing", "p&id", "pid", "photo",
    "picture", "ocr", "read this pdf", "handwritten", "diagram",
]
DOC_KEYWORDS = [
    "summar", "draft", "note", "approval", "report", "letter",
    "memo", "document", "write a note", "compose",
]

def classify_task(prompt: str, has_image: bool = False) -> str:
    """Classify a task into one of: code, vision, document, general."""
    if has_image:
        return "vision"

    p = prompt.lower()

    # Check vision first (most specific)
    if any(kw in p for kw in VISION_KEYWORDS):
        return "vision"

    # Check code
    if any(kw in p for kw in CODE_KEYWORDS):
        return "code"

    # Check document
    if any(kw in p for kw in DOC_KEYWORDS):
        return "document"

    return "general"

def select_model(task_type: str) -> str:
    """Map task type to the appropriate model."""
    if task_type == "code":
        return MODELS["code"]
    if task_type == "vision":
        return MODELS["vision"]
    # document and general both go to llama3.2:1b
    return MODELS["general"]

def get_model_pool() -> dict:
    return MODELS.copy()