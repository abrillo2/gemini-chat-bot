import functions_framework
from flask import request, jsonify
from google.auth import default
from googleapiclient.discovery import build
import google.generativeai as genai

# 🔹 Workspace user to impersonate
IMPERSONATE_USER = "admin@dev2.orghub.ca"  # replace with your Workspace user

# 🔹 Cloud project / region
PROJECT_ID = "compact-arc-471013-q6"
LOCATION = "us-central1"

# 🔹 Configure Google Gen AI SDK (no API key needed on Cloud Run/Functions)
genai.configure(client_type="gcp_project", project=PROJECT_ID, location=LOCATION)


def get_user_credentials():
    """Get credentials for a Workspace user using domain-wide delegation."""
    creds, _ = default(scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ])
    return creds.with_subject(IMPERSONATE_USER)


def fetch_gmail_messages(creds):
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=3).execute()
    msgs = results.get("messages", [])
    snippets = []
    for m in msgs:
        msg = service.users().messages().get(userId="me", id=m["id"]).execute()
        snippets.append(msg.get("snippet", ""))
    return "\n".join(snippets)


def fetch_drive_files(creds):
    service = build("drive", "v3", credentials=creds)
    results = service.files().list(pageSize=3, fields="files(name)").execute()
    files = results.get("files", [])
    return "\n".join(f["name"] for f in files)


def call_gemini(question: str, context: str) -> str:
    prompt = f"""
You are a helpful FAQ assistant.
Question: {question}
Context: {context}
Answer:
"""
    response = genai.chat(model="gemini-1.5", messages=[{"author": "user", "content": prompt}])
    return response.last.content if getattr(response, "last", None) else "No answer found."


@functions_framework.http
def chat_faq_bot(request):
    event = request.get_json(silent=True)
    if not event:
        return jsonify({"text": "Invalid request"}), 400

    question = event.get("message", {}).get("text", "").strip()
    if not question:
        return jsonify({"text": "No question provided."})

    creds = get_user_credentials()
    gmail_context = fetch_gmail_messages(creds)
    drive_context = fetch_drive_files(creds)
    context = f"Gmail:\n{gmail_context}\n\nDrive:\n{drive_context}"

    answer = call_gemini(question, context)

    return jsonify({"text": answer})
