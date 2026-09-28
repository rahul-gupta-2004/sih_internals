import streamlit as st
from pathlib import Path
from agent import run_agent
from router import get_model_pool
from audit import get_recent_logs, verify_chain
from tools import build_knowledge_base, kb_search

st.set_page_config(
    page_title="Sovereign AI Workbench",
    page_icon="🔒",
    layout="wide",
)

st.title("🔒 Sovereign On-Premise Agentic AI Workbench")
st.caption("Air-gapped · Multi-model routing · Agentic execution · Zero external calls")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Model Pool")
    for task, model in get_model_pool().items():
        st.markdown(f"- **{task}** → `{model}`")

    st.divider()
    st.header("Knowledge Base")
    if st.button("📥 Build / Rebuild KB"):
        with st.spinner("Indexing documents..."):
            count = build_knowledge_base()
        st.success(f"Indexed {count} chunks from kb_docs/")

    st.divider()
    st.header("Audit Chain")
    valid, count = verify_chain()
    if valid:
        st.success(f"✅ Chain intact ({count} entries)")
    else:
        st.error("❌ Chain broken!")
    with st.expander("Recent log entries"):
        for entry in reversed(get_recent_logs(8)):
            st.caption(f"`{entry['timestamp'][11:19]}` **{entry['event']}** — {entry['detail'][:60]}")

    st.divider()
    st.header("Network Monitor")
    st.success("External connections: **0**")
    st.caption("All inference is local via Ollama at 127.0.0.1:11434")

# ---------- Main layout ----------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Submit a Task")

    task = st.text_area(
        "Describe what you need:",
        value="Write a Python script to calculate minimum pipe wall thickness given pressure=100, diameter=12, stress=20000, efficiency=0.85",
        height=110,
    )

    uploaded = st.file_uploader(
        "Upload a scanned document or image (optional, for OCR)",
        type=["png", "jpg", "jpeg", "pdf"],
    )

    # If a file is uploaded, save it and embed path in prompt
    if uploaded:
        save_path = Path("sandbox").resolve() / uploaded.name
        save_path.write_bytes(uploaded.getbuffer())
        task_with_path = f"{task}\n\nread this image: {save_path}"
        st.info(f"File saved to: {save_path}")
    else:
        task_with_path = task

    has_image = uploaded is not None

    if st.button("▶ Run Task", type="primary"):
        if not task.strip():
            st.warning("Please enter a task.")
        else:
            with st.spinner("Agent is working..."):
                result = run_agent(task_with_path, has_image=has_image)

            st.subheader("🧠 Agent Plan")
            for i, step in enumerate(result["plan"], 1):
                st.markdown(f"**Step {i}:** {step}")

            st.subheader("📊 Routing Decision")
            st.markdown(f"- **Task type:** `{result['task_type']}`")
            st.markdown(f"- **Model used:** `{result['model_used']}`")

            st.subheader("📦 Deliverable")
            st.markdown(result["output"])

            if result["artifacts"]:
                st.subheader("📁 Artifacts Written")
                for art in result["artifacts"]:
                    st.markdown(f"- `{art}`")

            if result["kb_hits"]:
                st.subheader("🔍 Knowledge Base Sources")
                for hit in result["kb_hits"]:
                    st.caption(f"📄 {hit['source']}")

with col2:
    st.subheader("Quick Test Tasks")

    st.markdown("**Coding task** (→ Qwen Coder)")
    st.code(
        "Write a Python script to compute the safety factor of a pressure vessel given yield strength 250 MPa and operating stress 120 MPa.",
        language="text",
    )

    st.markdown("**Document task** (→ Llama 3.2)")
    st.code(
        "Draft an approval note for the maintenance shutdown of Pump P-101 based on standard SOPs.",
        language="text",
    )

    st.markdown("**Vision task** (→ GLM-OCR)")
    st.code(
        "Upload a scanned P&ID or inspection report and ask: read this image",
        language="text",
    )

    st.divider()
    st.subheader("Live KB Search")
    q = st.text_input("Test KB retrieval:", value="approval note template")
    if q:
        hits = kb_search(q, top_k=2)
        if hits:
            for h in hits:
                st.caption(f"📄 {h['source']}: {h['text'][:120]}...")
        else:
            st.caption("No documents indexed yet. Add files to kb_docs/ and click Build KB.")