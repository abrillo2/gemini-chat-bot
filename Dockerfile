FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run the Functions Framework
CMD ["functions-framework", "--target=chat_faq_bot", "--source=app.py", "--port=8080"]
