import streamlit as st
from pypdf import PdfReader

from gemini_service import answer_question, create_client
from web_search import search_web

st.set_page_config(page_title="Everyday AI Assistant", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp { background: #0b1020; color: #f5f7ff; }
.block-container { max-width: 1100px; padding-top: 2rem; }
h1, h2, h3, p, label { color: #f5f7ff; }
[data-testid="stChatMessage"] { border: 1px solid #26324b; border-radius: 14px; padding: 12px; }
.stButton button { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

with st.sidebar:
    st.title("⚙️ Settings")
    mode = st.selectbox("Assistant mode", ["AI Chat", "Live Web Search", "Latest News"])
    language = st.selectbox("Response language", ["English", "Telugu", "Hindi"])
    style = st.selectbox("Response style", ["Detailed", "Balanced", "Concise"], index=0)

    st.divider()
    st.subheader("📄 Ask questions about a PDF")
    uploaded_file = st.file_uploader("Upload a text-based PDF", type=["pdf"])
    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            st.session_state.pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)[:20000]
            st.success(f"Loaded {len(reader.pages)} PDF page(s)")
            if not st.session_state.pdf_text.strip():
                st.warning("No selectable text found. Scanned PDFs need OCR.")
        except Exception as exc:
            st.session_state.pdf_text = ""
            st.error(f"Could not read PDF: {exc}")
    else:
        st.session_state.pdf_text = ""

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Gemini answers questions; Tavily retrieves live web/news sources.")
    st.caption("Keep API keys in Streamlit Secrets or a local .env file—not in GitHub.")

@st.cache_resource
def get_gemini_client():
    return create_client()

st.title("🤖 Everyday AI Assistant")
if mode == "AI Chat":
    st.write("Ask questions, learn concepts, get programming help, or discuss a PDF.")
elif mode == "Live Web Search":
    st.write("Search the web for current information and see source links.")
else:
    st.write("Explore recent news headlines, publication dates, and original articles.")

try:
    client = get_gemini_client()
except Exception:
    st.error("Gemini setup failed. Check GEMINI_API_KEY in Streamlit Settings → Secrets.")
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

placeholder = {
    "AI Chat": "Ask anything...",
    "Live Web Search": "What do you want to search for?",
    "Latest News": "e.g. Today's latest AI and technology news",
}[mode]
question = st.chat_input(placeholder)

if question:
    history = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        answer = ""
        if mode == "AI Chat":
            with st.spinner("Thinking..."):
                answer = answer_question(
                    client=client, question=question, language=language,
                    style=style, pdf_text=st.session_state.pdf_text, history=history
                )
            st.markdown(answer)
        else:
            try:
                is_news = mode == "Latest News"
                query = question
                if is_news and not any(
                    word in question.lower()
                    for word in ("news", "headline", "headlines", "latest", "today")
                ):
                    query = f"Latest news: {question}"

                with st.spinner("Searching the live web..."):
                    results = search_web(query, news_mode=is_news, max_results=8)

                if not results:
                    answer = "The search provider returned no results. Try a more specific query."
                    st.warning(answer)
                else:
                    source_lines = []
                    for i, item in enumerate(results, start=1):
                        source_lines.append(
                            f"[Source {i}]\n"
                            f"Title: {item.get('title', 'Untitled')}\n"
                            f"Published: {item.get('published_date') or 'Date not provided'}\n"
                            f"URL: {item.get('url', '')}\n"
                            f"Snippet: {item.get('content', '')}"
                        )

                    search_context = "\n\n".join(source_lines)[:18000]
                    prompt = f"""
The user's question is: {question}

Answer in {language} with a {style.lower()} level of detail.
Use the live search results below as the evidence for current claims.
Do not claim you lack internet access: the results were just retrieved.
Do not invent facts, dates, or URLs. Mention if dates are missing or sources disagree.
Summarize the most useful points and make clear that article publication date
may differ from the date an event happened. Source links will be displayed below.

LIVE SEARCH RESULTS:
{search_context}
"""
                    with st.spinner("Summarizing the live results with Gemini..."):
                        answer = answer_question(
                            client=client, question=prompt, language=language,
                            style=style, pdf_text="", history=history
                        )
                    st.markdown(answer)
                    st.subheader("📰 Sources")
                    for i, item in enumerate(results, start=1):
                        title = item.get("title") or f"Source {i}"
                        url = item.get("url", "")
                        published = item.get("published_date")
                        snippet = item.get("content", "")
                        with st.container(border=True):
                            if url:
                                st.markdown(f"**[{i}. {title}]({url})**")
                            else:
                                st.markdown(f"**{i}. {title}**")
                            st.caption(f"Published: {published or 'Date not provided'}")
                            if snippet:
                                st.write(snippet[:400])
            except Exception as exc:
                answer = (
                    "Live search failed. Check that TAVILY_API_KEY is configured in "
                    "Streamlit Secrets and that the latest deployment finished. "
                    f"Error: {type(exc).__name__}: {exc}"
                )
                st.error(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
