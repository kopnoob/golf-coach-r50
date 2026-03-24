FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_PATH=/app/data/golf_coach.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
