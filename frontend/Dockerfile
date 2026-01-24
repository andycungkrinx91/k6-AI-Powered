# ---------- Base ----------
FROM node:24-alpine AS base
WORKDIR /app
RUN corepack enable

# ---------- Dependencies ----------
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ---------- Builder ----------
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
COPY .env .env
RUN pnpm build

# ---------- Runner ----------
FROM node:24-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN corepack enable

# Copy standalone build
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
#COPY --from=builder /app/public ./public
COPY .env /app/.env

EXPOSE 3000

CMD ["node", "server.js", "--hostname", "0.0.0.0", "--port", "3000"]
