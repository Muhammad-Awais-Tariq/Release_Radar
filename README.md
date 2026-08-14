# 🎬 Release Radar

A genre-based movie discovery app that tells you what's releasing soon. Pick a genre, and get the top 3 upcoming movies matching it pulled live from TMDB. Built with a **Streamlit** frontend and an **n8n** workflow as the backend, so the API key and data logic never touch the client side.

## Features

- Browse upcoming movie releases filtered by genre (Action, Horror, Sci-Fi, Comedy, and 14 more)
- Results sorted by soonest release date first
- Clean, trimmed data per movie title, release date, overview, and poster no bloated API payloads
- Backend logic fully separated from the frontend via an n8n webhook
- Importable n8n workflow the whole backend can be recreated in one click

## How the Program Works

The app is split into two independent pieces that talk to each other over HTTP:

```
Streamlit (frontend)
      │
      │  POST { "genre": "horror" }
      ▼
n8n Webhook (backend)
      │
      ▼
Genre name → TMDB genre ID
      │
      ▼
TMDB API — discover upcoming movies for that genre
      │
      ▼
Trim response to top 3 movies (title, date, overview, poster)
      │
      ▼
Respond back to Streamlit
      │
      ▼
Streamlit renders 3 movie cards
```

- You pick a genre from a dropdown in Streamlit and click the button
- Streamlit sends that genre as a POST request to the n8n webhook URL
- n8n takes it from there no frontend code ever talks to TMDB directly
- The finished movie data comes back as a JSON array, which Streamlit loops through and displays

## The n8n Workflow — Node by Node

The backend workflow lives in [`n8n_workflow/release_radar_n8n.json`](./n8n_workflow/release_radar_n8n.json) and can be imported directly into any n8n instance. Here's what each node does:

![n8n workflow](https://github.com/Muhammad-Awais-Tariq/Release_Radar/blob/main/n8n_workflow/workflow.png)

| Node | Type | What it does |
|---|---|---|
| **Webhook** | Trigger | Listens for incoming `POST` requests at `/discover`. This is the entry point Streamlit calls into. |
| **Edit Fields** | Set | Converts the genre name sent by Streamlit (e.g. `"horror"`) into the numeric genre ID TMDB expects (e.g. `27`), using a lookup map covering all 18 genres. |
| **HTTP Request** | API Call | Calls TMDB's `/discover/movie` endpoint with the genre ID, sorts by `primary_release_date.asc`, and filters to only movies releasing on or after today. Authentication is handled via an n8n **Query Auth credential**, so the API key never appears in the workflow file itself. |
| **Code in JavaScript** | Data Transform | Takes TMDB's full response (which includes dozens of fields per movie) and trims it down to just the top 3 results with only `title`, `release_date`, `overview`, and a fully-formed poster `image` URL. |
| **Respond to Webhook** | Response | Sends the final array of 3 movies back to whichever client called the webhook configured to return **all incoming items**, not just the first one. |

**Data flow summary:** `Webhook → Edit Fields → HTTP Request → Code in JavaScript → Respond to Webhook`

## API Used

- **[TMDB (The Movie Database)](https://www.themoviedb.org/documentation/api)** — provides all movie data: titles, release dates, overviews, and posters. Free to use with a developer API key.

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
6. Open the **HTTP Request** node in the imported workflow and link it to this new credential (Authentication → Generic Credential Type → Query Auth → select your credential)

### Step 3 — Activate the workflow

1. Toggle **Publish/Active** at the top of the workflow canvas
2. Open the **Webhook** node → copy the **Production URL** (e.g. `http://localhost:5678/webhook/discover`)

### Step 4 — Set up the Streamlit app

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

### Step 5 — Run the app

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`), pick a genre, and click **Find Upcoming Movies**.

## Technologies Used

- Python
- [Streamlit](https://streamlit.io/) — web UI framework
- [n8n](https://n8n.io/) — workflow automation / backend logic
- [TMDB API](https://www.themoviedb.org/documentation/api) — movie data source
- Docker — for running n8n locally
- `requests` / `python-dotenv` — HTTP calls and environment config

## Notes

- Results are always sorted by soonest release date, so the top 3 shown are the *very next* releases in that genre.
- The n8n workflow must be **Active** (published), not just saved, for the Production webhook URL to respond to real requests.
- The TMDB API key is stored as an n8n credential and is never present in the exported workflow JSON safe to commit and share publicly.
- Currently limited to movies; a games-discovery branch (via a game database API) is a planned extension.

## Author

Muhammad Awais Tariq

---

If you like this project, consider giving it a star ⭐