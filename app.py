import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

st.set_page_config(page_title="Release Radar", page_icon="🎬", layout="wide")

st.title("🎬 Release Radar")
st.caption("Discover upcoming movies by genre picked and explained by AI based on your mood")

genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
          "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
          "Romance", "Sci-Fi", "Thriller", "War", "Western"]

with st.sidebar:
    st.header("Filters")
    genre = st.selectbox("Pick a genre", genres)
    mood = st.text_area(
        "What's your mood?",
        placeholder="e.g. something dark and slow-paced, or a fun popcorn movie",
        help="Optional leave blank and the AI will pick broadly appealing movies.",
        height=100
    )
    search = st.button("Find upcoming movies", width="stretch")

if search:
    with st.spinner(f"Asking AI to pick the best upcoming {genre} movies for you..."):
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json={
                    "genre": genre.lower().replace("-", "").replace(" ", ""),
                    "mood": mood
                },
                timeout=30
            )
            response.raise_for_status()
            movies = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Couldn't reach n8n: {e}")
            movies = []

    if movies:
        st.header(f"Upcoming {genre} Movies", divider="rainbow")
        if mood.strip():
            st.caption(f"Curated for the mood: *\"{mood}\"*")

        cols = st.columns(len(movies))
        for col, movie in zip(cols, movies):
            with col:
                with st.container(border=True):
                    if movie.get("image"):
                        st.image(movie["image"], width="stretch")
                    else:
                        st.markdown(
                            """
                            <div style="height:300px; display:flex; align-items:center;
                                        justify-content:center; background-color:#262730;
                                        border-radius:8px; color:#888; font-size:14px;">
                                No poster available
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.subheader(movie.get("title", "Untitled"))
                    st.badge(movie.get("release_date", "TBA"), icon="📅")

                    if movie.get("reason"):
                        st.info(f" **Why this pick:** {movie['reason']}")

                    with st.expander("Overview"):
                        st.write(movie.get("overview", "No overview available."))
    else:
        st.info("No results yet — pick a genre and hit search.")
else:
    st.info("👈 Pick a genre (and optionally a mood) from the sidebar, then hit search to get started.")