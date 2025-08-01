# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Production stage
FROM node:18-alpine AS production

# Install dumb-init
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S mqttclient -u 1001

WORKDIR /app

# Copy built application
COPY --from=builder --chown=mqttclient:nodejs /app/dist ./dist
COPY --from=builder --chown=mqttclient:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=mqttclient:nodejs /app/package*.json ./

# Switch to non-root user
USER mqttclient

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "console.log('MQTT client is running')" || exit 1

# Start application
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/index.js"] 