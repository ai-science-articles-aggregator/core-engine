#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

uv run python -m grpc_tools.protoc \
  -I "$ROOT/proto_contracts" \
  --python_out="$ROOT/generated" \
  --grpc_python_out="$ROOT/generated" \
  "$ROOT/proto_contracts/retrieval/v1/retrieval.proto" \
  "$ROOT/proto_contracts/agent/v1/agent.proto"

echo "Done → $ROOT/generated/"
