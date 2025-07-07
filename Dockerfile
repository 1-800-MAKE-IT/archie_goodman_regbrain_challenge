#this file was created by chatgpt 
# ---------- base image ----------
FROM python:3.10-slim

# ---------- workdir ----------
WORKDIR /app

# ---------- OS packages ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ---------- Python deps ----------
COPY requirements.txt .

# Force CPU-only PyTorch
ENV PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ---------- project code ----------
COPY . .

# ---------- expose dev ports ----------
EXPOSE 8501 8000

# ---------- default cmd ----------
CMD ["bash"]