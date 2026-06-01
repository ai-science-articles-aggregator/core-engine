#!/usr/bin/env bash
set -euo pipefail
B=http://127.0.0.1:8000/api/v1
J=/tmp/cj.txt
rm -f "$J"
PY=python3

echo "--- register ---"
curl -s -c "$J" -b "$J" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"sprint2@test.com","first_name":"Sprint","last_name":"Two","department":"CS","password":"pass1234"}' \
  | $PY -m json.tool || true

echo "--- profile ---"
curl -s -b "$J" "$B/auth/profile" | $PY -m json.tool

echo "--- create notebook with new fields ---"
NB=$(curl -s -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-1","description":"hello","tags":["Attention","4K"],"visibility":"shared"}')
echo "$NB" | $PY -m json.tool
NBID=$(echo "$NB" | $PY -c 'import sys, json; print(json.load(sys.stdin)["id"])')
echo "NBID=$NBID"

echo "--- list notebooks ---"
curl -s -b "$J" "$B/notebooks/" | $PY -m json.tool

echo "--- update visibility=private ---"
curl -s -b "$J" -X PUT "$B/notebooks/$NBID" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-1-renamed","visibility":"private"}' \
  | $PY -m json.tool

echo "--- get single ---"
curl -s -b "$J" "$B/notebooks/$NBID" | $PY -m json.tool

echo "--- delete ---"
curl -s -b "$J" -X DELETE "$B/notebooks/$NBID" | $PY -m json.tool

echo "--- list after delete ---"
curl -s -b "$J" "$B/notebooks/" | $PY -m json.tool

echo "--- POST with garbage area_id (should not 422) ---"
curl -s -o /dev/null -w 'http=%{http_code}\n' -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-2","area_id":null}'
