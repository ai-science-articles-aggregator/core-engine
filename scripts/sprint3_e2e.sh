#!/usr/bin/env bash
set -euo pipefail
B=http://127.0.0.1:8000/api/v1
J=/tmp/cj_s3.txt
J2=/tmp/cj_s3_bob.txt
rm -f "$J" "$J2"
PY=python3

ok() { echo; echo "=== $* ==="; }

ok "register alice"
curl -s -c "$J" -b "$J" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice3@test.com","first_name":"Alice","last_name":"Smith","department":"CS","password":"pass1234"}' | $PY -m json.tool

ok "ACCEPT 1: alice has 10 default areas"
ALICE_AREAS=$(curl -s -b "$J" "$B/areas")
echo "$ALICE_AREAS" | $PY -m json.tool
N=$(echo "$ALICE_AREAS" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "areas_count=$N (expected 10)"
test "$N" = "10"

ok "ACCEPT 3: POST /areas Linguistics → 201, slug=linguistics"
NEW=$(curl -s -b "$J" -X POST "$B/areas" -H 'Content-Type: application/json' -d '{"name":"Linguistics","palette_key":"plum"}')
echo "$NEW" | $PY -m json.tool
NEW_ID=$(echo "$NEW" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
SLUG=$(echo "$NEW" | $PY -c 'import sys,json; print(json.load(sys.stdin)["slug"])')
test "$SLUG" = "linguistics"

ok "ACCEPT 4: повтор → 409 Conflict"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$J" -X POST "$B/areas" -H 'Content-Type: application/json' -d '{"name":"linguistics"}')
echo "http=$HTTP (expected 409)"
test "$HTTP" = "409"

ok "PATCH rename + recolor"
ML_ID=$(echo "$ALICE_AREAS" | $PY -c 'import sys,json; print([a["id"] for a in json.load(sys.stdin) if a["slug"]=="machine-learning"][0])')
curl -s -b "$J" -X PATCH "$B/areas/$ML_ID" -H 'Content-Type: application/json' \
  -d '{"name":"ML & AI","palette_key":"amber"}' | $PY -m json.tool

ok "register bob (отдельная кука)"
curl -s -c "$J2" -b "$J2" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"bob3@test.com","first_name":"Bob","last_name":"Jones","password":"pass1234"}' > /dev/null
BOB_AREAS=$(curl -s -b "$J2" "$B/areas")
NB=$(echo "$BOB_AREAS" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "bob_areas=$NB (expected 10)"
test "$NB" = "10"

ok "ACCEPT 5: alice пытается создать notebook с area_id Боба → 400"
BOB_AREA_ID=$(echo "$BOB_AREAS" | $PY -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"hack\",\"area_id\":\"$BOB_AREA_ID\"}")
echo "http=$HTTP (expected 400)"
test "$HTTP" = "400"

ok "alice создаёт notebook со СВОИМ area_id (Linguistics)"
NB=$(curl -s -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"My NB\",\"area_id\":\"$NEW_ID\"}")
echo "$NB" | $PY -m json.tool
NBID=$(echo "$NB" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

ok "ACCEPT 6: DELETE area → 204, GET /areas её не возвращает, notebook остаётся"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$J" -X DELETE "$B/areas/$NEW_ID")
echo "delete_http=$HTTP (expected 204)"
test "$HTTP" = "204"

REMAIN=$(curl -s -b "$J" "$B/areas" | $PY -c 'import sys,json; data=json.load(sys.stdin); print(any(a["slug"]=="linguistics" for a in data))')
echo "linguistics_present_after_delete=$REMAIN (expected False)"
test "$REMAIN" = "False"

NB_AFTER=$(curl -s -b "$J" "$B/notebooks/$NBID")
echo "$NB_AFTER" | $PY -m json.tool
NB_AREA=$(echo "$NB_AFTER" | $PY -c 'import sys,json; data=json.load(sys.stdin); print(data["area"])')
echo "notebook.area after area delete = $NB_AREA (expected None)"
test "$NB_AREA" = "None"

ok "ALL SPRINT 3 ACCEPTANCE PASSED"
