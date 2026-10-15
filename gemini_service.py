
import time

from google import genai
from google.genai import errors, types

from config import API_KEY, MODEL_NAME


# ---------------- SYSTEM INSTRUCTIONS ----------------

SYSTEM_INSTRUCTION = """
You are Everyday AI Assistant, a helpful, intelligent, and accurate AI tutor.

Your goal is to provide detailed, well-organized, beginner-friendly answers.

Follow these rules:

1. Answer the user's exact question.
2. Explain topics clearly, step by step.
3. Use headings, subheadings, bullet points, and numbered steps.
4. Include examples wherever useful.
5. For programming questions, provide correct code examples.
6. Explain important code line by line when appropriate.
7. For educational notes, include definitions, explanations,
   syntax, examples, important points, and a conclusion.
8. For complex topics, provide sufficient detail rather than
   giving only a short summary.
9. Adjust answer length to the question and the selected style.
10. Reply in the language selected by the user.
11. Use uploaded PDF content when relevant.
12. Do not invent facts, sources, or results.
13. If the question is unclear, ask a relevant clarification.
14. Avoid unnecessary repetition.
"""


# ---------------- CREATE GEMINI CLIENT ----------------

def create_client():
    """Create and return a Gemini API client."""

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
    """Generate a detailed answer using Gemini."""

    if not question or not question.strip():
        return "Please enter a question."

    # Keep only recent conversation messages.
    history = history or []
    previous_messages = []

    for item in history[-6:]:
        role = item.get("role", "user")
        content = item.get("content", "")

        if content:
            previous_messages.append(
                f"{role}: {content}"
            )

    conversation = "\n".join(previous_messages)

    # Limit PDF content to keep the prompt manageable.
    document_text = (
        pdf_text[:20000]
        if pdf_text
        else "No PDF uploaded."
    )

    # Build the user's prompt.
    prompt = f"""
Selected language: {language}

Selected response style: {style}

Recent conversation:
{conversation if conversation else "No previous conversation."}

Uploaded PDF content:
{document_text}

Current user question:
{question.strip()}

Please answer the current question in the selected language
and follow the system instructions.
"""

    # Choose response length based on the selected style.
    token_limits = {
        "Concise": 1024,
        "Balanced": 4096,
        "Detailed": 8192,
    }

    max_tokens = token_limits.get(style, 4096)

    # Retry temporary server errors.
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.5,
                    max_output_tokens=max_tokens,
                ),
            )

            answer = response.text

            if answer and answer.strip():
                return answer.strip()

            return (
                "The AI returned an empty response. "
                "Please try asking again."
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
                    "Check your model quota and billing settings "
                    "in Google AI Studio."
                )

            if code == 503:
                return (
                    "Gemini is temporarily unavailable. "
                    "Please wait and try again."
                )

            if code in (400, 401, 403):
                return (
                    f"Gemini API error ({code}). "
                    "Check your API key, model name, and API access. "
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
