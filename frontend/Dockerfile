# 1. Build Stage
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Build production bundle
COPY frontend/ ./
RUN npm run build

# 2. Runtime Stage
FROM nginx:alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

