
import time

from google import genai
from google.genai import errors

from config import API_KEY, MODEL_NAME


# ---------------- CREATE GEMINI CLIENT ----------------

def create_client():
    """Create a Gemini API client."""
    if not API_KEY:
        raise ValueError(
            "Gemini API key is missing. "
            "Add GEMINI_API_KEY in Streamlit Secrets."
        )

    return genai.Client(api_key=API_KEY)


# ---------------- GET AI ANSWER ----------------

def answer_question(
    client,
    question,
    language="English",
    style="Balanced",
    pdf_text="",
    history=None,
):
    """Generate an answer using the Gemini API."""

    if not question or not question.strip():
        return "Please enter a question."

    history = history or []

    # Include recent conversation history.
    previous_messages = []

    for item in history[-6:]:
        role = item.get("role", "user")
        content = item.get("content", "")

        if content:
            previous_messages.append(
                f"{role}: {content}"
            )

    conversation = "\n".join(previous_messages)

    # Limit PDF text to avoid excessively large prompts.
    document_text = (
        pdf_text[:20000] if pdf_text else "No PDF uploaded."
    )

    prompt = f"""
You are Everyday AI Assistant, a helpful and accurate AI assistant.

Instructions:
- Answer the user's question directly and clearly.
- Use simple, beginner-friendly explanations when appropriate.
- Use examples when they help explain a concept.
- Reply in this language: {language}.
- Follow this response style: {style}.
- If the answer is uncertain, explain the uncertainty.
- If a PDF is provided, use its content when relevant.
- Do not invent information that is not supported.

Recent conversation:
{conversation if conversation else "No previous conversation."}

PDF content:
{document_text}

Current user question:
{question.strip()}
"""

    # Retry temporary service errors.
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            answer = response.text

            if answer and answer.strip():
                return answer.strip()

            return (
                "Gemini returned an empty response. "
                "Please try asking in a different way."
            )

        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            details = str(exc)

            # Retry temporary server errors.
            if code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue

            if code == 429:
                return (
                    "Gemini API quota or rate limit reached. "
                    "Please check your API usage and quota "
                    "in Google AI Studio."
                )

            if code == 503:
                return (
                    "Gemini is temporarily unavailable (503). "
                    "Please wait a little and try again."
                )

            if code in (400, 401, 403):
                return (
                    f"Gemini API error ({code}). "
                    "Check your API key, model name, "
                    "and API access permissions. "
                    f"Details: {details}"
                )

            return (
                f"Gemini API error ({code}). "
                f"Details: {details}"
            )

        except Exception as exc:
            return (
                f"Unexpected error: {type(exc).__name__}: {exc}"
            )

    return (
        "Gemini is still unavailable after several attempts. "
        "Please try again later."
    )

