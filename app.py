import functions_framework
from flask import request, jsonify
from google.auth import default
from googleapiclient.discovery import build
from google.cloud import aiplatform

# 🔹 Workspace user to impersonate
IMPERSONATE_USER = "admin@dev2.orghub.ca"

# 🔹 Cloud project / region
PROJECT_ID = "compact-arc-471013-q6"
LOCATION = "us-central1"

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)

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

def call_vertex_ai(question: str, context: str) -> str:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import GenerativeModel
    
    prompt = f"""
You are a helpful FAQ assistant. Use the following context from user's emails and drive files to answer the question.

Context from user's data:
{context}

Question: {question}

Please provide a helpful answer based on the available context.
"""
    
    model = GenerativeModel("gemini-1.5-pro-preview-0514")
    response = model.generate_content(prompt)
    return response.text

@functions_framework.http
def chat_faq_bot(request):
    event = request.get_json(silent=True)
    if not event:
        return jsonify({"text": "Invalid request"}), 400

    question = event.get("message", {}).get("text", "").strip()
    if not question:
        return jsonify({"text": "No question provided."})

    try:
        creds = get_user_credentials()
        gmail_context = fetch_gmail_messages(creds)
        drive_context = fetch_drive_files(creds)
        context = f"Gmail snippets:\n{gmail_context}\n\nDrive files:\n{drive_context}"

        answer = call_vertex_ai(question, context)
        return jsonify({"text": answer})
    
    except Exception as e:
        return jsonify({"text": f"Error: {str(e)}"}), 500
