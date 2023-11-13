# Build Assets
FROM node:16 AS build

RUN mkdir /srv/bt && chown node:node /srv/bt

USER node

WORKDIR /srv/bt

COPY --chown=node:node frontend/package.json frontend/package-lock.json frontend/.npmrc frontend/.nvmrc ./
COPY --chown=node:node frontend/bin/ ./bin/
COPY --chown=node:node frontend/env/ ./env/

RUN npm ci --quiet --production

COPY --chown=node:node frontend .
COPY .release-please-manifest.json .
ENV ENV=prod
RUN npm run bundle


# Set up runtime container
FROM node:16-slim AS production
USER node

WORKDIR /srv/bt
COPY --from=build --chown=node:node /srv/bt/ .

ENV ENV=prod
ENV NODE_ENV=production

EXPOSE 8080
CMD ["node",  "./api/index.js"]
