FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run Functions Framework directly
CMD ["functions-framework", "--target=chat_faq_bot", "--source=app.py", "--port=8080"]
