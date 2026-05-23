
FROM node:20-alpine AS builder

WORKDIR /app


COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build



FROM nginx:1.27-alpine

# Remove default configuration and copy our custom nginx.conf
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

