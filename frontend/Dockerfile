# Build Assets
FROM node:16 AS build

RUN mkdir /srv/bt && chown node:node /srv/bt

USER node

WORKDIR /srv/bt

COPY --chown=node:node package.json package-lock.json .npmrc .nvmrc ./
COPY --chown=node:node bin/ ./bin/
COPY --chown=node:node env/ ./env/

RUN npm ci --quiet --production

COPY --chown=node:node . .
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
