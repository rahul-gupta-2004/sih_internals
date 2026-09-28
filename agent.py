import re
import ollama
from router import classify_task, select_model
from tools import execute_python, kb_search, write_word_doc, write_text_file
from audit import log_event


def call_llm(model: str, prompt: str, system: str = "") -> str:
    """Call a local Ollama model and return the response text."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


def run_agent(task: str, has_image: bool = False) -> dict:
    """
    Main agentic entry point.
    1. Classify the task
    2. Select the model
    3. Execute the appropriate pipeline
    4. Return a structured result
    """
    result = {
        "task": task,
        "task_type": None,
        "model_used": None,
        "plan": [],
        "output": "",
        "artifacts": [],
        "kb_hits": [],
    }

    # Step 1: Classify
    task_type = classify_task(task, has_image=has_image)
    result["task_type"] = task_type
    log_event("CLASSIFY", f"Task classified as: {task_type}", metadata={"task": task[:120]})

    # Step 2: Route
    model = select_model(task_type)
    result["model_used"] = model
    log_event("ROUTE", f"Selected model: {model}", model=model)

    # Step 3: Dispatch based on task type
    if task_type == "code":
        return _run_code_task(task, model, result)
    elif task_type == "vision":
        return _run_vision_task(task, model, result)
    elif task_type == "document":
        return _run_document_task(task, model, result)
    else:
        return _run_general_task(task, model, result)


def _run_code_task(task: str, model: str, result: dict) -> dict:
    """Generate code, execute it, and verify."""
    result["plan"] = [
        "Generate Python code from the request",
        "Execute code in sandbox",
        "Capture output and verify",
    ]

    # Generate code
    system = (
        "You are a Python code generator. Output ONLY valid Python code. "
        "No explanations, no markdown fences. Include print() statements to show results."
    )
    code = call_llm(model, task, system=system)
    code = _strip_code_fences(code)
    log_event("GENERATE", "Code generated", model=model, metadata={"code_len": len(code)})

    # Execute
    exec_result = execute_python(code)
    log_event(
        "EXECUTE",
        f"Sandbox exit code: {exec_result['exit_code']}",
        model=model,
        metadata={"success": exec_result["success"]},
    )

    # Save code artifact
    code_path = write_text_file("generated_code.py", code)
    result["artifacts"].append(str(code_path))

    result["output"] = (
        f"**Generated Code:**\n\n```python\n{code}\n```\n\n"
        f"**Execution Result (exit code {exec_result['exit_code']}):**\n\n"
        f"```\n{exec_result['stdout']}\n```"
    )
    if exec_result["stderr"]:
        result["output"] += f"\n\n**Stderr:**\n```\n{exec_result['stderr']}\n```"

    return result


def _run_document_task(task: str, model: str, result: dict) -> dict:
    """Search KB, then draft a document using retrieved context."""
    result["plan"] = [
        "Search local knowledge base for relevant context",
        "Draft document using retrieved context",
        "Write .docx file to outputs/",
    ]

    # Search KB
    hits = kb_search(task, top_k=3)
    result["kb_hits"] = hits
    log_event("KB_SEARCH", f"Retrieved {len(hits)} chunks from local KB", model=model)

    context = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits) if hits else "(No KB context found)"

    # Draft
    system = (
        "You are an industrial documentation assistant. "
        "Draft a formal approval note or document based on the request and any provided context. "
        "Use professional language. Structure with clear paragraphs."
    )
    prompt = f"Request: {task}\n\nContext from local knowledge base:\n{context}"
    draft = call_llm(model, prompt, system=system)
    log_event("DRAFT", "Document drafted", model=model)

    # Write .docx
    doc_path = write_word_doc("approval_note.docx", "Approval Note", draft)
    result["artifacts"].append(str(doc_path))
    log_event("WRITE", f"Wrote deliverable: {doc_path.name}", model=model)

    result["output"] = f"**Drafted Document:**\n\n{draft}\n\n---\n\n📄 Saved as `{doc_path.name}`"
    if hits:
        result["output"] += "\n\n**Sources used:**\n" + "\n".join(f"- {h['source']}" for h in hits)

    return result


def _run_vision_task(task: str, model: str, result: dict) -> dict:
    """Handle vision/OCR tasks. Requires an image path in the task string."""
    result["plan"] = [
        "Load image",
        "Run local OCR / vision model",
        "Return extracted content",
    ]

    # For OCR, the user must provide an image path in the prompt
    # Example task: "read this image: /path/to/scan.png"
    match = re.search(r"(/[^\s]+\.(?:png|jpg|jpeg|pdf))", task, re.IGNORECASE)
    if not match:
        result["output"] = (
            "Vision task detected, but no image path found in the prompt. "
            "Please include an absolute path to a .png/.jpg/.pdf file."
        )
        return result

    image_path = match.group(1)
    log_event("VISION", f"Running OCR on {image_path}", model=model)

    try:
        response = ollama.chat(
            model=model,
            messages=[{
                "role": "user",
                "content": "Extract all text and describe any diagrams, tables, or drawings in this image. Be thorough.",
                "images": [image_path],
            }],
        )
        extracted = response["message"]["content"]
        log_event("OCR_DONE", "OCR extraction complete", model=model)
        result["output"] = f"**Extracted Content:**\n\n{extracted}"

        # Save as artifact
        txt_path = write_text_file("ocr_output.txt", extracted)
        result["artifacts"].append(str(txt_path))
    except Exception as e:
        log_event("ERROR", f"OCR failed: {e}", model=model)
        result["output"] = f"OCR failed: {e}"

    return result


def _run_general_task(task: str, model: str, result: dict) -> dict:
    """General reasoning — no tools, just direct response."""
    result["plan"] = ["Generate response using general reasoning model"]
    system = "You are a helpful industrial assistant running locally. Answer concisely and accurately."
    output = call_llm(model, task, system=system)
    log_event("GENERATE", "General response generated", model=model)
    result["output"] = output
    return result


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences if the model added them."""
    text = text.strip()
    text = re.sub(r"^```(?:python)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()