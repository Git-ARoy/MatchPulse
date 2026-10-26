FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup -S -g 10001 matchpulse && adduser -S -u 10001 -G matchpulse matchpulse
COPY --from=build --chown=matchpulse:matchpulse /app/public ./public
COPY --from=build --chown=matchpulse:matchpulse /app/.next/standalone ./
COPY --from=build --chown=matchpulse:matchpulse /app/.next/static ./.next/static
USER matchpulse
EXPOSE 3000
CMD ["node", "server.js"]
