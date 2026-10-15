import io
import json
import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from pypdf import PdfReader

from config import API_KEY
from gemini_service import answer_question, create_client
from web_search import search_web

st.set_page_config(page_title="Everyday AI Assistant", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.stApp { background: #0b1020; color: #f5f7ff; }
.block-container { max-width: 1150px; padding-top: 1.2rem; padding-left: clamp(0.75rem, 3vw, 2rem); padding-right: clamp(0.75rem, 3vw, 2rem); }\n@media (max-width: 640px) { .block-container { padding-top: 0.6rem; } h1 { font-size: 1.7rem !important; } [data-testid="stMetric"] { padding: 8px; } }
h1, h2, h3, p, label { color: #f5f7ff; }
[data-testid="stChatMessage"] { border: 1px solid #26324b; border-radius: 14px; padding: 12px; }
.stButton button { border-radius: 10px; }
div[data-testid="stMetric"] { background: #121b30; padding: 12px; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

MODES = ["AI Chat", "Live Web Search", "Latest News", "PDF Study Assistant",
         "Coding Assistant", "Study Planner", "Quiz Generator", "Daily Life Organizer", "CSV/Excel Analysis"]

if "messages_by_mode" not in st.session_state:
    st.session_state.messages_by_mode = {m: [] for m in MODES}
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = ""

@st.cache_resource
def get_gemini_client():
    return create_client()

def ask_ai(question, language, style, pdf_text="", history=None):
    """Initialize Gemini only when a tool actually needs it."""
    try:
        client = get_gemini_client()
    except Exception as exc:
        return f"Gemini setup failed: {exc}\n\nCheck GEMINI_API_KEY in Streamlit Secrets."
    return answer_question(client=client, question=question, language=language,
                           style=style, pdf_text=pdf_text, history=history or [])

def extract_pdf(upload):
    reader = PdfReader(upload)
    text = "\n\n".join(f"[Page {i + 1}]\n{page.extract_text() or ''}"
                         for i, page in enumerate(reader.pages))
    return text[:50000], len(reader.pages)

def clean_json(text):
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    return json.loads(text)

st.sidebar.title("⚙️ Everyday AI")
mode = st.sidebar.selectbox("Choose a tool", MODES)
language = st.sidebar.selectbox("Response language", ["English", "Telugu", "Hindi"])
style = st.sidebar.selectbox("Answer detail", ["Detailed", "Balanced", "Concise"], index=1)
st.sidebar.divider()
st.sidebar.caption("Keys stay in Streamlit Secrets or your local .env file. Never commit API keys to GitHub.")
if st.sidebar.button("🗑️ Clear this tool's chat", use_container_width=True):
    st.session_state.messages_by_mode[mode] = []
    st.rerun()

st.title("🤖 Everyday AI Assistant")
st.caption("One workspace for learning, research, coding, documents, planning, quizzes, and data.")

if mode == "AI Chat":
    st.write("Ask questions, learn concepts, or get beginner-friendly explanations.")
    history = st.session_state.messages_by_mode[mode]
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if history:
        transcript = "\\n\\n".join(
            f"{'You' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history
        )
        st.download_button("⬇️ Export conversation", transcript, "chat_transcript.txt", "text/plain")
    question = st.chat_input("Ask anything...")
    if question:
        st.session_state.messages_by_mode[mode].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ask_ai(question, language, style, st.session_state.pdf_text, history)
            st.markdown(answer)
        st.session_state.messages_by_mode[mode].append({"role": "assistant", "content": answer})

elif mode in ("Live Web Search", "Latest News"):
    is_news = mode == "Latest News"
    st.write("Search current web pages and inspect source links." if not is_news else
             "Find recent headlines and open the original articles.")
    query = st.text_input("Search topic", placeholder="e.g. latest AI developments in India")
    limit = st.slider("Maximum sources", 3, 10, 6)
    if st.button("🔎 Search", type="primary") and query.strip():
        try:
            with st.spinner("Searching the web..."):
                results = search_web(query.strip(), news_mode=is_news, max_results=limit)
            if not results:
                st.info("No results returned. Try a more specific search.")
            else:
                context = "\n\n".join(
                    f"Title: {r.get('title','Untitled')}\nDate: {r.get('published_date') or 'Not provided'}\n"
                    f"URL: {r.get('url','')}\nSnippet: {r.get('content','')}"
                    for r in results
                )[:18000]
                with st.spinner("Preparing evidence-based summary..."):
                    summary = ask_ai(
                        f"Answer the query: {query}\nSummarize using only the supplied search evidence. "
                        f"Do not invent details. State uncertainty and distinguish publication dates from event dates.\n\n{context}",
                        language, style)
                st.markdown(summary)
                st.subheader("Sources")
                for i, item in enumerate(results, 1):
                    with st.container(border=True):
                        title = item.get("title") or f"Source {i}"
                        url = item.get("url", "")
                        if url:
                            st.markdown(f"**[{i}. {title}]({url})**")
                        else:
                            st.markdown(f"**{i}. {title}**")
                        st.caption(f"Published: {item.get('published_date') or 'Date not provided'}")
                        st.write((item.get("content") or "")[:500])
        except Exception as exc:
            st.error(f"Search failed ({type(exc).__name__}). Check TAVILY_API_KEY in Streamlit Secrets and try again.")

elif mode == "PDF Study Assistant":
    st.write("Upload a text-based PDF, then summarize it or ask questions grounded in its contents.")
    upload = st.file_uploader("Choose a PDF", type=["pdf"], key="study_pdf")
    if upload:
        try:
            text, pages = extract_pdf(upload)
            st.session_state.pdf_text = text
            st.session_state.pdf_name = upload.name
            st.success(f"Loaded {upload.name} • {pages} page(s)")
            if not text.strip():
                st.warning("No selectable text found. Scanned PDFs need OCR before this tool can read them.")
            task = st.selectbox("What would you like to do?", [
                "Summarize this PDF", "Make exam notes", "Explain in simple words",
                "Generate important questions", "Ask my own question"])
            own_question = st.text_input("Your question (used for Ask my own question)",
                                         placeholder="e.g. Explain chapter 2")
            if st.button("📘 Process PDF", type="primary"):
                prompts = {
                    "Summarize this PDF": "Summarize this document by section and list key takeaways.",
                    "Make exam notes": "Create structured exam notes with definitions, headings, examples, and important points.",
                    "Explain in simple words": "Explain the document in beginner-friendly language with examples.",
                    "Generate important questions": "Generate likely exam questions with concise model answers.",
                    "Ask my own question": own_question.strip()
                }
                if task == "Ask my own question" and not own_question.strip():
                    st.warning("Enter a question first.")
                else:
                    with st.spinner("Reading the PDF..."):
                        st.markdown(ask_ai(prompts[task], language, style, text))
        except Exception as exc:
            st.error(f"Could not read this PDF: {type(exc).__name__}: {exc}")
    else:
        st.info("Upload a PDF to begin. Scanned/image-only PDFs are not supported without OCR.")

elif mode == "Coding Assistant":
    st.write("Get code explanations, debugging help, and beginner-friendly solutions.")
    task = st.selectbox("Task", ["Explain code", "Debug an error", "Write code", "Review/improve code"])
    language_name = st.selectbox("Programming language", ["Python", "C", "C++", "Java", "HTML/CSS/JavaScript", "Other"])
    code = st.text_area("Paste your code or error (if relevant)", height=220)
    goal = st.text_area("What do you want help with?", placeholder="Describe the expected output, error message, or project requirement.")
    if st.button("💻 Get coding help", type="primary"):
        if not goal.strip() and not code.strip():
            st.warning("Add code, an error, or describe what you want to build.")
        else:
            prompt = f"Task: {task}\nProgramming language: {language_name}\nUser request: {goal}\nCode/error:\n{code}\n\nGive a correct beginner-friendly response. If debugging, identify the likely cause, provide corrected code, and explain how to run/test it. Do not claim code was executed."
            with st.spinner("Working on your code..."):
                st.markdown(ask_ai(prompt, language, style))

elif mode == "Study Planner":
    st.write("Create a practical timetable based on your subjects, exam date, and available study time.")
    subjects = st.text_input("Subjects/topics (comma-separated)", placeholder="Mathematical Logic, Python, AI")
    exam_date = st.date_input("Exam or target date", value=date.today() + timedelta(days=7), min_value=date.today())
    hours = st.slider("Available study hours per day", 1, 12, 3)
    start_time = st.selectbox("Preferred start time", ["6:00 AM", "7:00 AM", "8:00 AM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM"])
    weak = st.text_input("Topics you find difficult (optional)")
    if st.button("🗓️ Build my study plan", type="primary"):
        if not subjects.strip():
            st.warning("Enter at least one subject.")
        else:
            days = max(1, (exam_date - date.today()).days)
            prompt = f"Create a realistic day-by-day study plan. Subjects: {subjects}. Target date: {exam_date}. Days available: {days}. Study hours/day: {hours}. Preferred start: {start_time}. Weak topics: {weak or 'not specified'}. Include revision, breaks, practice questions, and buffer time. Do not overfill the schedule."
            with st.spinner("Creating your plan..."):
                plan_text = ask_ai(prompt, language, style)
            st.markdown(plan_text)
            st.download_button("⬇️ Download study plan", plan_text, "study_plan.md", "text/markdown")

elif mode == "Quiz Generator":
    st.write("Generate a practice quiz and check your answers.")
    topic = st.text_input("Quiz topic", placeholder="e.g. Python basics, mathematical logic")
    level = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
    count = st.slider("Number of questions", 3, 10, 5)
    if st.button("🧠 Generate quiz", type="primary"):
        if not topic.strip():
            st.warning("Enter a topic.")
        else:
            prompt = f"""Create exactly {count} multiple-choice questions about {topic}, difficulty {level}.
Return ONLY valid JSON array. Each item must have keys: question (string), options (array of exactly 4 strings), answer (integer 0-3), explanation (string). Ensure one correct answer per question."""
            with st.spinner("Generating questions..."):
                raw = ask_ai(prompt, "English", "Balanced")
            try:
                quiz = clean_json(raw)
                if not isinstance(quiz, list) or not quiz:
                    raise ValueError("The response was not a question list.")
                st.session_state.quiz_data = quiz
                st.session_state.quiz_topic = topic
            except Exception:
                st.error("Could not format the quiz this time. Please click Generate quiz again.")
                with st.expander("AI response for troubleshooting"):
                    st.code(raw)
    quiz = st.session_state.get("quiz_data", [])
    if quiz:
        st.subheader(f"Quiz: {st.session_state.get('quiz_topic', topic)}")
        picks = []
        with st.form("quiz_answers"):
            for i, q in enumerate(quiz):
                st.markdown(f"**Q{i+1}. {q.get('question','Question')}**")
                options = q.get("options", [])
                picks.append(st.radio("Choose one", options, key=f"quiz_{i}", index=None, label_visibility="collapsed"))
            submitted = st.form_submit_button("Check answers")
        if submitted:
            correct = 0
            for i, (q, pick) in enumerate(zip(quiz, picks)):
                options = q.get("options", [])
                idx = options.index(pick) if pick in options else -1
                is_correct = idx == q.get("answer")
                correct += int(is_correct)
                st.write(f"{'✅' if is_correct else '❌'} **Q{i+1}:** {'Correct' if is_correct else 'Review this answer'}")
                st.caption(q.get("explanation", ""))
            st.metric("Score", f"{correct}/{len(quiz)}", f"{round(correct/len(quiz)*100)}%")
            result_rows = []
            for i, (q, pick) in enumerate(zip(quiz, picks)):
                options = q.get("options", [])
                idx = options.index(pick) if pick in options else -1
                result_rows.append({
                    "Question": q.get("question", ""),
                    "Your answer": pick or "Not answered",
                    "Correct answer": options[q.get("answer", 0)] if options and 0 <= q.get("answer", 0) < len(options) else "",
                    "Correct": idx == q.get("answer"),
                    "Explanation": q.get("explanation", "")
                })
            st.download_button("⬇️ Download quiz results", pd.DataFrame(result_rows).to_csv(index=False).encode("utf-8"),
                               "quiz_results.csv", "text/csv")

elif mode == "Daily Life Organizer":
    st.write("Organize today's tasks and track expenses. Download your records so you can keep them between sessions.")
    tab_tasks, tab_expenses = st.tabs(["✅ Tasks", "💸 Expenses"])

    if "daily_tasks" not in st.session_state:
        st.session_state.daily_tasks = []
    if "daily_expenses" not in st.session_state:
        st.session_state.daily_expenses = []

    with st.expander("💾 Backup and restore my records"):
        st.caption("Download a backup before closing the app. Records currently live in the active session and may be cleared when the app restarts.")
        backup_payload = json.dumps({
            "tasks": st.session_state.daily_tasks,
            "expenses": st.session_state.daily_expenses
        }, indent=2)
        st.download_button("Download records backup (JSON)", backup_payload,
                           "everyday_ai_backup.json", "application/json")
        restore_file = st.file_uploader("Restore a previous JSON backup", type=["json"], key="restore_daily_backup")
        if restore_file is not None and st.button("Restore backup", key="restore_daily_button"):
            try:
                restored = json.load(restore_file)
                tasks_in = restored.get("tasks", [])
                expenses_in = restored.get("expenses", [])
                if not isinstance(tasks_in, list) or not isinstance(expenses_in, list):
                    raise ValueError("Backup tasks and expenses must be lists.")
                if any(not isinstance(x, dict) for x in tasks_in + expenses_in):
                    raise ValueError("Backup records have an invalid format.")
                st.session_state.daily_tasks = tasks_in
                st.session_state.daily_expenses = expenses_in
                st.success("Backup restored.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not restore backup: {type(exc).__name__}: {exc}")

    with tab_tasks:
        st.subheader("Task list")
        with st.form("add_daily_task", clear_on_submit=True):
            task_title = st.text_input("Task", placeholder="e.g. Revise Mathematical Logic")
            task_due = st.date_input("Due date", value=date.today(), key="task_due")
            task_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            task_category = st.selectbox("Category", ["Study", "Work", "Personal", "Health", "Other"])
            add_task = st.form_submit_button("Add task")
        if add_task:
            if task_title.strip():
                st.session_state.daily_tasks.append({
                    "Task": task_title.strip(), "Due date": str(task_due),
                    "Priority": task_priority, "Category": task_category, "Done": False
                })
                st.success("Task added.")
            else:
                st.warning("Enter a task name.")
        if st.session_state.daily_tasks:
            task_df = pd.DataFrame(st.session_state.daily_tasks)
            done_count = sum(bool(t["Done"]) for t in st.session_state.daily_tasks)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total tasks", len(st.session_state.daily_tasks))
            m2.metric("Completed", done_count)
            m3.metric("Remaining", len(st.session_state.daily_tasks) - done_count)
            st.caption("Tick completed tasks below. Tasks are kept for this active app session; download the CSV to save a copy.")
            for i, task in enumerate(st.session_state.daily_tasks):
                cols = st.columns([0.6, 4, 1.4, 1.2])
                st.session_state.daily_tasks[i]["Done"] = cols[0].checkbox(
                    "Done", value=bool(task["Done"]), key=f"task_done_{i}", label_visibility="collapsed")
                cols[1].write(f"**{task['Task']}**")
                cols[2].caption(f"{task['Priority']} priority")
                cols[3].caption(task["Due date"])
            export_tasks = pd.DataFrame(st.session_state.daily_tasks)
            st.download_button("⬇️ Export tasks as CSV", export_tasks.to_csv(index=False).encode("utf-8"),
                               "my_tasks.csv", "text/csv")
            if st.button("Clear all tasks", key="clear_tasks"):
                st.session_state.daily_tasks = []
                st.rerun()
        else:
            st.info("Your task list is empty. Add your first task above.")

    with tab_expenses:
        st.subheader("Simple expense tracker")
        with st.form("add_expense", clear_on_submit=True):
            expense_name = st.text_input("Expense description", placeholder="e.g. Bus fare")
            expense_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
            expense_category = st.selectbox("Expense category", ["Food", "Travel", "Education", "Shopping", "Bills", "Health", "Other"])
            expense_date = st.date_input("Expense date", value=date.today(), key="expense_date")
            add_expense = st.form_submit_button("Add expense")
        if add_expense:
            if expense_name.strip() and expense_amount > 0:
                st.session_state.daily_expenses.append({
                    "Date": str(expense_date), "Description": expense_name.strip(),
                    "Category": expense_category, "Amount (INR)": round(expense_amount, 2)
                })
                st.success("Expense added.")
            else:
                st.warning("Enter a description and an amount greater than zero.")
        if st.session_state.daily_expenses:
            exp_df = pd.DataFrame(st.session_state.daily_expenses)
            total = float(exp_df["Amount (INR)"].sum())
            st.metric("Tracked expenses", f"₹{total:,.2f}")
            st.dataframe(exp_df, use_container_width=True, hide_index=True)
            by_category = exp_df.groupby("Category")["Amount (INR)"].sum().sort_values(ascending=False)
            st.bar_chart(by_category)
            st.download_button("⬇️ Export expenses as CSV", exp_df.to_csv(index=False).encode("utf-8"),
                               "my_expenses.csv", "text/csv")
            if st.button("Clear all expenses", key="clear_expenses"):
                st.session_state.daily_expenses = []
                st.rerun()
        else:
            st.info("No expenses recorded yet. Add one above to start tracking.")

elif mode == "CSV/Excel Analysis":
    st.write("Upload a CSV or Excel file to inspect columns, missing values, summary statistics, and charts.")
    file = st.file_uploader("Upload data", type=["csv", "xlsx", "xls"])
    if file:
        try:
            if file.name.lower().endswith(".csv"):
                df = pd.read_csv(file)
            else:
                book = pd.ExcelFile(file)
                sheet = st.selectbox("Excel sheet", book.sheet_names)
                df = pd.read_excel(book, sheet_name=sheet)
            st.subheader("Data preview")
            st.dataframe(df.head(100), use_container_width=True)
            a, b, c = st.columns(3)
            a.metric("Rows", f"{df.shape[0]:,}")
            b.metric("Columns", f"{df.shape[1]:,}")
            c.metric("Missing cells", f"{int(df.isna().sum().sum()):,}")
            with st.expander("Column types and missing values", expanded=True):
                st.dataframe(pd.DataFrame({"Data type": df.dtypes.astype(str),
                                           "Missing": df.isna().sum(),
                                           "Missing %": (df.isna().mean()*100).round(2)}),
                             use_container_width=True)
            numeric = df.select_dtypes(include="number")
            if not numeric.empty:
                st.subheader("Numeric summary")
                st.dataframe(numeric.describe().T, use_container_width=True)
                col = st.selectbox("Column to chart", numeric.columns.tolist())
                st.bar_chart(df[col].dropna().value_counts().sort_index().head(50))
                if len(numeric.columns) >= 2:
                    st.subheader("Correlation matrix")
                    st.dataframe(numeric.corr(numeric_only=True).round(3), use_container_width=True)
            else:
                st.info("No numeric columns were found for numeric summaries or charts.")
            st.download_button("⬇️ Download cleaned CSV", df.to_csv(index=False).encode("utf-8"),
                               file_name="analysis_export.csv", mime="text/csv")
            with st.expander("Ask AI about this dataset"):
                data_question = st.text_input("Question about the data", placeholder="What patterns should I investigate?")
                if st.button("Analyze with AI"):
                    sample = df.head(30).to_csv(index=False)
                    prompt = f"Analyze this dataset sample carefully. Do not claim to have inspected rows not included. Explain likely patterns, limitations, and useful next analyses.\nQuestion: {data_question}\nShape: {df.shape}\nColumns: {list(df.columns)}\nSample:\n{sample}"
                    with st.spinner("Analyzing sample..."):
                        st.markdown(ask_ai(prompt, language, style))
        except Exception as exc:
            st.error(f"Could not analyze this file: {type(exc).__name__}: {exc}")
else:
    st.info("Choose a tool from the sidebar.")
