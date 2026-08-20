# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance folder for SQLite
RUN mkdir -p /app/instance

# Environment
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["python", "run.py"]
