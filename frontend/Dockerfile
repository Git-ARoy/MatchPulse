FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S -g 10001 matchpulse && adduser -S -u 10001 -G matchpulse matchpulse
COPY --from=build --chown=matchpulse:matchpulse /app ./
USER matchpulse
EXPOSE 3000
CMD ["npm", "run", "start"]
