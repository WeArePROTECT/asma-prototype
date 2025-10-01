# --- Backend ---
FROM python:3.13-slim AS backend
WORKDIR /app
# Copy requirements first so they can be cached
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Now copy backend code
COPY backend/ /app
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
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
