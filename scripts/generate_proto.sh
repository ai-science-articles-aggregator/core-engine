#!/bin/bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

uv run python -m grpc_tools.protoc \
  -I "$ROOT/proto_contracts" \
  --python_out="$ROOT/generated" \
  --grpc_python_out="$ROOT/generated" \
  "$ROOT/proto_contracts/rag/v1/rag.proto" \
  "$ROOT/proto_contracts/summary/v1/summary.proto"

echo "Done → $ROOT/generated/"
