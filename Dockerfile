FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY atlas/ ./atlas/
COPY main.py .

# Railway sets PORT env var
ENV PORT=8080
EXPOSE 8080

# Run the agent
CMD ["python", "main.py"]
