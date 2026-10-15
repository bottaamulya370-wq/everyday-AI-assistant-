"""FastAPI backend for the standalone Everyday AI Assistant web frontend.

Run locally from the repository root:
    uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
"""
import os
from io import BytesIO
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pypdf import PdfReader

from gemini_service import answer_question, create_client
from web_search import search_web

app = FastAPI(
    title="Everyday AI Assistant API",
    version="1.0.0",
    description="API for chat, coding help, study planning, PDF Q&A, and web search.",
)

_origins = os.getenv("FRONTEND_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip().rstrip("/") for origin in _origins if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=12000)
    language: Literal["English", "Telugu", "Hindi"] = "English"
    style: Literal["Detailed", "Balanced", "Concise"] = "Balanced"
    history: list[dict[str, str]] = Field(default_factory=list, max_length=12)
    pdf_text: str = Field(default="", max_length=50000)
    task: Literal["chat", "coding", "study_plan", "quiz"] = "chat"

class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    news_mode: bool = False
    max_results: int = Field(default=6, ge=3, le=10)
    language: Literal["English", "Telugu", "Hindi"] = "English"
    style: Literal["Detailed", "Balanced", "Concise"] = "Balanced"

def _ai(question: str, language: str, style: str, pdf_text: str = "", history=None) -> str:
    try:
        client = create_client()
        return answer_question(
            client=client, question=question, language=language,
            style=style, pdf_text=pdf_text, history=history or [],
        )
    except Exception as exc:
        # Do not return secrets or provider exception details to public clients.
        raise HTTPException(status_code=503, detail=f"AI service unavailable ({type(exc).__name__}). Check backend environment variables and provider status.") from None

@app.get("/")
def root():
    return {"name": "Everyday AI Assistant API", "docs": "/docs", "health": "/api/health"}

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "everyday-ai-assistant-api"}

@app.post("/api/chat")
def chat(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be blank.")
    prompts = {
        "chat": question,
        "coding": "Act as a beginner-friendly coding mentor. Explain the likely cause, show a corrected example when useful, and include how to run or test it. Do not claim code was executed.\n\n" + question,
        "study_plan": "Create a realistic study plan with revision, practice, breaks, and buffer time.\n\n" + question,
        "quiz": "Create a short multiple-choice quiz. Clearly mark the correct answer and explain why.\n\n" + question,
    }
    answer = _ai(prompts[payload.task], payload.language, payload.style, payload.pdf_text, payload.history[-8:])
    return {"answer": answer, "task": payload.task}

@app.post("/api/search")
def search(payload: SearchRequest):
    try:
        results = search_web(payload.query.strip(), news_mode=payload.news_mode, max_results=payload.max_results)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Search service unavailable ({type(exc).__name__}). Check TAVILY_API_KEY in backend environment variables.") from None
    evidence = "\n\n".join(
        f"Title: {item.get('title', 'Untitled')}\nDate: {item.get('published_date') or 'Not provided'}\nURL: {item.get('url', '')}\nSnippet: {item.get('content', '')}"
        for item in results
    )[:18000]
    summary = ""
    if evidence:
        prompt = (
            f"Answer this query using only the supplied search evidence: {payload.query}\n"
            "Cite source titles and URLs from the evidence in your summary. Do not invent facts. "
            "State uncertainty where needed.\n\n" + evidence
        )
        summary = _ai(prompt, payload.language, payload.style)
    return {"query": payload.query, "summary": summary, "results": results}

@app.post("/api/pdf")
async def pdf_question(
    question: str,
    language: Literal["English", "Telugu", "Hindi"] = "English",
    style: Literal["Detailed", "Balanced", "Concise"] = "Balanced",
    file: UploadFile = File(...),
):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=415, detail="Please upload a PDF file.")
    raw = await file.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF must be 12 MB or smaller.")
    try:
        reader = PdfReader(BytesIO(raw))
        if len(reader.pages) > 150:
            raise HTTPException(status_code=413, detail="PDF must contain 150 pages or fewer.")
        text = "\n\n".join(f"[Page {i + 1}]\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages))[:30000]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="The PDF could not be read. Please try a valid, text-based PDF.") from None
    if not text.strip():
        raise HTTPException(status_code=422, detail="No selectable text found. Scanned PDFs require OCR.")
    answer = _ai(question.strip() or "Summarize this document and list key takeaways.", language, style, text)
    return {"filename": file.filename or "uploaded.pdf", "pages": len(reader.pages), "answer": answer}
