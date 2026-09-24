# The dashboard, for Cloud Run.
#
# The 13 agents are NOT in this image and cannot be: they need the local
# Chrome bridge, the Brain DB, font files and four minutes per cycle. The
# pipeline runs on the founder's machine and pushes each run to GCS; this
# container reads from there. That seam is what `lib/gcs.ts` implements.

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || npm install --omit=dev

FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=8080
# Standalone ships its own minimal node_modules; static and public are not
# included in it and have to be copied alongside.
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
EXPOSE 8080
CMD ["node", "server.js"]
