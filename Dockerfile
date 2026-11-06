FROM python:3.12-slim

# Tizim paketlari, ffmpeg va nodejs o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Talablar faylini ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha fayllarni ko'chirish
COPY . .

# Render beradigan PORT o'zgaruvchisi
ENV PORT=10000
EXPOSE 10000

# Botni ishga tushirish
CMD ["python", "bot.py"]
