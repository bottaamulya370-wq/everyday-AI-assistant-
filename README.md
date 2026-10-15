# Everyday AI Assistant

A Streamlit-based AI workspace with Gemini-powered chat, live web research, PDF study tools, coding help, study planning, quiz generation, personal task/expense tracking, and CSV/Excel analysis.

## Features

- **AI Chat** — conversational answers, language and response-style controls, transcript export.
- **Live Web Search / Latest News** — Tavily results, AI summaries, source URLs, and available publication dates.
- **PDF Study Assistant** — extract selectable PDF text, summarize, create exam notes, generate questions, or ask questions about the document. Scanned PDFs need OCR and are not supported directly.
- **Coding Assistant** — explanations, debugging guidance, code generation, and review.
- **Study Planner** — build and download a study plan.
- **Quiz Generator** — multiple-choice quizzes, explanations, scoring, and CSV export.
- **Daily Life Organizer** — tasks, completion tracking, expenses, category chart, JSON backup/restore, and CSV exports.
- **CSV/Excel Analysis** — data preview, missing values, summary statistics, charts, correlation matrix, and sample-based AI analysis.
- **Optional Supabase persistence** — authenticated user accounts and per-user database records for tasks and expenses. Without Supabase configuration, those two tools run in temporary session-only mode.

## Run locally

1. Install Python 3.10 or newer.
2. Clone the repository and open its folder.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Create a local `.env` file in the project root (do not commit it):

   ```dotenv
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-2.5-flash
   TAVILY_API_KEY=your_tavily_api_key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_supabase_publishable_or_anon_key
   ```

   Gemini is needed for AI features, Tavily for live web search/news, and Supabase is optional. Never use a Supabase service-role key in this public Streamlit app.

6. Start the app:

   ```bash
   streamlit run app.py
   ```

## Enable persistent tasks and expenses with Supabase

Supabase setup is optional. If it is not configured, the rest of the assistant still works and tasks/expenses remain session-only.

1. Create a project at [Supabase](https://supabase.com/).
2. Open **SQL Editor** in the Supabase dashboard.
3. Open `supabase_schema.sql` from this repository, copy its SQL, and run it in the SQL Editor. It creates the `tasks` and `expenses` tables, enables row-level security (RLS), and limits records to the authenticated owner.
4. In Supabase **Project Settings → API** (or the API Keys section), copy the project URL and the publishable/anon key.
5. Add these values to your local `.env` or Streamlit Cloud **App → Settings → Secrets**:

   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   GEMINI_MODEL = "gemini-2.5-flash"
   TAVILY_API_KEY = "your_tavily_api_key"
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_ANON_KEY = "your_supabase_publishable_or_anon_key"
   ```

6. In Supabase **Authentication → URL Configuration**, set the site URL to your Streamlit app URL if you enable email confirmation. Configure email confirmation as desired for your project.
7. Restart/reboot the Streamlit app. Open **Daily Life Organizer**, create an account or sign in, then add a task or expense. Sign in again to access the records associated with that account.

The app uses Supabase Auth and user-scoped queries. Keep RLS enabled. Never disable RLS or place a service-role/secret key in Streamlit Secrets for this app. If you rotate credentials, update the Secrets and reboot the app.

## Deploy on Streamlit Community Cloud

1. Push/confirm the code is on the repository's `main` branch.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/) and select the existing app.
3. Set the app entry point to `app.py`.
4. Open **App settings → Secrets** and add the TOML secrets shown above, using only the services you have configured.
5. Save the settings and reboot the app. Streamlit should install the packages from `requirements.txt`.
6. Check the app logs if the app does not start. A GitHub commit does not guarantee that deployment succeeded; verify the live app and logs after each major update.

## Security and limitations

- API keys belong in local `.env` or Streamlit Cloud Secrets, never in source code or screenshots.
- The Supabase app uses the publishable/anon key plus row-level security; do not use the service-role key.
- Chat history and uploaded PDF text are kept in Streamlit session state, not stored in the database.
- PDF extraction works for selectable text; scanned documents need OCR.
- The AI may make mistakes. Verify important academic, coding, financial, and current-event information against reliable sources.
- CSV/Excel AI analysis sends a limited sample of the uploaded data to the selected AI provider. Do not upload sensitive or confidential data unless you are permitted to share it.
- No automated end-to-end or live deployment test is claimed by this repository update. Test the features and review logs in your own deployed environment.

## Main files

- `app.py` — Streamlit interface and tool workflows.
- `gemini_service.py` — Gemini client and answer generation.
- `web_search.py` — Tavily search/news integration.
- `database.py` — optional Supabase authentication and database helpers.
- `supabase_schema.sql` — database tables and row-level security policies.
- `config.py` — secrets and environment configuration.
- `requirements.txt` — Python dependencies.
