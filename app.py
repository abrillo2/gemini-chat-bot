import functions_framework
from flask import request, jsonify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def chat_faq_bot(request):
    """Simple working version without external APIs"""
    try:
        logger.info("Received request")
        
        event = request.get_json(silent=True)
        if not event:
            return jsonify({"text": "Hello! I received your request but no message."})
        
        question = event.get("message", {}).get("text", "").strip()
        
        if not question:
            return jsonify({"text": "Hello! Please ask me a question about your emails or files."})
        
        # Simple response without external APIs
        response_text = f"Hello! I received your message: '{question}'. I'm currently in setup mode. Soon I'll be able to access your emails and drive files to help you!"
        
        logger.info(f"Responding: {response_text}")
        return jsonify({"text": response_text})
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"text": "I'm experiencing technical difficulties. Please try again later."})
