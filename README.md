# Everyday AI Assistant

A Streamlit-based AI workspace with Gemini-powered chat, live web research, PDF study tools, coding help, study planning, quiz generation, personal task/expense tracking, and CSV/Excel analysis.

## Features

- **AI Chat** — conversational answers, in-session conversation history, new-chat/reset control, regenerate, transcript export, and loading/error feedback.
- **Text Summarizer** — summarize pasted text as short/detailed summaries, key takeaways, revision notes, or simple explanations.
- **Study Assistant** — beginner explanations, exam notes, worked examples, practice questions, and quick revision.
- **Email Drafting** — professional, polite, friendly, concise, follow-up, and thank-you email drafts.
- **User Feedback** — anonymous 1–5 ratings for answer quality, speed, usability, and overall experience; feedback can be stored in Supabase for 10–20-person user testing.
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

## Anonymous user testing (10–20 people)

1. Run the updated `supabase_schema.sql` in Supabase SQL Editor so the `product_feedback` table and insert-only policy exist.
2. Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to Streamlit App Settings → Secrets. Use only the publishable/anon key, never the service-role key.
3. Reboot the Streamlit app and ask 10–20 testers to try at least one feature each, then open **User Feedback** and submit the anonymous survey.
4. Review the `product_feedback` rows in Supabase Table Editor. Compare average overall rating, answer quality, speed, and ease of use; group comments by recurring issue. Do not collect names/emails or paste confidential information into feedback.
5. If feedback storage is not configured, the app offers a CSV download as a manual fallback; that fallback does not automatically send responses to the project owner.

## Security and limitations

- API keys belong in local `.env` or Streamlit Cloud Secrets, never in source code or screenshots.
- The Supabase app uses the publishable/anon key plus row-level security; do not use the service-role key.
- Chat history and uploaded PDF text are kept in Streamlit session state, not stored in the database. Feedback submissions are stored in `product_feedback` only when Supabase is configured and the updated schema has been run.
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

## Separate HTML/CSS/JavaScript frontend + FastAPI backend

The original Streamlit app remains available as `app.py`. A separate browser frontend and FastAPI API have also been added:

- `frontend/index.html`, `frontend/styles.css`, `frontend/app.js` — responsive dark-mode web interface.
- `api/main.py` — FastAPI endpoints for chat, coding/study/quiz prompts, web search/news, and PDF Q&A.
- `render.yaml` — Render backend service template.
- `netlify.toml` — Netlify static-site publish configuration.

### Run both locally

1. Install Python 3.10+ and dependencies: `pip install -r requirements.txt`.
2. Set `GEMINI_API_KEY` in your local `.env`. Add `TAVILY_API_KEY` for search. Do not commit `.env`.
3. From the repository root, start the backend:

   ```bash
   uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. Open a second terminal and serve the frontend directory:

   ```bash
   python -m http.server 5500 --directory frontend
   ```

5. Open `http://127.0.0.1:5500`. The frontend calls `http://127.0.0.1:8000` by default. API documentation is at `http://127.0.0.1:8000/docs`.
6. Use the gear icon in the frontend to set and test a deployed API URL. The URL is held only in the current browser tab.

### Deploy the backend on Render

1. Push this repository to GitHub (the changes are committed on `main`).
2. In [Render](https://render.com/), choose **New → Blueprint** and select this repository. Render reads `render.yaml`.
3. Add the secret values for `GEMINI_API_KEY` and, if needed, `TAVILY_API_KEY`. Set `FRONTEND_ORIGINS` to the exact deployed frontend origin, for example `https://your-site.netlify.app` (no trailing slash). Do not put the frontend URL in API-key fields.
4. Deploy and check `https://YOUR-API.onrender.com/api/health` returns a JSON status response. The first request on a free service may take time while it wakes up.
5. Confirm `https://YOUR-API.onrender.com/docs` loads the API documentation.

### Deploy the frontend on Netlify

1. In [Netlify](https://www.netlify.com/), import this repository and let it use `netlify.toml` (publish directory: `frontend`), or deploy the `frontend` folder as a static site.
2. Copy the final HTTPS site origin from Netlify.
3. In Render, set `FRONTEND_ORIGINS` to that exact origin and redeploy/restart the backend.
4. Open the Netlify site, click the gear icon, enter the Render API base URL (for example `https://your-api.onrender.com`), then choose **Test connection** and **Connect**.
5. Test chat, search, and PDF Q&A separately. Check browser developer tools and Render logs for failures.

### API endpoints

- `GET /api/health` — health check.
- `POST /api/chat` — AI chat, coding, study planning, or quiz-style response.
- `POST /api/search` — live web search/news and AI summary.
- `POST /api/pdf` — text-based PDF question answering (multipart upload).

### Architecture notes

- Streamlit and the separate HTML/JS frontend are two frontends that share the Python AI/search services; the Streamlit app has not been removed.
- The static frontend currently uses browser-memory chat history. Supabase-backed task/expense persistence remains in the existing Streamlit organizer and is not yet wired into the standalone frontend.
- This API does not yet expose Supabase account/task/expense endpoints; do not assume that the standalone frontend persists personal data.
- Never put provider API keys in HTML/JavaScript. They must remain on the backend environment.
- CORS is restricted by `FRONTEND_ORIGINS`; set it to the actual frontend origin before production use.
- Automated tests and a live deployment have not been run as part of this change. Verify the health endpoint and the main workflows after deployment.
