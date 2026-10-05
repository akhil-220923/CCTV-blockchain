# Stage 1: Build the production SSR bundle
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package manifests first for efficient layer caching
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Copy application source and build production artifacts
COPY . .
RUN npm run build

# Stage 2: Minimal Production SSR Runner
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Copy pre-compiled Nitro node-server output
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
