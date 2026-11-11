# MinIO's official prebuilt image tag is no longer available. Build its
# security-fix release from the upstream project for local development.
FROM golang:1.25-alpine AS build
RUN apk add --no-cache git ca-certificates
RUN CGO_ENABLED=0 go install github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z
FROM alpine:3.22
RUN apk add --no-cache ca-certificates
COPY --from=build /go/bin/minio /usr/local/bin/minio
ENTRYPOINT ["minio"]
