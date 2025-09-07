import functions_framework
from flask import request, jsonify
from google.auth import default, credentials
from googleapiclient.discovery import build
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Workspace user to impersonate
IMPERSONATE_USER = "admin@dev2.orghub.ca"  # replace with your Workspace user

# 🔹 Cloud project / region
PROJECT_ID = "compact-arc-471013-q6"
LOCATION = "us-central1"

# Initialize Vertex AI
try:
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    logger.info("Vertex AI initialized successfully")
except Exception as e:
    logger.error(f"Vertex AI initialization failed: {e}")

def get_user_credentials():
    """Get credentials for a Workspace user using domain-wide delegation."""
    try:
        creds, _ = default(scopes=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/cloud-platform"
        ])
        delegated_creds = creds.with_subject(IMPERSONATE_USER)
        logger.info("Credentials obtained successfully")
        return delegated_creds
    except Exception as e:
        logger.error(f"Failed to get credentials: {e}")
        raise

def fetch_gmail_messages(creds):
    """Fetch recent Gmail messages."""
    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=5).execute()
        msgs = results.get("messages", [])
        snippets = []
        
        for m in msgs[:3]:  # Limit to 3 messages
            msg = service.users().messages().get(userId="me", id=m["id"], format="metadata").execute()
            subject = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'), 'No Subject')
            snippets.append(f"Subject: {subject}")
        
        return "\n".join(snippets) if snippets else "No recent emails found"
    except Exception as e:
        logger.error(f"Gmail API error: {e}")
        return f"Error accessing Gmail: {str(e)}"

def fetch_drive_files(creds):
    """Fetch recent Drive files."""
    try:
        service = build("drive", "v3", credentials=creds)
        results = service.files().list(
            pageSize=5,
            fields="files(name, mimeType, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute()
        files = results.get("files", [])
        
        file_info = []
        for f in files[:3]:  # Limit to 3 files
            file_type = "Folder" if f.get("mimeType") == "application/vnd.google-apps.folder" else "File"
            file_info.append(f"{file_type}: {f.get('name', 'Unnamed')}")
        
        return "\n".join(file_info) if file_info else "No recent files found"
    except Exception as e:
        logger.error(f"Drive API error: {e}")
        return f"Error accessing Drive: {str(e)}"

def call_vertex_ai(question: str, context: str) -> str:
    """Call Vertex AI Gemini model."""
    try:
        prompt = f"""
You are a helpful FAQ assistant for a company. Use the following context from the user's emails and drive files to answer their question.

CONTEXT FROM USER'S DATA:
{context}

USER'S QUESTION: {question}

Please provide a helpful, concise answer based on the available context. If the context doesn't contain relevant information, politely say you don't have enough information from their recent data.

Answer:
"""
        
        model = GenerativeModel("gemini-pro")
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 1024,
                "temperature": 0.2,
                "top_p": 0.8,
            }
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"Vertex AI error: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."

@functions_framework.http
def chat_faq_bot(request):
    """HTTP Cloud Function for FAQ chatbot."""
    try:
        event = request.get_json(silent=True)
        if not event:
            return jsonify({"text": "Invalid request format"}), 400

        # Extract question from Google Chat event
        message = event.get("message", {})
        question = message.get("text", "").strip()
        
        if not question:
            return jsonify({"text": "Please provide a question to answer."})

        logger.info(f"Received question: {question}")

        # Get user context
        creds = get_user_credentials()
        gmail_context = fetch_gmail_messages(creds)
        drive_context = fetch_drive_files(creds)
        
        context = f"Recent Emails:\n{gmail_context}\n\nRecent Drive Files:\n{drive_context}"
        logger.info(f"Context gathered: {context}")

        # Generate answer using Vertex AI
        answer = call_vertex_ai(question, context)
        
        return jsonify({"text": answer})
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"text": "An unexpected error occurred. Please try again."}), 500
