#!/usr/bin/env bash
set -euo pipefail
B=http://127.0.0.1:8000/api/v1
J=/tmp/cj_s7.txt
rm -f "$J"
PY=python3

ok() { echo; echo "=== $* ==="; }

ok "register alice"
curl -s -c "$J" -b "$J" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice7@test.com","first_name":"Alice","last_name":"Smith","password":"pass1234"}' > /dev/null

ok "create two notebooks N1, N2"
N1=$(curl -s -b "$J" -X POST "$B/notebooks/create" -H 'Content-Type: application/json' \
  -d '{"name":"N1"}' | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
N2=$(curl -s -b "$J" -X POST "$B/notebooks/create" -H 'Content-Type: application/json' \
  -d '{"name":"N2"}' | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "N1=$N1 N2=$N2"

ok "POST /N1/sources [arxiv:2401.001, arxiv:2401.002]"
SRC1=$(curl -s -b "$J" -X POST "$B/notebooks/$N1/sources" -H 'Content-Type: application/json' \
  -d '{"article_ids":["arxiv:2401.001","arxiv:2401.002"]}')
echo "$SRC1" | $PY -m json.tool
COUNT=$(echo "$SRC1" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "count=$COUNT (expected 2)"; test "$COUNT" = "2"

ok "POST /N2/sources [arxiv:2401.001] — cross-notebook reuse"
SRC2=$(curl -s -b "$J" -X POST "$B/notebooks/$N2/sources" -H 'Content-Type: application/json' \
  -d '{"article_ids":["arxiv:2401.001"]}')
echo "$SRC2" | $PY -m json.tool
COUNT=$(echo "$SRC2" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "count=$COUNT (expected 1)"; test "$COUNT" = "1"

ok "DB: один и тот же arxiv:2401.001 в обоих notebook'ах"
docker exec postgres psql -U root -d appdb -c "SELECT notebook_id, article_id FROM notebook_sources WHERE article_id = 'arxiv:2401.001' ORDER BY notebook_id;"
NDISTINCT=$(docker exec postgres psql -U root -d appdb -tAc "SELECT COUNT(DISTINCT notebook_id) FROM notebook_sources WHERE article_id = 'arxiv:2401.001';")
echo "distinct notebooks with arxiv:2401.001 = $NDISTINCT (expected 2)"; test "$NDISTINCT" = "2"

ok "PATCH /N1/sources/arxiv:2401.001 selected=false"
RES=$(curl -s -b "$J" -X PATCH "$B/notebooks/$N1/sources/arxiv:2401.001" -H 'Content-Type: application/json' \
  -d '{"selected":false}')
echo "$RES" | $PY -m json.tool
SEL=$(echo "$RES" | $PY -c 'import sys,json; print(json.load(sys.stdin)["selected"])')
echo "selected=$SEL (expected False)"; test "$SEL" = "False"

ok "GET /N1/sources — должен быть тот же selected=false для arxiv:2401.001"
LIST=$(curl -s -b "$J" "$B/notebooks/$N1/sources")
echo "$LIST" | $PY -m json.tool

ok "POST /N1/sources с уже добавленным id — дедуп, total всё равно 2"
DUP=$(curl -s -b "$J" -X POST "$B/notebooks/$N1/sources" -H 'Content-Type: application/json' \
  -d '{"article_ids":["arxiv:2401.001","arxiv:9999.new"]}')
COUNT=$(echo "$DUP" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "total in N1 after dedup=$COUNT (expected 3: 001+002+9999.new)"; test "$COUNT" = "3"

ok "DELETE /N1/sources/arxiv:2401.001 → 204"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$J" -X DELETE "$B/notebooks/$N1/sources/arxiv:2401.001")
echo "http=$HTTP (expected 204)"; test "$HTTP" = "204"
# N2 всё ещё имеет эту статью
N2_HAS=$(docker exec postgres psql -U root -d appdb -tAc "SELECT COUNT(*) FROM notebook_sources WHERE notebook_id = '$N2' AND article_id = 'arxiv:2401.001';")
echo "N2 still has arxiv:2401.001 → $N2_HAS (expected 1)"; test "$N2_HAS" = "1"

ok "notebook.sources_count корректный"
N1_META=$(curl -s -b "$J" "$B/notebooks/$N1")
echo "$N1_META" | $PY -m json.tool
N1_SC=$(echo "$N1_META" | $PY -c 'import sys,json; print(json.load(sys.stdin)["sources_count"])')
echo "N1 sources_count=$N1_SC (expected 2: 002 + 9999.new)"; test "$N1_SC" = "2"

ok "ALL SPRINT 7 PASSED"
