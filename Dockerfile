# ---- Frontend build (Next.js) ----
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# ---- Runtime deps (Python venv built in the runtime image) ----
FROM node:22-alpine AS runtime-deps
RUN apk add --no-cache python3 py3-pip \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip
ENV PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10
WORKDIR /tmp/deps
COPY backend/requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime (serves frontend on $PORT, proxies /api to uvicorn on :8765) ----
FROM node:22-alpine
RUN apk add --no-cache python3
WORKDIR /app
ENV PATH="/opt/venv/bin:/app/frontend/node_modules/.bin:$PATH"
COPY --from=runtime-deps /opt/venv /opt/venv
COPY backend/app /app/app
COPY --from=frontend-build /build/.next /app/frontend/.next
COPY --from=frontend-build /build/public /app/frontend/public
COPY --from=frontend-build /build/node_modules /app/frontend/node_modules
COPY --from=frontend-build /build/package.json /app/frontend/package.json
COPY --from=frontend-build /build/next.config.ts /app/frontend/next.config.ts
COPY --from=frontend-build /build/tsconfig.json /app/frontend/tsconfig.json
COPY --from=frontend-build /build/next-env.d.ts /app/frontend/next-env.d.ts
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh
EXPOSE 8765
CMD ["/app/start.sh"]