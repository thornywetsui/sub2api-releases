ARG ALPINE_IMAGE=alpine:3.21
ARG POSTGRES_IMAGE=postgres:18-alpine
FROM ${POSTGRES_IMAGE} AS pg-client
FROM ${ALPINE_IMAGE}
LABEL maintainer="Anonymous"
LABEL description="Sub2API - AI API Gateway Platform"
LABEL org.opencontainers.image.source="https://github.com/thornywetsui/sub2api-releases"

RUN apk add --no-cache ca-certificates tzdata curl su-exec libpq \
    zstd-libs lz4-libs krb5-libs libldap libedit
COPY --from=pg-client /usr/local/bin/pg_dump /usr/local/bin/pg_dump
COPY --from=pg-client /usr/local/bin/psql /usr/local/bin/psql
COPY --from=pg-client /usr/local/lib/libpq.so.5* /usr/local/lib/
RUN addgroup -g 1000 sub2api && \
    adduser -u 1000 -G sub2api -s /bin/sh -D sub2api
WORKDIR /app
# 上下文仅由通过校验的发布资产和公开入口脚本构成。
COPY sub2api /app/sub2api
COPY --chown=sub2api:sub2api backend/resources /app/resources
COPY deploy/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN mkdir -p /app/data && chown -R sub2api:sub2api /app && \
    chmod +x /app/sub2api /app/docker-entrypoint.sh
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT:-8080}/health || exit 1
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["/app/sub2api"]
