# SETU-AI: Sovereign On-Premise AI Workbench

An air-gapped, fully offline industrial agentic assistant built with Streamlit and Ollama. It processes confidential engineering documents (P&ID drawings, handwritten field notes, scanned inspection forms) entirely on-premise using local LLMs, with zero external network calls.

## Features

- Vision-based OCR and tag extraction from engineering drawings using Moondream
- Handwritten field note transcription
- Key-value extraction from scanned inspection documents
- Sandboxed wall thickness compliance calculations
- Multi-source synthesis into a downloadable approval note (.docx)
- Real-time network isolation monitoring (zero outbound packets)

## Prerequisites

- Python 3.8+
- Ollama installed and running locally
- Required Ollama models pulled:
  ```
  ollama pull moondream
  ollama pull qwen2.5-coder:1.5b
  ```

## Setup

```bash
python3 -m venv sih_prototype_venv
source sih_prototype_venv/bin/activate
pip install -r requirements.txt
```

## Dataset

Place the following files in the `dataset/` directory:

- `engineering_drawing.jpg` - P&ID engineering drawing
- `field_note.png` - Handwritten field note
- `inspection_report.png` - Scanned inspection form

## Run

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Tech Stack

- Streamlit (UI)
- Ollama (local LLM inference)
- Moondream (vision model)
- Qwen 2.5 Coder 1.5B (reasoning and code)
- python-docx (document generation)
