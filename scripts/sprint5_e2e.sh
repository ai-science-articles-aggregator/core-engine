#!/usr/bin/env bash
set -euo pipefail
B=http://127.0.0.1:8000/api/v1
JA=/tmp/cj_s5_alice.txt
JB=/tmp/cj_s5_bob.txt
rm -f "$JA" "$JB"
PY=python3

ok() { echo; echo "=== $* ==="; }

# ---- register alice & bob ----
ok "register alice"
curl -s -c "$JA" -b "$JA" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice5@test.com","first_name":"Alice","last_name":"Smith","password":"pass1234"}' > /dev/null

ok "register bob"
curl -s -c "$JB" -b "$JB" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"bob5@test.com","first_name":"Bob","last_name":"Jones","password":"pass1234"}' > /dev/null

ALICE_ID=$(curl -s -b "$JA" "$B/auth/profile" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
BOB_ID=$(curl -s -b "$JB" "$B/auth/profile" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "alice=$ALICE_ID bob=$BOB_ID"

# ---- alice creates notebook ----
ok "alice creates notebook"
NB=$(curl -s -b "$JA" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alice NB","description":"shared with bob","tags":["LLM"]}')
echo "$NB" | $PY -m json.tool
NBID=$(echo "$NB" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

# ---- ACCEPT 1: share with bob role=viewer ----
ok "ACCEPT 1: alice shares to bob role=viewer"
SHARE=$(curl -s -b "$JA" -X POST "$B/notebooks/$NBID/shares" \
  -H 'Content-Type: application/json' \
  -d "{\"user_email\":\"bob5@test.com\",\"role\":\"viewer\"}")
echo "$SHARE" | $PY -m json.tool

# ---- ACCEPT 2: bob sees alice's notebook in GET /notebooks ----
ok "ACCEPT 2: bob GET /notebooks → видит alice NB"
BOB_LIST=$(curl -s -b "$JB" "$B/notebooks/")
echo "$BOB_LIST" | $PY -m json.tool
NB_COUNT=$(echo "$BOB_LIST" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "bob list count=$NB_COUNT (expected 1)"
test "$NB_COUNT" = "1"

IS_OWNER=$(echo "$BOB_LIST" | $PY -c 'import sys,json; print(json.load(sys.stdin)[0]["is_owner"])')
SHARED_BY=$(echo "$BOB_LIST" | $PY -c 'import sys,json; d=json.load(sys.stdin)[0]["shared_by"]; print(d["id"] if d else None)')
echo "is_owner=$IS_OWNER (expected False)"
echo "shared_by=$SHARED_BY (expected $ALICE_ID)"
test "$IS_OWNER" = "False"
test "$SHARED_BY" = "$ALICE_ID"

# ---- ACCEPT 3: bob area=null initially, потом меняет ----
ok "ACCEPT 3a: bob's area=null до PATCH /shares/me"
AREA=$(echo "$BOB_LIST" | $PY -c 'import sys,json; print(json.load(sys.stdin)[0]["area"])')
echo "area=$AREA (expected None)"
test "$AREA" = "None"

ok "ACCEPT 3b: bob выбирает свою область"
BOB_AREAS=$(curl -s -b "$JB" "$B/areas")
BOB_AREA_ID=$(echo "$BOB_AREAS" | $PY -c 'import sys,json; print([a["id"] for a in json.load(sys.stdin) if a["slug"]=="biology"][0])')
echo "bob will attach biology area=$BOB_AREA_ID"

curl -s -b "$JB" -X PATCH "$B/notebooks/$NBID/shares/me" \
  -H 'Content-Type: application/json' \
  -d "{\"area_id\":\"$BOB_AREA_ID\"}" | $PY -m json.tool

BOB_NB=$(curl -s -b "$JB" "$B/notebooks/$NBID")
echo "$BOB_NB" | $PY -m json.tool
AREA_SLUG=$(echo "$BOB_NB" | $PY -c 'import sys,json; d=json.load(sys.stdin)["area"]; print(d["slug"] if d else None)')
echo "bob.area.slug=$AREA_SLUG (expected biology)"
test "$AREA_SLUG" = "biology"

# alice всё ещё видит тетрадь со своей областью (никакой)
ALICE_NB=$(curl -s -b "$JA" "$B/notebooks/$NBID")
ALICE_AREA=$(echo "$ALICE_NB" | $PY -c 'import sys,json; print(json.load(sys.stdin)["area"])')
echo "alice still sees area=$ALICE_AREA (expected None)"

# ---- ACCEPT 4: PUT от bob (role=viewer) → 403 ----
ok "ACCEPT 4: bob (viewer) PUT → 403"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X PUT "$B/notebooks/$NBID" \
  -H 'Content-Type: application/json' \
  -d '{"name":"hack","visibility":"public"}')
echo "http=$HTTP (expected 403)"
test "$HTTP" = "403"

# DELETE от bob → 403
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X DELETE "$B/notebooks/$NBID")
echo "bob delete http=$HTTP (expected 403)"
test "$HTTP" = "403"

# ---- bonus: promote bob to editor → теперь PUT работает ----
ok "BONUS: alice promotes bob to editor"
curl -s -b "$JA" -X DELETE "$B/notebooks/$NBID/shares/$BOB_ID" -o /dev/null -w '%{http_code}\n'
curl -s -b "$JA" -X POST "$B/notebooks/$NBID/shares" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"$BOB_ID\",\"role\":\"editor\"}" > /dev/null

HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X PUT "$B/notebooks/$NBID" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alice NB (edited by Bob)"}')
echo "bob editor PUT http=$HTTP (expected 200)"
test "$HTTP" = "200"

# DELETE от bob (editor) всё ещё запрещён — только owner может удалять
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X DELETE "$B/notebooks/$NBID")
echo "bob editor delete http=$HTTP (expected 403)"
test "$HTTP" = "403"

# ---- self-share guard ----
ok "GUARD: alice tries to share to herself → 400"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JA" -X POST "$B/notebooks/$NBID/shares" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"$ALICE_ID\",\"role\":\"viewer\"}")
echo "http=$HTTP (expected 400)"
test "$HTTP" = "400"

# ---- duplicate share ----
ok "GUARD: alice пытается ещё раз шарить bob → 409"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JA" -X POST "$B/notebooks/$NBID/shares" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"$BOB_ID\",\"role\":\"viewer\"}")
echo "http=$HTTP (expected 409)"
test "$HTTP" = "409"

# ---- area_id чужой при PATCH /shares/me → 400 ----
ok "GUARD: bob пытается привязать area_id Алисы → 400"
ALICE_AREA_ID=$(curl -s -b "$JA" "$B/areas" | $PY -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X PATCH "$B/notebooks/$NBID/shares/me" \
  -H 'Content-Type: application/json' \
  -d "{\"area_id\":\"$ALICE_AREA_ID\"}")
echo "http=$HTTP (expected 400)"
test "$HTTP" = "400"

# ---- filters ----
ok "FILTER: bob ?owned_only=true → 0, ?shared_only=true → 1"
NB1=$(curl -s -b "$JB" "$B/notebooks/?owned_only=true" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
NB2=$(curl -s -b "$JB" "$B/notebooks/?shared_only=true" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "owned=$NB1 shared=$NB2 (expected 0 / 1)"
test "$NB1" = "0"
test "$NB2" = "1"

ok "FILTER: ?q=alice → 1 (matches name)"
NB1=$(curl -s -b "$JB" "$B/notebooks/?q=alice" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "q=alice → $NB1 (expected 1)"
test "$NB1" = "1"

# ---- ACCEPT 5: alice deletes notebook → bob не видит ----
ok "ACCEPT 5: alice deletes notebook → cascade в shares"
curl -s -b "$JA" -X DELETE "$B/notebooks/$NBID" > /dev/null
BOB_AFTER=$(curl -s -b "$JB" "$B/notebooks/" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "bob notebooks after alice delete=$BOB_AFTER (expected 0)"
test "$BOB_AFTER" = "0"

# share row тоже удалена?
SHARES_LEFT=$(docker exec postgres psql -U root -d appdb -tAc "SELECT COUNT(*) FROM notebook_shares;")
echo "notebook_shares rows in DB=$SHARES_LEFT (expected 0)"
test "$SHARES_LEFT" = "0"

ok "ALL SPRINT 5 ACCEPTANCE PASSED"
