FROM selenium/standalone-chrome

USER root

# Install Python 3.11 from deadsnakes PPA without add-apt-repository
RUN apt-get update \
    && apt-get install -y curl gnupg lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && apt-get update \
    && apt-get install -y python3.11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Ensure temp directory exists
RUN mkdir -p headless-browser-scraper/temp

# Set PYTHONPATH
ENV PYTHONPATH=.

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
