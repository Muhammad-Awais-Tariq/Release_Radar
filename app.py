import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

st.set_page_config(page_title="Release Radar", page_icon="🎬", layout="wide")

st.title("🎬 Release Radar")
st.caption("Discover upcoming movies by genre")

genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
          "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
          "Romance", "Sci-Fi", "Thriller", "War", "Western"]

with st.sidebar:
    st.header("Filters")
    genre = st.selectbox("Pick a genre", genres)
    search = st.button("🔍 Find upcoming movies", width="stretch")

if search:
    with st.spinner(f"Fetching upcoming {genre} movies..."):
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json={"genre": genre.lower().replace("-", "").replace(" ", "")},
                timeout=10
            )
            response.raise_for_status()
            movies = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Couldn't reach n8n: {e}")
            movies = []

    if movies:
        st.header(f"Upcoming {genre} Movies", divider="rainbow")

        cols = st.columns(len(movies))
        for col, movie in zip(cols, movies):
            with col:
                with st.container(border=True):
                    if movie.get("image"):
                        st.image(movie["image"], width="stretch")
                    st.subheader(movie.get("title", "Untitled"))
                    st.badge(movie.get("release_date", "TBA"), icon="📅")
                    with st.expander("Overview"):
                        st.write(movie.get("overview", "No overview available."))
    else:
        st.info("No results yet — pick a genre and hit search.")
else:
    st.info("👈 Pick a genre from the sidebar and hit search to get started.")