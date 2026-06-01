#!/usr/bin/env bash
set -euo pipefail
B=http://127.0.0.1:8000/api/v1
JA=/tmp/cj_s6_alice.txt
JB=/tmp/cj_s6_bob.txt
rm -f "$JA" "$JB"
PY=python3

ok() { echo; echo "=== $* ==="; }

ok "register alice & bob"
curl -s -c "$JA" -b "$JA" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice6@test.com","first_name":"Alice","last_name":"Smith","password":"pass1234"}' > /dev/null
curl -s -c "$JB" -b "$JB" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"bob6@test.com","first_name":"Bob","last_name":"Jones","password":"pass1234"}' > /dev/null
ALICE_ID=$(curl -s -b "$JA" "$B/auth/profile" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
BOB_ID=$(curl -s -b "$JB" "$B/auth/profile" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

ok "alice creates notebook"
NB=$(curl -s -b "$JA" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Research"}')
NBID=$(echo "$NB" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "NBID=$NBID"

ok "alice shares to bob as viewer"
curl -s -b "$JA" -X POST "$B/notebooks/$NBID/shares" \
  -H 'Content-Type: application/json' \
  -d "{\"user_email\":\"bob6@test.com\",\"role\":\"viewer\"}" > /dev/null

# ---- seed Articles directly in DB (RAG legacy, у нас нет реального RAG в тесте) ----
ok "seed two articles into DB"
docker exec postgres psql -U root -d appdb -c \
  "INSERT INTO articles (id, arxiv_id, title, authors, score, notebook_id) VALUES
   ('11111111-1111-1111-1111-111111111111','arxiv:2401.1','Attention Is All You Need','Vaswani et al',0.91,'$NBID'),
   ('22222222-2222-2222-2222-222222222222','arxiv:2402.2','BERT','Devlin et al',0.87,'$NBID');" > /dev/null

# ---- SOURCES ----
ok "alice POST sources"
RES=$(curl -s -b "$JA" -X POST "$B/notebooks/$NBID/sources" \
  -H 'Content-Type: application/json' \
  -d '{"article_ids":["11111111-1111-1111-1111-111111111111","22222222-2222-2222-2222-222222222222"]}')
echo "$RES" | $PY -m json.tool
N=$(echo "$RES" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "sources count=$N (expected 2)"
test "$N" = "2"

ok "alice GET sources"
curl -s -b "$JA" "$B/notebooks/$NBID/sources" | $PY -m json.tool

ok "alice PATCH source.selected=false"
curl -s -b "$JA" -X PATCH "$B/notebooks/$NBID/sources/22222222-2222-2222-2222-222222222222" \
  -H 'Content-Type: application/json' \
  -d '{"selected":false}' | $PY -m json.tool

ok "bob (viewer) PATCH source → 403"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X PATCH "$B/notebooks/$NBID/sources/11111111-1111-1111-1111-111111111111" \
  -H 'Content-Type: application/json' -d '{"selected":false}')
echo "http=$HTTP (expected 403)"
test "$HTTP" = "403"

ok "bob (viewer) GET sources → 200"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" "$B/notebooks/$NBID/sources")
echo "http=$HTTP (expected 200)"
test "$HTTP" = "200"

ok "alice DELETE source"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JA" -X DELETE "$B/notebooks/$NBID/sources/22222222-2222-2222-2222-222222222222")
echo "http=$HTTP (expected 204)"
test "$HTTP" = "204"

# ---- NOTES ----
ok "alice POST note"
NOTE=$(curl -s -b "$JA" -X POST "$B/notebooks/$NBID/notes" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Alice note","body":"first"}')
echo "$NOTE" | $PY -m json.tool
NOTE_ID=$(echo "$NOTE" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

ok "bob (viewer) POST note → 403"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X POST "$B/notebooks/$NBID/notes" \
  -H 'Content-Type: application/json' -d '{"title":"Bob","body":"hi"}')
echo "http=$HTTP (expected 403 — viewer не пишет notes)"
test "$HTTP" = "403"

ok "promote bob to commenter"
curl -s -b "$JA" -X DELETE "$B/notebooks/$NBID/shares/$BOB_ID" > /dev/null
curl -s -b "$JA" -X POST "$B/notebooks/$NBID/shares" \
  -H 'Content-Type: application/json' \
  -d "{\"user_id\":\"$BOB_ID\",\"role\":\"commenter\"}" > /dev/null

ok "bob (commenter) POST note → 201"
BOB_NOTE=$(curl -s -b "$JB" -X POST "$B/notebooks/$NBID/notes" \
  -H 'Content-Type: application/json' -d '{"title":"Bob","body":"hi from bob"}')
echo "$BOB_NOTE" | $PY -m json.tool
BOB_NOTE_ID=$(echo "$BOB_NOTE" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

ok "bob (commenter) PATCH Alice's note → 403"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X PATCH "$B/notebooks/$NBID/notes/$NOTE_ID" \
  -H 'Content-Type: application/json' -d '{"body":"hacked"}')
echo "http=$HTTP (expected 403 — bob не автор)"
test "$HTTP" = "403"

ok "bob (commenter) PATCH своей заметки → 200"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JB" -X PATCH "$B/notebooks/$NBID/notes/$BOB_NOTE_ID" \
  -H 'Content-Type: application/json' -d '{"body":"edited by bob"}')
echo "http=$HTTP (expected 200)"
test "$HTTP" = "200"

ok "alice (owner) DELETE bob's note → 204 (owner-override)"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$JA" -X DELETE "$B/notebooks/$NBID/notes/$BOB_NOTE_ID")
echo "http=$HTTP (expected 204)"
test "$HTTP" = "204"

# ---- CHAT ----
ok "alice GET messages → пусто"
M=$(curl -s -b "$JA" "$B/notebooks/$NBID/messages")
echo "$M" | $PY -m json.tool
COUNT=$(echo "$M" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
test "$COUNT" = "0"

ok "alice POST message — SSE стрим"
RAW=$(curl -s -N -b "$JA" -X POST "$B/notebooks/$NBID/messages" \
  -H 'Content-Type: application/json' -d '{"text":"summarize"}' || true)
echo "$RAW" | tail -10

ok "после POST messages → 2 сообщения (user + assistant/system)"
M2=$(curl -s -b "$JA" "$B/notebooks/$NBID/messages")
echo "$M2" | $PY -m json.tool
COUNT=$(echo "$M2" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "count=$COUNT (expected 2)"
test "$COUNT" = "2"

ROLES=$(echo "$M2" | $PY -c 'import sys,json; print([m["role"] for m in json.load(sys.stdin)])')
echo "roles=$ROLES"

ok "bob (commenter) POST message → 201/stream"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -N -b "$JB" -X POST "$B/notebooks/$NBID/messages" \
  -H 'Content-Type: application/json' -d '{"text":"hi"}')
echo "http=$HTTP (expected 200)"
test "$HTTP" = "200"

# ---- counts in notebook list ----
ok "GET /notebooks → sources_count и notes_count соответствуют"
LST=$(curl -s -b "$JA" "$B/notebooks/")
echo "$LST" | $PY -m json.tool
SC=$(echo "$LST" | $PY -c 'import sys,json; print(json.load(sys.stdin)[0]["sources_count"])')
NC=$(echo "$LST" | $PY -c 'import sys,json; print(json.load(sys.stdin)[0]["notes_count"])')
echo "sources_count=$SC notes_count=$NC (expected 1 / 1)"
test "$SC" = "1"
test "$NC" = "1"

ok "ALL SPRINT 6 ACCEPTANCE PASSED"
