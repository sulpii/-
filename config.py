import os
import streamlit as st
from openai import OpenAI

def get_openai_client(api_key: str = None):
    key = api_key or st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)
