from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.auth import default
import os
import base64

app = Flask(__name__)

@app.route('/', methods=['POST'])
def faq_bot():
    # Authenticate with domain-wide delegation
    credentials, _ = default()
    
    # Initialize all APIs
    gmail = build('gmail', 'v1', credentials=credentials)
    drive = build('drive', 'v3', credentials=credentials)
    chat = build('chat', 'v1', credentials=credentials)
    
    # Get user query from Chat message
    user_message = request.json.get('message', {})
    query = user_message.get('text', '').replace('@FAQ-Bot', '').strip()
    space_name = user_message.get('space', {}).get('name')
    
    # Search across all services
    results = {
        'emails': gmail.users().messages().list(
            userId='me',
            q=query,
            maxResults=3,
            fields='messages(id,snippet)'
        ).execute().get('messages', []),
        
        'files': drive.files().list(
            q=f"fullText contains '{query}'",
            pageSize=3,
            fields='files(name,webViewLink)'
        ).execute().get('files', []),
        
        'chats': chat.spaces().messages().list(
            parent=space_name,
            filter=f"text:\"{query}\"",
            pageSize=3
        ).execute().get('messages', [])
    }
    
    # Format response for Google Chat
    response = {
        'text': f"🔍 Results for '{query}':",
        'cards': [{
            'header': {'title': 'FAQ Results'},
            'sections': []
        }]
    }
    
    # Add email results
    if results['emails']:
        email_snippets = "\n".join(
            f"📧 {msg['snippet'][:50]}..." 
            for msg in results['emails']
        )
        response['cards'][0]['sections'].append({
            'widgets': [{
                'textParagraph': {
                    'text': f"<b>Emails ({len(results['emails'])}):</b>\n{email_snippets}"
                }
            }]
        })
    
    # Add Drive results
    if results['files']:
        file_links = "\n".join(
            f"📁 <a href='{file['webViewLink']}'>{file['name']}</a>"
            for file in results['files']
        )
        response['cards'][0]['sections'].append({
            'widgets': [{
                'textParagraph': {
                    'text': f"<b>Drive Files ({len(results['files'])}):</b>\n{file_links}"
                }
            }]
        })
    
    # Add Chat history
    if results['chats']:
        chat_history = "\n".join(
            f"💬 {msg['text'][:50]}..." 
            for msg in results['chats']
        )
        response['cards'][0]['sections'].append({
            'widgets': [{
                'textParagraph': {
                    'text': f"<b>Related Chats ({len(results['chats'])}):</b>\n{chat_history}"
                }
            }]
        })
    
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
