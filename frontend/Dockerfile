# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Clean install
RUN npm ci

# Copy source code
COPY . .

# Set environment variables for build
ENV GENERATE_SOURCEMAP=false
ENV REACT_APP_API_URL=http://localhost:5000/api

# Build app
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 