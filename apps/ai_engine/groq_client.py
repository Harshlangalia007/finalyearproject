# Centralized client for Groq API
import os
from groq import Groq

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key)
