# Étape 1 : Builder l'application Next.js
FROM node:18-alpine AS builder

WORKDIR /app

# Copier les fichiers de dépendances
COPY package.json package-lock.json* ./

# Installer les dépendances
RUN npm ci

# Copier le reste du code source
COPY . .

# Construire l'application
RUN npm run build

# Étape 2 : Image de production runner
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV production

# Créer un utilisateur non-root (bonne pratique)
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copier les fichiers nécessaires depuis le builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Passer à l'utilisateur nextjs
USER nextjs

EXPOSE 3000

ENV PORT 3000

# Démarrer l'application
CMD ["node", "server.js"]
