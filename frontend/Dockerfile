# Build Stage
FROM node:20-slim as builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .

RUN npm run build

# Serve Stage
FROM nginx:alpine

# Add bash for the startup script
RUN apk add --no-cache bash

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/public/env.js /usr/share/nginx/html/env.js.template

EXPOSE 80

CMD ["/bin/sh", "-c", "envsubst < /usr/share/nginx/html/env.js.template > /usr/share/nginx/html/env.js && nginx -g 'daemon off;'"]
