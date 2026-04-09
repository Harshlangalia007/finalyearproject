"""LLM logic for email intent detection and response generation."""

from __future__ import annotations

import json
from typing import Any

from .groq_client import get_groq_client

import re


GROQ_MODEL = "llama-3.1-8b-instant"
SUPPORTED_INTENTS = {"summarize", "question_answering", "draft_reply"}


def _build_email_context(latest_email: dict[str, Any]) -> str:
    """
    Convert the latest email metadata into a plain-text prompt context.

    The engine only receives a lightweight email payload, so this helper
    formats the subject, sender, and snippet into a consistent block that can
    be reused by intent detection and all downstream response functions.
    """
    subject = str(latest_email.get("subject", "")).strip()
    sender = str(latest_email.get("sender", "")).strip()
    snippet = str(latest_email.get("snippet", "")).strip()

    return (
        f"Subject: {subject or 'N/A'}\n"
        f"Sender: {sender or 'N/A'}\n"
        f"Snippet: {snippet or 'N/A'}"
    )


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """
    Send a chat completion request to Groq and return the raw text response.

    This helper centralizes the model name and request structure so the intent
    classifier and the routed handlers all use the same LLM interface.
    """
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        output = response.choices[0].message.content.strip()
        print("LLM Response:", output)
        
        return output if output else ""
        
    except Exception as e:
        return ""
        
    return response.choices[0].message.content.strip()


def _detect_intent(user_input: str, latest_email: dict[str, Any]) -> str:
    """
    Classify the user's request into one of the supported email intents.

    The classifier uses both the user query and the latest email context, then
    returns one normalized label that the router can safely dispatch on.
    """
    email_context = _build_email_context(latest_email)
    raw_response = _call_groq(
        system_prompt=(
            "You are an intent classifier.\n"
            "Return ONLY valid JSON.\n"
            "No explanation, no extra text.\n"
            "Format:\n"
            '{"intent": "summarize"}\n'
            "Allowed values:\n"
            "- summarize\n"
            "- question_answering\n"
            "- draft_reply\n"
        ),
        user_prompt=(
            "Determine the user's intent based on the request and email.\n\n"
            f"User request:\n{user_input}\n\n"
            f"Latest email:\n{email_context}"
        ),
    )

    try:
        match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if match:
            raw_response = match.group()
        
        parsed_response = json.loads(raw_response)
        intent = str(parsed_response.get("intent", "")).strip()
        
    except (TypeError, ValueError, json.JSONDecodeError):
        print("Intent parsing failed:", raw_response)
        intent = ""

    if intent not in SUPPORTED_INTENTS:
        print("Invalid intent:", intent)
        return "question_answering"

    return intent


def summarize_email(email_text: str) -> str:
    """
    Generate a concise summary of the latest email content.

    This function is called when the detected intent is `summarize` and asks
    the model to focus on the key message, request, and any obvious next steps.
    """
    return _call_groq(
        system_prompt=(
            "You summarize emails clearly and concisely. "
            "Focus on the main message, important details, and any requested action."
        ),
        user_prompt=f"Summarize this email:\n\n{email_text}",
    )


def answer_question(email_text: str, user_input: str) -> str:
    """
    Answer the user's question using only the provided email context.

    This function is used for the `question_answering` intent and keeps the
    response grounded in the latest email instead of inventing missing details.
    """
    return _call_groq(
        system_prompt=(
            "You answer questions about an email using only the provided context. "
            "If the answer is not supported by the email, say so clearly."
        ),
        user_prompt=(
            f"Email context:\n{email_text}\n\n"
            f"User question:\n{user_input}\n\n"
            "Answer the question based only on the email context."
        ),
    )


def draft_reply(email_text: str, user_input: str) -> str:
    """
    Draft a reply email based on the user's instruction and email context.

    This function is used for the `draft_reply` intent and produces a reply
    draft only. It does not send the email or trigger any external action.
    """
    return _call_groq(
        system_prompt=(
            "You draft professional email replies. "
            "Write a clear and relevant reply based on the provided email and user instruction."
        ),
        user_prompt=(
            f"Original email:\n{email_text}\n\n"
            f"User instruction:\n{user_input}\n\n"
            "Draft an appropriate reply email."
        ),
    )


def process_user_query(user_input: str, latest_email: dict[str, Any]) -> dict[str, Any]:
    """
    Detect the user's intent and route the request to the correct email helper.

    The router combines the latest email metadata into prompt context, uses
    Groq to detect one of the supported intents, then calls the matching
    internal function and returns a structured response payload.
    """
    if not latest_email:
            return {
                "intent": "error",
                "response": "No email context available.",
                "requires_action": False,
            }
            
    email_text = _build_email_context(latest_email)
    intent = _detect_intent(user_input, latest_email)

    try:
        if intent == "summarize":
            response_text = summarize_email(email_text)
        elif intent == "draft_reply":
            response_text = draft_reply(email_text, user_input)
        else:
            response_text = answer_question(email_text, user_input)
            intent = "question_answering"
            
    except Exception as e:
        print("Error in routing:", str(e))
        response_text = "Sorry, something went wrong while processing your request."
        
    if not response_text:
        response_text = "I couldn't generate a response. Please try again."

    return {
        "intent": intent,
        "response": response_text,
        "requires_action": intent == "draft_reply",
    }


def analyze_email_content(email_text: str, action: str) -> dict[str, Any]:
    """
    Provide a backward-compatible wrapper for older callers in this project.

    Existing code can still call this helper with a raw email string and action
    text, while the new implementation routes through `process_user_query`.
    """
    latest_email = {
        "subject": "",
        "sender": "",
        "snippet": email_text,
    }
    return process_user_query(action, latest_email)
