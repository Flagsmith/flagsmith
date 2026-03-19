FROM golang:1.25-bookworm AS builder

WORKDIR /build

# Install OCB
RUN GO111MODULE=on go install go.opentelemetry.io/collector/cmd/builder@v0.147.0

# Copy source
COPY builder-config.yaml .
COPY exporter/ ./exporter/

# Build the collector
RUN CGO_ENABLED=0 builder --config=builder-config.yaml

# --- Runtime ---
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /build/build/otelcol-flagsmith /otelcol-flagsmith

EXPOSE 4317 4318

ENTRYPOINT ["/otelcol-flagsmith"]
CMD ["--config=/etc/otelcol/config.yaml"]
