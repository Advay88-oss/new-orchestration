# Mission Control dashboard — Cloud Run container (fixture mode, self-contained).
# No secrets, no D:/ paths: pages render from bundled lib/fixture.json.
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim AS run
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=8080
# Next.js standalone output bundles only what the server needs
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
EXPOSE 8080
CMD ["node", "server.js"]
