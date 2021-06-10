# Build Assets
FROM node:12 AS build

RUN mkdir /srv/bt && chown node:node /srv/bt

USER node

WORKDIR /srv/bt

COPY --chown=node:node . .

RUN npm install --quiet --production
ENV ENV=prod
ENV ASSET_URL=/
RUN npm run bundle


# Set up runtime container
FROM node:12-slim AS production
USER node

WORKDIR /srv/bt
COPY --from=build --chown=node:node /srv/bt/ .

ENV ENV=prod
ENV NODE_ENV=production

EXPOSE 8080
CMD ["node",  "./server/index.js"]
