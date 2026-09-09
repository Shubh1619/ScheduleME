# ---- Frontend build (Next.js static export) ----
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# ---- Runtime deps (Python venv) ----
FROM python:3.11-alpine AS runtime-deps
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip
ENV PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10
WORKDIR /tmp/deps
COPY backend/requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime (single process: uvicorn serves API + static frontend on $PORT) ----
FROM python:3.11-alpine
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=runtime-deps /opt/venv /opt/venv
COPY backend/app /app/app
COPY --from=frontend-build /build/out /app/frontend_out
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh
EXPOSE 10000
CMD ["/app/start.sh"]