FROM python:3.11-slim

# Install ffmpeg + Node.js (needed for yt-dlp EJS signature solver) + git
RUN apt-get update && \
    apt-get install -y ffmpeg nodejs npm git && \
    rm -rf /var/lib/apt/lists/*

# Setup PO Token provider HTTP server
RUN git clone https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /pot-provider && \
    cd /pot-provider/server && \
    npm ci && \
    npx tsc

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Expose port 7860 for Hugging Face Spaces health check
EXPOSE 7860

# Start the PO token server in the background, then start the bot
CMD node /pot-provider/server/build/main.js & python main.py
