# Step 1 - Build Front End Application
FROM node:16 AS build

# Copy the entire project - Webpack puts compiled assets into the Django folder
WORKDIR /app
COPY . .

RUN cd frontend && npm install --quiet --production
ENV ENV=prod
ENV ASSET_URL=/
RUN cd frontend && npm run bundledjango


# Step 2 - Build Django Application
FROM python:3.9-slim as application

WORKDIR /app
COPY api /app/

# arm architecture platform builds need postgres drivers installing via apt #todo: can be removed possibly at some point
ARG TARGETARCH
RUN if [ "$TARGETARCH" != "amd64" ]; then apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Install python dependencies
RUN pip install -r requirements.txt --no-cache-dir --compile

# Compile static Django assets
RUN python /app/manage.py collectstatic --no-input

# Copy the compiled front end assets from the previous build step
COPY --from=build /app/api/static /app/static/
COPY --from=build /app/api/app/templates/webpack /app/app/templates/webpack

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}
ENV DJANGO_SETTINGS_MODULE=app.settings.production

EXPOSE 8000

USER nobody

ENTRYPOINT ["./scripts/run-docker.sh"]

# other options below are `migrate` or `serve`
CMD ["migrate-and-serve"]
