import streamlit as st
from pypdf import PdfReader

from gemini_service import answer_question, create_client


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
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("⚙️ Settings")

    language = st.selectbox(
        "Response language",
        ["English", "Telugu", "Hindi"],
        index=0,
    )

    style = st.selectbox(
        "Response style",
        ["Detailed", "Balanced", "Concise"],
        index=0,
    )

    st.caption("Detailed is selected by default for fuller explanations.")

    st.markdown("---")
    st.subheader("📄 Ask questions about a PDF")

    uploaded_file = st.file_uploader(
        "Upload a text-based PDF",
        type=["pdf"],
    )

    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            pages = [page.extract_text() or "" for page in reader.pages]
            st.session_state.pdf_text = "\n".join(pages)[:20000]
            st.success(f"PDF loaded: {len(reader.pages)} page(s)")
            if not st.session_state.pdf_text.strip():
                st.warning(
                    "No selectable text was found. Scanned PDFs need OCR."
                )
        except Exception as exc:
            st.session_state.pdf_text = ""
            st.error(f"Could not read the PDF: {exc}")
    else:
        st.session_state.pdf_text = ""

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("Powered by the Gemini API. Keep your API key in Streamlit Secrets.")


# ---------------- CLIENT ----------------

@st.cache_resource
def get_gemini_client():
    return create_client()


# ---------------- MAIN CHAT ----------------

st.title("🤖 Everyday AI Assistant")
st.write(
    "Ask questions, learn concepts step by step, get programming help, "
    "or ask questions about an uploaded PDF."
)

st.caption("Tip: For in-depth notes, ask for definitions, step-by-step explanations, examples, applications, and a summary.")

try:
    client = get_gemini_client()
except Exception as exc:
    st.error(
        "The Gemini client could not be initialized. Check that "
        "GEMINI_API_KEY is configured in Streamlit Settings → Secrets."
    )
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask anything...")

if question:
    # Preserve the conversation before adding the new question.
    history = list(st.session_state.messages)

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking and preparing your answer..."):
            answer = answer_question(
                client=client,
                question=question,
                language=language,
                style=style,
                pdf_text=st.session_state.pdf_text,
                history=history,
            )
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
