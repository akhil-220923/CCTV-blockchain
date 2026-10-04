FROM node:22-alpine

WORKDIR /app

# Copy package manifests first for efficient caching
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

ENV PORT=3000 \
    HOST=0.0.0.0 \
    VITE_BACKEND_URL=http://backend:5000

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
