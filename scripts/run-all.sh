#!/usr/bin/env bash
# Start the stack fresh, run every scenario, and write transcripts to captures/.
set -euo pipefail
cd "$(dirname "$0")/.."

# --force-recreate matters: keys are generated at process start, and agentgateway
# loads the JWKS once at startup. A restarted IdP or AS with a stale gateway
# fails every token with InvalidSignature.
docker compose up -d --build --force-recreate

until [ "$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:43000/mcp)" = "401" ]; do
  sleep 1
done

for args in "alice" "bob" "carol" "alice --attacks" "alice --gateway-xaa"; do
  echo "== client $args"
  # shellcheck disable=SC2086
  docker compose run --rm --no-deps client $args > /dev/null
done

docker compose logs --no-log-prefix idp > captures/idp.log
docker compose logs --no-log-prefix as > captures/notes-as.log
docker compose logs --no-log-prefix notes-mcp > captures/notes-mcp.log
echo "== transcripts"
ls captures
