
import streamlit as st
from pypdf import PdfReader

from config import MODEL_NAME
from gemini_service import create_client, answer_question


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Everyday AI Assistant",
    page_icon="🤖",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background-color: #0b1020;
}
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}
h1, h2, h3, p, label {
    color: #f1f5f9;
}
[data-testid="stChatMessage"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.title("🤖 Everyday AI")
    st.caption("Your everyday thinking partner")
    st.divider()

    language = st.selectbox(
        "Response language",
        [
            "English",
            "Telugu",
            "Hindi",
            "Tamil",
            "Kannada",
            "Malayalam",
        ],
    )

    style = st.selectbox(
        "Response style",
        [
            "Balanced",
            "Simple",
            "Detailed",
            "Professional",
            "Exam-oriented",
        ],
    )

    st.divider()
    st.subheader("📄 Ask about a PDF")

    uploaded_pdf = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        help="Upload a text-based PDF to ask questions about its contents.",
    )

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption(f"Model configured: {MODEL_NAME}")


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""


# ---------------- READ PDF ----------------

if uploaded_pdf is not None:
    if st.session_state.pdf_name != uploaded_pdf.name:
        try:
            reader = PdfReader(uploaded_pdf)

            if reader.is_encrypted:
                st.session_state.pdf_text = ""
                st.session_state.pdf_name = None
                st.error(
                    "This PDF is password-protected. "
                    "Please upload an accessible PDF."
                )
            else:
                pages = []
                for page in reader.pages:
                    pages.append(page.extract_text() or "")

                extracted_text = "\n".join(pages).strip()

                st.session_state.pdf_text = extracted_text
                st.session_state.pdf_name = uploaded_pdf.name

                if extracted_text:
                    st.sidebar.success(
                        f"PDF loaded: {uploaded_pdf.name}"
                    )
                else:
                    st.sidebar.warning(
                        "No selectable text was found. "
                        "This may be a scanned PDF."
                    )

        except Exception as exc:
            st.session_state.pdf_text = ""
            st.session_state.pdf_name = None
            st.error(
                f"Could not read this PDF: "
                f"{type(exc).__name__}: {exc}"
            )
else:
    st.session_state.pdf_text = ""
    st.session_state.pdf_name = None


# ---------------- MAIN HEADER ----------------

st.title("🤖 Everyday AI Assistant")
st.write(
    "Ask questions, learn new concepts, and explore your PDF documents."
)

if uploaded_pdf is not None and st.session_state.pdf_text:
    st.info(f"Using PDF: {uploaded_pdf.name}")


# ---------------- DISPLAY CHAT HISTORY ----------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------- CHAT INPUT ----------------

user_question = st.chat_input(
    "Ask anything in your preferred language..."
)

if user_question:
    # Show and save the user's question.
    st.session_state.messages.append({
        "role": "user",
        "content": user_question,
    })

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                client = create_client()

                # Use the conversation before adding the new answer.
                previous_history = st.session_state.messages[:-1]

                reply = answer_question(
                    client=client,
                    question=user_question,
                    language=language,
                    style=style,
                    pdf_text=st.session_state.pdf_text,
                    history=previous_history,
                )

                st.markdown(reply)

            except Exception as exc:
                reply = (
                    f"Could not complete your request: "
                    f"{type(exc).__name__}: {exc}"
                )
                st.error(reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
    })
