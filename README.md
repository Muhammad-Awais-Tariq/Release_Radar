# 🎬 Release Radar

An AI-powered movie discovery app that tells you what's releasing soon — and *why* it's worth watching. Pick a genre and describe your mood, and an **AI agent** searches a live movie database on its own terms, decides which 3 releases actually fit, and explains why. Built with a **Streamlit** frontend and an **n8n** workflow as the backend, so the API keys and decision-making logic never touch the client side.

## Features

- Browse upcoming movie releases filtered by genre (Action, Horror, Sci-Fi, Comedy, and 14 more)
- Describe your mood in plain language (e.g. *"something dark and slow-paced"*) and get picks tailored to it
- An **AI Agent** (Google Gemini) owns the search itself — it decides when and how to query TMDB (which sort order, which date range, whether to search again with different parameters), rather than being handed a fixed, pre-fetched list
- The agent then reasons over whatever it finds and picks the best 3, writing a short AI-written explanation of why each fits your mood
- Backend logic fully separated from the frontend via an n8n webhook
- Importable n8n workflow — the whole backend can be recreated in one click

## How the Program Works

The app is split into two independent pieces that talk to each other over HTTP:

```
Streamlit (frontend)
      │
      │  POST { "genre": "horror", "mood": "something dark and slow-paced" }
      ▼
n8n Webhook (backend)
      │
      ▼
Genre name → TMDB genre ID
      │
      ▼
AI Agent (Gemini) takes over:
  - decides how to query TMDB (sort order, date range)
  - calls the TMDB search tool
  - if results are thin or don't fit the mood, searches again
    with different parameters (up to 3 tries)
  - picks the best 3 movies and writes a reason for each
      │
      ▼
Parse AI response into clean movie objects
      │
      ▼
Respond back to Streamlit
      │
      ▼
Streamlit renders 3 movie cards with AI reasoning
```

- You pick a genre and (optionally) describe a mood in Streamlit, then click the button
- Streamlit sends both as a POST request to the n8n webhook URL
- n8n hands the genre and mood to an **AI Agent**, which has direct, autonomous access to a TMDB search tool — it isn't pre-fed a fixed list of candidates
- The agent decides for itself what to search for, whether one search is enough, and which 3 movies genuinely fit — rather than the workflow applying a fixed rule like "take the top 3 by date"
- The finished data (movies + AI reasoning) comes back as a JSON array, which Streamlit loops through and displays

## The n8n Workflow — Node by Node

The backend workflow lives in [`n8n_workflow/release_radar_n8n.json`](./n8n_workflow/release_radar_n8n.json) and can be imported directly into any n8n instance. Here's what each node does:

![n8n workflow](https://github.com/Muhammad-Awais-Tariq/Release_Radar/blob/main/n8n_workflow/workflow.png)

| Node | Type | What it does |
|---|---|---|
| **Webhook** | Trigger | Listens for incoming `POST` requests at `/discover`. This is the entry point Streamlit calls into, carrying the user's `genre` and `mood`. |
| **Edit Fields** | Set | Converts the genre name sent by Streamlit (e.g. `"horror"`) into the numeric genre ID TMDB expects (e.g. `27`), using a lookup map covering all 18 genres. |
| **AI Agent** | Agent (Google Gemini) | The core decision-maker. Given the genre ID, the user's mood (falling back to `"no specific preference"` if left blank), and today's date, it decides on its own whether and how to search TMDB — it can call the search tool up to 3 times with different parameters (wider date range, different sort order) if the first results are too few or don't fit the mood. Once satisfied, it picks exactly 3 movies and writes a short, specific reason for each, grounded only in real candidates it actually retrieved. |
| **Google Gemini Chat Model** | Sub-node (LLM) | Plugs into the AI Agent as its reasoning engine (`gemini-3-flash-preview`). This is what the Agent "thinks" with — it has no direct connection in the main data flow, only into the Agent's Chat Model input. |
| **TMDB Search Tool** | Sub-node (Tool) | Also plugs into the AI Agent, not the main flow — this is what the Agent calls. It wraps TMDB's `/discover/movie` endpoint, with `with_genres`, `sort_by`, and `primary_release_date.gte` left for the Agent itself to fill in at call time based on its own reasoning. Authentication is handled via an n8n **Query Auth credential**, so the API key never appears in the workflow file itself. |
| **Code in JavaScript** | Data Transform | Parses the AI Agent's raw text output (stripping any markdown formatting) into clean JSON, and reshapes each movie into a simple object with `title`, `release_date`, `overview`, `reason`, and a fully-formed poster `image` URL. |
| **Respond to Webhook** | Response | Sends the final array of 3 AI-picked movies back to whichever client called the webhook — configured to return **all incoming items**, not just the first one. |

**Data flow summary:** `Webhook → Edit Fields → AI Agent (Gemini + TMDB Search Tool) → Code in JavaScript → Respond to Webhook`

> The TMDB fetch used to be a fixed, always-executed HTTP Request step that ran once before the AI ever saw the data. It's now a **tool** the Agent calls on its own — the Agent decides whether one search is enough or whether to retry with different parameters, which is what makes this an agentic workflow rather than a fixed automation pipeline.

## APIs Used

- **[TMDB (The Movie Database)](https://www.themoviedb.org/documentation/api)** — provides all movie data: titles, release dates, overviews, and posters. Free to use with a developer API key.
- **[Google Gemini](https://ai.google.dev/)** — powers the AI Agent's reasoning and tool-calling. Free tier via Google AI Studio, no card required.

## File Structure

```bash
Release_Radar/
│
├── n8n_workflow/
│   ├── release_radar_n8n.json     # Exportable/importable n8n workflow
│   └── workflow.png                # Visual screenshot of the workflow canvas
│
├── app.py                          # Streamlit frontend
├── .env                            # Local environment variables (not committed)
├── .env.example                    # Template showing required variables
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

## How to Run Locally

### Prerequisites

- Python 3.10+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (to run n8n)
- A free [TMDB API key](https://www.themoviedb.org/settings/api)
- A free [Google Gemini API key](https://aistudio.google.com/apikey)

### Step 1 — Set up n8n

1. Run n8n locally via Docker (see [n8n's official Docker guide](https://docs.n8n.io/hosting/installation/docker/))
2. Open `http://localhost:5678` in your browser
3. Create a new workflow and click **Import from File** (or drag in the file)
4. Import [`n8n_workflow/release_radar_n8n.json`](./n8n_workflow/release_radar_n8n.json)

### Step 2 — Add your TMDB API key as a credential

1. In n8n, go to **Credentials → Add Credential**
2. Choose **Query Auth**
3. Name: `api_key`
4. Value: your TMDB API key
5. Save
6. Open the **TMDB Search Tool** node in the imported workflow and link it to this new credential (Authentication → Generic Credential Type → Query Auth → select your credential)

### Step 3 — Add your Gemini API key as a credential

1. In n8n, go to **Credentials → Add Credential**
2. Search for **Google Gemini(PaLM) Api**
3. Paste your Gemini API key (from [aistudio.google.com/apikey](https://aistudio.google.com/apikey))
4. Save
5. Open the **Google Gemini Chat Model** node and link it to this new credential

### Step 4 — Activate the workflow

1. Toggle **Active** at the top of the workflow canvas
2. Open the **Webhook** node → copy the **Production URL** (e.g. `http://localhost:5678/webhook/discover`)

### Step 5 — Set up the Streamlit app

1. Clone the repository and navigate to the project folder
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\Activate.ps1      # Windows
   source venv/bin/activate       # Mac/Linux
   ```
3. Install dependencies:
   ```bash
   pip install streamlit requests python-dotenv
   ```
4. Copy `.env.example` to `.env` and set your webhook URL:
   ```
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/discover
   ```

### Step 6 — Run the app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`), pick a genre, optionally describe your mood, and click **Find Upcoming Movies**.

## Technologies Used

- Python
- [Streamlit](https://streamlit.io/) — web UI framework
- [n8n](https://n8n.io/) — workflow automation / agent orchestration
- [TMDB API](https://www.themoviedb.org/documentation/api) — movie data source, exposed to the agent as a callable tool
- [Google Gemini](https://ai.google.dev/) — powers the AI Agent's reasoning and tool-calling decisions
- Docker — for running n8n locally
- `requests` / `python-dotenv` — HTTP calls and environment config

## Notes

- If the mood field is left blank, the Agent falls back to picking broadly appealing movies based on the overviews alone.
- The n8n workflow must be **Active** (published), not just saved, for the Production webhook URL to respond to real requests.
- Both the TMDB and Gemini API keys are stored as n8n credentials and are never present in the exported workflow JSON — safe to commit and share publicly.
- The Agent can call the TMDB tool up to 3 times per request if it decides its first search wasn't good enough — this is visible in n8n's execution log under the AI Agent node.
- Currently limited to movies; a games-discovery branch (via a game database API) is a planned extension.

## Author

Muhammad Awais Tariq

---

If you like this project, consider giving it a star ⭐