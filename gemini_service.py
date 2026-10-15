```python
import time

from google import genai
from google.genai import errors, types

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
    """Generate an answer using Gemini and Google Search."""

    if not question or not question.strip():
        return "Please enter a question."

    history = history or []

    # Include recent conversation history.
    previous_messages = []

    for item in history[-6:]:
        role = item.get("role", "user")
        content = item.get("content", "")

        if content:
            previous_messages.append(f"{role}: {content}")

    conversation = "\n".join(previous_messages)

    # Limit PDF text to avoid excessively large prompts.
    document_text = (
        pdf_text[:20000] if pdf_text else "No PDF uploaded."
    )

    prompt = f"""
You are Everyday AI Assistant, a helpful and accurate AI assistant.

Instructions:
- Answer the user's question directly and clearly.
- Use simple, beginner-friendly explanations.
- Give examples when useful.
- Reply in this language: {language}.
- Follow this response style: {style}.
- Use the uploaded PDF when relevant.
- Do not invent facts or sources.
- For current news, today's events, recent updates, and other
  time-sensitive questions, use Google Search to find current
  information when needed.
- Clearly distinguish verified facts from uncertainty.
- Include source links in your answer when relevant.

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
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            google_search=types.GoogleSearch()
                        )
                    ]
                ),
            )

            answer = response.text

            if answer and answer.strip():
                return answer.strip()

            return (
                "Gemini returned an empty answer. "
                "Please try asking again."
            )

        except errors.APIError as exc:
            code = getattr(exc, "code", None)
            details = str(exc)

            print(f"Gemini API error code: {code}")
            print(f"Gemini API error details: {details}")

            # Retry temporary server errors.
            if code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue

            if code == 429:
                return (
                    "Gemini API quota or rate limit reached. "
                    "Check your Google AI Studio usage and quota. "
                    "Adding Google Search does not bypass API limits."
                )

            if code == 503:
                return (
                    "Gemini is temporarily unavailable. "
                    "Please try again later."
                )

            if code in (400, 401, 403):
                return (
                    f"Gemini API error ({code}): {details}. "
                    "Check your API key, model name, "
                    "model support for Google Search, and permissions."
                )

            return f"Gemini API error ({code}): {details}"

        except Exception as exc:
            print(
                f"Unexpected error: {type(exc).__name__}: {exc}"
            )
            return (
                f"Unexpected error: {type(exc).__name__}: {exc}"
            )

    return (
        "Gemini is still unavailable after several attempts. "
        "Please try again later."
    )
