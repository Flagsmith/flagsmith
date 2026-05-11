# Minimal launcher image: the upstream flagd image is distroless (no
# /bin/sh), but our local-dev compose needs a shell to source the
# server-side key from a file written by `bootstrap_flagd_local`.
# This image copies the flagd binary into an alpine base.
FROM ghcr.io/open-feature/flagd:v0.13.2 AS flagd
FROM alpine:3.20
COPY --from=flagd /flagd-build /usr/local/bin/flagd
ENTRYPOINT ["/bin/sh", "-c"]
