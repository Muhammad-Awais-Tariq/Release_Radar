import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

st.title("Release Radar")

genres = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
          "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
          "Romance", "Sci-Fi", "Thriller", "War", "Western"]

genre = st.selectbox("Pick a genre" , genres)

if st.button("Find upcomming movies"):
    try:
        response =  requests.post(
            N8N_WEBHOOK_URL,
            json={"genre" : genre.lower().replace("-" , "").replace(" " , "")},
            timeout=10
        )

        response.raise_for_status()

        movies = response.json()

        
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't reach n8n: {e}")
