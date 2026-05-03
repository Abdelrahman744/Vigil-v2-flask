# ── Vigil Frontend — React + Tailwind (Vite) ────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Install dependencies (cache-friendly layer)
COPY package*.json ./
RUN npm install

# Copy application source
COPY . .

# Expose the dev-server port
EXPOSE 5173

# Start the Vite dev server, accessible from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
