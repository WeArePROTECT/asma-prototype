# --- Backend ---
FROM python:3.13-slim AS backend
WORKDIR /app
COPY backend/ /app
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

# --- Frontend ---
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/ /frontend
RUN npm install && npm run build

# --- Final combined image ---
FROM python:3.13-slim
WORKDIR /app
COPY --from=backend /app /app
COPY --from=frontend /frontend/dist /app/static
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]