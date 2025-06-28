# Running

In order to run MCP server, following env vars must be configured

```
KEYCLOAK_SERVER_URL
KEYCLOAK_REALM

OTEL_ENABLED=false
# Optional when OTEL_ENABLED is true (OpenTelemetry)
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT
OTEL_AUTH_TOKEN
```

For client:

```
GOOGLE_API_KEY
MCP_SERVER_URL
REFRESH_TOKEN (User refresh token after sucessfully authentifying with keycloak)
```