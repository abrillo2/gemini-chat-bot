import functions_framework
import json
from flask import request, jsonify
from google.cloud import aiplatform
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 🔹 Hardcode your values here
PROJECT_ID = "compact-arc-471013-q6"                 # <-- replace with your GCP project
LOCATION = "us-central1"                       # <-- or another region where Vertex AI is enabled
IMPERSONATE_USER = "admin@dev2.orghub.ca"      # <-- replace with a Workspace user email
SERVICE_ACCOUNT_FILE = "key.json"              # <-- path to your service account JSON inside container

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)
gemini_model = aiplatform.GenerativeModel("gemini-1.5-flash")


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


def get_user_credentials():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
        subject=IMPERSONATE_USER,  # impersonating this user
    )
    return creds.with_quota_project(PROJECT_ID)


def call_gemini(question: str, context: str) -> str:
    prompt = f"""
    You are a helpful FAQ assistant. 
    Question: {question}
    Context: {context}
    Answer:
    """
    resp = gemini_model.generate_content(prompt)
    return resp.text.strip() if getattr(resp, "text", None) else "No answer found."


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
