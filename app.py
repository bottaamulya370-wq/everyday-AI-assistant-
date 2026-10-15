
import re
from collections import Counter

import streamlit as st
from pypdf import PdfReader


# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Everyday AI Assistant",
    page_icon="🤖",
    layout="wide",
)

# ---------------- STYLING ----------------

st.markdown("""
<style>
.stApp {
    background: #0b1020;
    color: #f5f7ff;
}
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}
h1, h2, h3, p, label {
    color: #f5f7ff;
}
[data-testid="stChatMessage"] {
    border: 1px solid #26324b;
    border-radius: 14px;
    padding: 12px;
}
.stButton button {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hi! Welcome to Everyday AI Assistant. "
                "I can answer built-in questions and help you "
                "find information inside an uploaded PDF."
            ),
        }
    ]

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""


# ---------------- SIMPLE RESPONSE ENGINE ----------------

def words(text):
    return re.findall(r"[a-zA-Z0-9']+", text.lower())


def find_pdf_answer(question, document):
    """Find document sentences sharing keywords with the question."""
    if not document.strip():
        return None

    question_words = set(words(question))
    stop_words = {
        "what", "when", "where", "which", "who", "why", "how",
        "the", "and", "for", "with", "from", "this", "that",
        "are", "was", "were", "does", "can", "you", "tell",
        "about", "please", "explain", "into", "have", "has",
    }
    keywords = question_words - stop_words

    if not keywords:
        return None

    sentences = re.split(r"(?<=[.!?])\s+|\n+", document)
    scored = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue

        sentence_words = set(words(sentence))
        overlap = len(keywords & sentence_words)

        if overlap:
            score = overlap / max(len(keywords), 1)
            scored.append((score, sentence))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = []
    seen = set()

    for score, sentence in scored[:4]:
        if sentence not in seen:
            selected.append(sentence)
            seen.add(sentence)

    return " ".join(selected)


def make_answer(question, language, style, document):
    q = question.lower().strip()

    # Try the uploaded document first.
    document_answer = find_pdf_answer(question, document)
    if document_answer:
        answer = (
            "**From your uploaded PDF:**\n\n"
            + document_answer
            + "\n\nThis is a keyword-based match, so check "
              "the original document for full context."
        )
        return answer

    # Built-in responses; this is not a generative AI model.
    if any(g in q for g in ["hello", "hi", "hey", "hii", "good morning"]):
        answer = (
            "Hello! 👋 Welcome to Everyday AI Assistant. "
            "Ask me a built-in question or upload a PDF "
            "to search its contents."
        )

    elif "your name" in q or "who are you" in q:
        answer = (
            "I am Everyday AI Assistant, a simple, "
            "API-free chatbot built with Python and Streamlit."
        )

    elif "what can you do" in q or "help" == q:
        answer = (
            "I can respond to a few built-in questions and "
            "find keyword-matched information in your uploaded PDF. "
            "I do not currently generate open-ended AI answers "
            "or fetch live news."
        )

    elif "python" in q:
        answer = (
            "Python is a general-purpose programming language "
            "known for readable syntax. It is used in automation, "
            "web development, data analysis, and machine learning."
        )

    elif "artificial intelligence" in q or re.search(r"\bai\b", q):
        answer = (
            "Artificial intelligence (AI) is a field of computing "
            "that develops systems capable of tasks such as "
            "recognizing patterns, understanding language, "
            "and making predictions."
        )

    elif "streamlit" in q:
        answer = (
            "Streamlit is a Python framework for building "
            "interactive web apps, especially for data and "
            "machine-learning projects."
        )

    elif "thank" in q:
        answer = "You're welcome! 😊 Ask another question whenever you're ready."

    else:
        answer = (
            "I don't have a built-in answer for that question yet. "
            "This API-free version does not use a generative AI model. "
            "Try asking about Python, artificial intelligence, or "
            "Streamlit—or upload a PDF and ask about its contents."
        )

    if style == "Concise":
        answer = answer.split("\n\n")[0]
    elif style == "Detailed":
        answer += (
            "\n\n**Next step:** Try asking a more specific question "
            "or upload a relevant PDF for document-based answers."
        )

    # Basic language-specific status note.
    # Full translation requires a translation engine or language model.
    if language != "English":
        answer += (
            f"\n\n*Note: Full {language} translation is not enabled "
            "in this API-free version yet.*"
        )

    return answer


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("⚙️ Settings")

    language = st.selectbox(
        "Response language",
        ["English", "Telugu", "Hindi"],
    )

    style = st.selectbox(
        "Response style",
        ["Balanced", "Concise", "Detailed"],
    )

    st.markdown("---")
    st.subheader("📄 Upload a PDF")

    uploaded_file = st.file_uploader(
        "Choose a PDF document",
        type=["pdf"],
    )

    if uploaded_file:
        try:
            reader = PdfReader(uploaded_file)
            pages = [
                page.extract_text() or ""
                for page in reader.pages
            ]
            st.session_state.pdf_text = "\n".join(pages)[:100000]
            st.success(
                f"PDF loaded: {len(reader.pages)} page(s)"
            )
            if not st.session_state.pdf_text.strip():
                st.warning(
                    "No selectable text found. "
                    "Scanned PDFs need OCR, which is not included."
                )
        except Exception as exc:
            st.error(f"Could not read the PDF: {exc}")
    else:
        st.session_state.pdf_text = ""

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("Runs without a Gemini API key.")
    st.caption("Answers are built-in or extracted from your PDF.")


# ---------------- MAIN CHAT ----------------

st.title("🤖 Everyday AI Assistant")
st.write(
    "Your simple assistant for everyday questions "
    "and searching uploaded PDF documents."
)

st.info(
    "API-free edition: this version does not use a generative "
    "AI model, live web search, or automatic translation."
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Type your question here...")

if question:
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Finding an answer..."):
            answer = make_answer(
                question,
                language,
                style,
                st.session_state.pdf_text,
            )
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
