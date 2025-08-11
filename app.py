from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.auth import default
import os

app = Flask(__name__)

@app.route('/', methods=['POST'])
def faq_bot():
    credentials, _ = default()
    
    # Initialize APIs
    gmail = build('gmail', 'v1', credentials=credentials)
    drive = build('drive', 'v3', credentials=credentials)
    
    # Process query
    query = request.json.get('message', {}).get('text', '')
    
    # Search services
    results = {
        'gmail': gmail.users().messages().list(
            userId='me',
            q=query,
            maxResults=3
        ).execute(),
        'drive': drive.files().list(
            q=f"fullText contains '{query}'",
            pageSize=3
        ).execute()
    }
    
    return jsonify({
        'text': f"Found {len(results['gmail'].get('messages', []))} emails",
        'cards': [{
            'header': {'title': 'Results'},
            'sections': [{
                'widgets': [{
                    'textParagraph': {
                        'text': f"Drive files found: {len(results['drive'].get('files', []))}"
                    }
                }]
            }]
        }]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
