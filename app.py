import functions_framework
from flask import request, jsonify
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@functions_framework.http
def chat_faq_bot(request):
    """Absolute minimal working version"""
    try:
        logger.info("=== Request received ===")
        
        # Simple response without any complex logic
        return jsonify({
            "text": "✅ Cloud Run is working! Hello from the bot!",
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"text": "Error occurred"}), 500
