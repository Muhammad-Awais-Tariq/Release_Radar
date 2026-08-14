import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

