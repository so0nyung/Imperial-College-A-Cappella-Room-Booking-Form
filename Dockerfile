# Use official Python slim image
FROM python:3.11-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome via official Google repo
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
      http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
# selenium>=4.10 ships with selenium-manager which auto-downloads ChromeDriver
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-warm selenium-manager so it downloads ChromeDriver at build time
RUN python -c "from selenium import webdriver; from selenium.webdriver.chrome.options import Options; o=Options(); o.add_argument('--headless'); o.add_argument('--no-sandbox'); o.add_argument('--disable-dev-shm-usage'); webdriver.Chrome(options=o).quit()" || true

# Copy app files
COPY . .

# Expose port
EXPOSE 8000

# Start the app
CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]