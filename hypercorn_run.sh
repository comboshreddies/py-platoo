#!/bin/sh
export VERBOSE_VALIDATION="on"
export PG_CONNECT="dbname=postgres user=postgres host=127.0.0.1"
export OAPI_DOCS="/docs"
export OAPI_JSON="/openapi.json"
WORK=${WORKERS:-4}
# S_NAME=${SERVER_NAME:-pyplatoo} # --server-name "$S_NAME" 
#hypercorn -w "$WORK" -k asyncio --statsd-host localhost -c ./hypercorn.toml asgi:api:app
hypercorn -c ./hypercorn.toml asgi:api:app
