#!/usr/bin/env bash
set -euo pipefail
B=http://127.0.0.1:8000/api/v1
J=/tmp/cj_s4.txt
rm -f "$J"
PY=python3

ok() { echo; echo "=== $* ==="; }

ok "register alice"
curl -s -c "$J" -b "$J" -X POST "$B/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice4@test.com","first_name":"Alice","last_name":"Smith","password":"pass1234"}' > /dev/null

ok "ACCEPT 1: POST notebook with tags=[Attention, attention, 4K] → dedup до 2 тегов"
NB1=$(curl -s -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-1","tags":["Attention","attention","4K"]}')
echo "$NB1" | $PY -m json.tool
NB1_ID=$(echo "$NB1" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

# Проверим что вернулось ровно 2 тега
T_COUNT=$(echo "$NB1" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)["tags"]))')
echo "tags_on_NB1=$T_COUNT (expected 2)"
test "$T_COUNT" = "2"

SLUGS=$(echo "$NB1" | $PY -c 'import sys,json; data=json.load(sys.stdin); print(sorted(t["slug"] for t in data["tags"]))')
echo "slugs=$SLUGS"
test "$SLUGS" = "['4k', 'attention']"

ok "ACCEPT 2: повтор того же → переиспользуем теги (без дублей)"
NB2=$(curl -s -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-2","tags":["Attention","4K"]}')
echo "$NB2" | $PY -m json.tool
NB2_ID=$(echo "$NB2" | $PY -c 'import sys,json; print(json.load(sys.stdin)["id"])')

# те же тег-id для обеих тетрадей
TAG_IDS_1=$(echo "$NB1" | $PY -c 'import sys,json; print(sorted(t["id"] for t in json.load(sys.stdin)["tags"]))')
TAG_IDS_2=$(echo "$NB2" | $PY -c 'import sys,json; print(sorted(t["id"] for t in json.load(sys.stdin)["tags"]))')
echo "NB1_tag_ids=$TAG_IDS_1"
echo "NB2_tag_ids=$TAG_IDS_2"
test "$TAG_IDS_1" = "$TAG_IDS_2"

ok "Создадим третью тетрадь только с 'attention' (для асимметрии в counts)"
curl -s -b "$J" -X POST "$B/notebooks/create" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-3","tags":["Attention"]}' > /dev/null

ok "ACCEPT 3: GET /tags → attention=3, 4k=2"
TAGS=$(curl -s -b "$J" "$B/tags")
echo "$TAGS" | $PY -m json.tool
ATT_COUNT=$(echo "$TAGS" | $PY -c 'import sys,json; d=json.load(sys.stdin); print([t["notebook_count"] for t in d if t["slug"]=="attention"][0])')
FK_COUNT=$(echo "$TAGS" | $PY -c 'import sys,json; d=json.load(sys.stdin); print([t["notebook_count"] for t in d if t["slug"]=="4k"][0])')
echo "attention.count=$ATT_COUNT (expected 3), 4k.count=$FK_COUNT (expected 2)"
test "$ATT_COUNT" = "3"
test "$FK_COUNT" = "2"

ok "ACCEPT 4: GET /notebooks?tags=attention,4k → только NB-1 и NB-2 (AND)"
AND_RES=$(curl -s -b "$J" "$B/notebooks/?tags=attention,4k")
echo "$AND_RES" | $PY -m json.tool
AND_COUNT=$(echo "$AND_RES" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "AND count=$AND_COUNT (expected 2)"
test "$AND_COUNT" = "2"

ok "BONUS: ?tags=attention,4k&tags_op=or → все 3"
OR_RES=$(curl -s -b "$J" "$B/notebooks/?tags=attention,4k&tags_op=or")
OR_COUNT=$(echo "$OR_RES" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)))')
echo "OR count=$OR_COUNT (expected 3)"
test "$OR_COUNT" = "3"

ok "GET /tags?q=at → autocomplete"
AUTO=$(curl -s -b "$J" "$B/tags?q=at")
echo "$AUTO" | $PY -m json.tool

ok "PATCH /tags/:id rename"
ATT_ID=$(echo "$TAGS" | $PY -c 'import sys,json; d=json.load(sys.stdin); print([t["id"] for t in d if t["slug"]=="attention"][0])')
curl -s -b "$J" -X PATCH "$B/tags/$ATT_ID" -H 'Content-Type: application/json' \
  -d '{"name":"Self-Attention"}' | $PY -m json.tool

ok "PATCH /tags/:id rename → collision"
FK_ID=$(echo "$TAGS" | $PY -c 'import sys,json; d=json.load(sys.stdin); print([t["id"] for t in d if t["slug"]=="4k"][0])')
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$J" -X PATCH "$B/tags/$FK_ID" \
  -H 'Content-Type: application/json' -d '{"name":"self-attention"}')
echo "rename collision http=$HTTP (expected 409)"
test "$HTTP" = "409"

ok "PUT notebook → заменить теги на пустой список"
UPD=$(curl -s -b "$J" -X PUT "$B/notebooks/$NB1_ID" \
  -H 'Content-Type: application/json' \
  -d '{"name":"NB-1","tags":[]}')
echo "$UPD" | $PY -m json.tool
TC=$(echo "$UPD" | $PY -c 'import sys,json; print(len(json.load(sys.stdin)["tags"]))')
echo "after empty tags update count=$TC (expected 0)"
test "$TC" = "0"

ok "DELETE tag → cascade в notebook_tags"
HTTP=$(curl -s -o /dev/null -w '%{http_code}' -b "$J" -X DELETE "$B/tags/$FK_ID")
echo "delete http=$HTTP (expected 204)"
test "$HTTP" = "204"
# NB-2 теперь только с self-attention тегом
NB2_AFTER=$(curl -s -b "$J" "$B/notebooks/$NB2_ID")
echo "$NB2_AFTER" | $PY -m json.tool
NB2_T=$(echo "$NB2_AFTER" | $PY -c 'import sys,json; print([t["slug"] for t in json.load(sys.stdin)["tags"]])')
echo "NB2 tags after FK delete=$NB2_T"
test "$NB2_T" = "['self-attention']"

ok "ALL SPRINT 4 ACCEPTANCE PASSED"
