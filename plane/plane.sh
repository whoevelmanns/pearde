#!/bin/bash
# pearde plane — run Plane (makeplane/plane) self-hosted inside the skill.
#
#   plane.sh boot        multi-project cold start: install + start + every
#                        board on the machine (registry + Claude session
#                        folders) bootstrapped and synced into its own project
#   plane.sh install     download + install into plane-app/ beside this script;
#                        no-op when already installed
#   plane.sh start       start the containers, wait for the API
#   plane.sh bootstrap [board]
#                        no-login first run: create the service account,
#                        workspace and API token, write prds/.plane.env;
#                        no-op when already configured
#   plane.sh open [board]
#                        bootstrap, copy the login password to the clipboard,
#                        open the app in the browser
#   plane.sh stop        stop the containers
#   plane.sh status [board]
#                        installed? running? reachable? and does that board
#                        mirror — a running app mirrors nothing on its own
#   plane.sh upgrade     pull the next Plane release
#   plane.sh url         print the app URL
#
# Rate limit: $PLANE_API_RATE_LIMIT, default 600/minute — the shipped
# 60/minute cannot finish a first sync of a large board.
#
# Port: $PLANE_PORT, default 8442. Set before `install`; afterwards edit
# LISTEN_HTTP_PORT, WEB_URL, CORS_ALLOWED_ORIGINS in plane-app/plane.env.
#
# Everything lives under this directory: setup.sh (Plane's own installer,
# fetched from the latest release), plane-app/ (compose file, plane.env,
# archives). Data lives in named docker volumes and survives stop/start.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$DIR/plane-app"
ENV_FILE="$APP_DIR/plane.env"
SETUP="$DIR/setup.sh"
PORT="${PLANE_PORT:-8442}"
URL="http://localhost:$PORT"

need_docker() {
  docker info >/dev/null 2>&1 || {
    echo "plane: docker daemon not reachable — start Docker first" >&2; exit 1; }
}

fetch_setup() {
  [ -x "$SETUP" ] && return
  curl -fsSL -o "$SETUP" \
    https://github.com/makeplane/plane/releases/latest/download/setup.sh
  chmod +x "$SETUP"
}

installed() { [ -f "$APP_DIR/docker-compose.yaml" ] && [ -f "$ENV_FILE" ]; }

set_env() { # KEY VALUE — replace or append in plane.env
  if grep -q "^$1=" "$ENV_FILE"; then
    sed -i.bak "s|^$1=.*|$1=$2|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  else
    printf '%s=%s\n' "$1" "$2" >> "$ENV_FILE"
  fi
}

configured_url() {
  [ -f "$ENV_FILE" ] && grep '^WEB_URL=' "$ENV_FILE" | cut -d= -f2- || echo "$URL"
}

cmd_install() {
  need_docker
  if installed; then
    echo "plane: already installed at $APP_DIR ($(configured_url))"
    return
  fi
  fetch_setup
  (cd "$DIR" && "$SETUP" install </dev/null)
  set_env LISTEN_HTTP_PORT "$PORT"
  set_env WEB_URL "$URL"
  set_env CORS_ALLOWED_ORIGINS "$URL"
  echo "plane: installed at $APP_DIR, port $PORT"
}

bind_localhost() {
  # Publish the proxy on 127.0.0.1 only — the login password is simple, so the
  # app must not face the LAN. PLANE_EXPOSE_LAN=1 removes the pin: then set a
  # strong password via PLANE_UI_PASSWORD before running bootstrap.
  python3 - "$APP_DIR/docker-compose.yaml" "${PLANE_EXPOSE_LAN:-}" <<'PY'
import re, sys
path, expose = sys.argv[1], sys.argv[2] == "1"
src = open(path).read()
out = re.sub(r"^(\s*)- target: (80|443)\n(\1  host_ip: \"127\.0\.0\.1\"\n)?",
             lambda m: f"{m.group(1)}- target: {m.group(2)}\n"
             + ("" if expose else f"{m.group(1)}  host_ip: \"127.0.0.1\"\n"),
             src, flags=re.M)
if out != src:
    open(path, "w").write(out)
    print("plane: proxy bound to " + ("all interfaces" if expose else "127.0.0.1 only"))
PY
}

write_autologin() {
  # Auto-login: the api signs every anonymous request in as the service
  # account (autologin/ beside this script), so the app never shows a login
  # screen. Only sane on 127.0.0.1 — PLANE_EXPOSE_LAN=1 disables it, and so
  # does PLANE_AUTOLOGIN=0.
  local file="$APP_DIR/autologin.yaml"
  if [ "${PLANE_AUTOLOGIN:-1}" = "0" ] || [ "${PLANE_EXPOSE_LAN:-}" = "1" ]; then
    rm -f "$file"
    return
  fi
  cat > "$file" <<EOF
services:
  api:
    volumes:
      - $DIR/autologin:/injected:ro
    environment:
      PYTHONPATH: /injected
      PLANE_AUTOLOGIN_EMAIL: $BOOT_EMAIL
EOF
}

compose() {
  local files=(-f "$APP_DIR/docker-compose.yaml")
  [ -f "$APP_DIR/autologin.yaml" ] && files+=(-f "$APP_DIR/autologin.yaml")
  docker compose "${files[@]}" --env-file "$ENV_FILE" "$@"
}

tune_env() {
  # The API-key throttle protects a public deployment. This one is pinned to
  # 127.0.0.1 and serves one syncer, where 60/minute means a board of 70 PRDs
  # cannot finish its first sync. Raise it, and leave a deliberate edit alone:
  # only the shipped default is replaced.
  local want="${PLANE_API_RATE_LIMIT:-600/minute}"
  local now; now=$(grep '^API_KEY_RATE_LIMIT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
  if [ -z "$now" ] || [ "$now" = "60/minute" ] || [ -n "${PLANE_API_RATE_LIMIT:-}" ]; then
    [ "$now" = "$want" ] || { set_env API_KEY_RATE_LIMIT "$want"
      echo "plane: API_KEY_RATE_LIMIT ${now:-unset} -> $want"; }
  fi
}

cmd_start() {
  need_docker
  installed || { echo "plane: not installed — run: $0 install" >&2; exit 1; }
  tune_env
  bind_localhost
  write_autologin
  compose up -d --quiet-pull
  local url; url=$(configured_url)
  local waited=0
  until curl -fsS -o /dev/null -m 3 "$url/api/instances/" 2>/dev/null; do
    waited=$((waited + 3)); sleep 3
    [ $waited -ge 300 ] && { echo "plane: api not up after ${waited}s — check: compose logs api" >&2; exit 1; }
  done
  echo "plane: up at $url"
  [ -f "$APP_DIR/autologin.yaml" ] && echo "plane: auto-login on — the app never asks for a password"
}

cmd_stop() {
  need_docker
  installed || { echo "plane: not installed" >&2; exit 1; }
  (cd "$DIR" && "$SETUP" stop </dev/null)
}

cmd_upgrade() {
  need_docker
  installed || { echo "plane: not installed — run: $0 install" >&2; exit 1; }
  fetch_setup
  (cd "$DIR" && "$SETUP" upgrade </dev/null)
}

cmd_status() { # [board] — the app, and whether this board mirrors
  if ! installed; then echo "plane: not installed — run: $0 install"; exit 1; fi
  local url; url=$(configured_url)
  local up=0
  docker info >/dev/null 2>&1 && \
    up=$(docker compose -f "$APP_DIR/docker-compose.yaml" --env-file "$ENV_FILE" \
         ps --status running -q 2>/dev/null | wc -l | tr -d ' ')
  local http="down"
  curl -fsS -o /dev/null -m 3 "$url" 2>/dev/null && http="up"
  echo "plane: installed at $APP_DIR · $up containers running · $url $http"
  [ "$http" = "up" ] || { echo "start it: $0 start"; return 1; }

  # a running app mirrors nothing until this board is bootstrapped — say which
  local board; board="${1:-$(find_board)}"
  if [ -z "$board" ]; then
    echo "board: none from $PWD — nothing to mirror"
    return 0
  fi
  local envfile="$board/.plane.env"
  if [ -f "$envfile" ]; then
    local key code
    key=$(grep '^PLANE_API_KEY=' "$envfile" | cut -d= -f2-)
    code=$(curl -s -o /dev/null -w '%{http_code}' -m 5 -H "X-API-Key: $key" \
           "$url/api/v1/users/me/" 2>/dev/null)
    # only 401/403 is a bad token. 429 is the app throttling a sync in flight,
    # and reporting that as rejected sends the user to re-bootstrap a key that
    # works.
    case "$code" in
      200)     echo "board: $board mirrors"; return 0 ;;
      401|403) echo "board: $board · .plane.env token rejected — run: $0 bootstrap $board"; return 1 ;;
      429)     echo "board: $board mirrors · api rate-limiting a sync in flight"; return 0 ;;
      *)       echo "board: $board · token unverified (HTTP ${code:-none})"; return 0 ;;
    esac
  fi
  echo "board: $board never bootstrapped, so nothing mirrors — run: $0 bootstrap $board"
  return 1
}

# ── bootstrap — no-login first run ────────────────────────────────────────────
# Creates a local service account (credentials in plane-app/bootstrap.env,
# also your login for the web UI), the workspace, an API token, and writes
# prds/.plane.env for the nearest board. Idempotent: a working .plane.env is
# left alone; a lost token or password is regenerated.

BOOT_ENV="$APP_DIR/bootstrap.env"
BOOT_EMAIL="prd-admin@localhost.local"
WS_SLUG="${PLANE_WORKSPACE_SLUG:-prd}"
BOARDS="$APP_DIR/boards.list"

register_board() { # one prds/ path per line, machine-local
  mkdir -p "$APP_DIR"; touch "$BOARDS"
  # canonical absolute path or nothing — a relative entry can never be found
  # again, and /tmp vs /private/tmp would register one board twice. A board on
  # an ephemeral filesystem is a fixture: it works now, it is gone on reboot,
  # so it never enters the permanent registry
  local canon; canon=$(cd "$1" 2>/dev/null && pwd -P) || return 0
  case "$canon" in /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) return 0 ;; esac
  grep -qxF "$canon" "$BOARDS" 2>/dev/null || echo "$canon" >> "$BOARDS"
}

discover_boards() {
  # every folder a Claude session was opened in (newest session per project),
  # walked up to its repo root, kept when it holds a prds/ board
  python3 - <<'PY' 2>/dev/null || true
import glob, json, os
cwds = set()
for proj in glob.glob(os.path.expanduser("~/.claude/projects/*/")):
    files = sorted(glob.glob(proj + "*.jsonl"), key=os.path.getmtime, reverse=True)
    for f in files[:3]:
        try:
            with open(f, errors="ignore") as fh:
                for _, line in zip(range(5), fh):
                    c = json.loads(line).get("cwd")
                    if c:
                        cwds.add(c)
                        break
        except Exception:
            continue
boards = set()
for c in cwds:
    d, found = c, False
    while d and d != "/":
        p = os.path.join(d, "prds")
        if os.path.isdir(p):
            boards.add(p)
            found = True
            break
        d = os.path.dirname(d)
    if found:
        continue
    # nothing on the way up: one level down, dot-dirs included. A board off the
    # contract path is mirrored, not skipped — `doctor.sh` is what says move it.
    try:
        for sub in os.listdir(c):
            p = os.path.join(c, sub, "prds")
            if os.path.isdir(p):
                boards.add(p)
    except Exception:
        pass
print("\n".join(sorted(boards)))
PY
}

find_board() { # walk up from $PWD to the nearest prds/
  local d="$PWD"
  while [ -n "$d" ] && [ "$d" != "/" ]; do
    if [ -d "$d/prds" ]; then echo "$d/prds"; return; fi
    d=$(dirname "$d")
  done
}

api_container() {
  docker compose -f "$APP_DIR/docker-compose.yaml" --env-file "$ENV_FILE" \
    ps -q api 2>/dev/null | head -1
}

jsonget() { python3 -c "import json,sys;print(json.load(sys.stdin).get('$1',''))"; }

csrf() { # JAR — fetch a csrf token into/with the cookie jar
  curl -s -b "$1" -c "$1" "$url/auth/get-csrf-token/" | jsonget csrf_token
}

cmd_bootstrap() {
  need_docker
  installed || { echo "plane: not installed — run: $0 install" >&2; exit 1; }
  local url; url=$(configured_url)
  curl -fsS -o /dev/null -m 3 "$url" 2>/dev/null \
    || { echo "plane: $url not reachable — run: $0 start" >&2; exit 1; }

  local board; board="${1:-$(find_board)}"
  local envfile=""
  [ -n "$board" ] && { envfile="$board/.plane.env"; register_board "$board"; }

  # login password: simple by default — the proxy is pinned to 127.0.0.1.
  # PLANE_UI_PASSWORD overrides (required knowledge if PLANE_EXPOSE_LAN=1).
  local pw
  if [ -n "${PLANE_UI_PASSWORD:-}" ]; then
    pw="$PLANE_UI_PASSWORD"
  elif [ -f "$BOOT_ENV" ]; then
    pw=$(grep '^PLANE_PASSWORD=' "$BOOT_ENV" | cut -d= -f2-)
  else
    pw="prd-board-local"
  fi
  printf 'PLANE_EMAIL=%s\nPLANE_PASSWORD=%s\n' "$BOOT_EMAIL" "$pw" > "$BOOT_ENV"
  chmod 600 "$BOOT_ENV"

  # ensure the account exists with this password, instance set up — via the
  # api container's Django shell: version-stable where the god-mode HTTP
  # endpoint is not, and only reachable with local docker access anyway
  local cid; cid=$(api_container)
  [ -n "$cid" ] || { echo "plane: api container not running — run: $0 start" >&2; exit 1; }
  docker exec -e BOOT_EMAIL="$BOOT_EMAIL" -e BOOT_PW="$pw" "$cid" \
    python manage.py shell -c '
import os, uuid
from django.contrib.auth.hashers import make_password
from plane.db.models import User, Profile
from plane.license.models import Instance, InstanceAdmin
email, pw = os.environ["BOOT_EMAIL"], os.environ["BOOT_PW"]
u = User.objects.filter(email=email).first()
if u is None:
    u = User.objects.create(email=email, username=uuid.uuid4().hex,
        first_name="PRD", last_name="Board", password=make_password(pw),
        is_password_autoset=False, is_active=True)
else:
    u.set_password(pw); u.is_active = True; u.save()
Profile.objects.get_or_create(user=u, defaults={"company_name": "prd-board"})
inst = Instance.objects.first()
if inst:
    InstanceAdmin.objects.get_or_create(user=u, instance=inst)
    if not inst.is_setup_done:
        inst.is_setup_done = True
        inst.save()
print("ADMIN_OK")' 2>/dev/null | grep -q ADMIN_OK \
    || { echo "plane: account setup failed in the api container" >&2; exit 1; }

  # a working .plane.env keeps its token — nothing more to create
  if [ -n "$envfile" ] && [ -f "$envfile" ]; then
    local key; key=$(grep '^PLANE_API_KEY=' "$envfile" | cut -d= -f2-)
    if [ -n "$key" ] && curl -fsS -o /dev/null -H "X-API-Key: $key" \
         "$url/api/v1/users/me/" 2>/dev/null; then
      echo "plane: already configured — $envfile works"
      return
    fi
  fi

  # session sign-in
  local jar; jar=$(mktemp); trap 'rm -f "$jar"' RETURN
  local tok; tok=$(csrf "$jar")
  curl -s -o /dev/null -b "$jar" -c "$jar" -H "Referer: $url/" \
    --data-urlencode "email=$BOOT_EMAIL" --data-urlencode "password=$pw" \
    --data-urlencode "csrfmiddlewaretoken=$tok" "$url/auth/sign-in/"
  curl -fsS -o /dev/null -b "$jar" "$url/api/users/me/" 2>/dev/null \
    || { echo "plane: sign-in as $BOOT_EMAIL failed" >&2; exit 1; }

  # workspace
  tok=$(csrf "$jar")
  if ! curl -s -b "$jar" "$url/api/users/me/workspaces/" | grep -q "\"slug\":\"$WS_SLUG\""; then
    curl -s -o /dev/null -b "$jar" -H "X-CSRFToken: $tok" -H "Referer: $url/" \
      -H 'Content-Type: application/json' \
      -d "{\"name\":\"$WS_SLUG\",\"slug\":\"$WS_SLUG\",\"organization_size\":\"Just myself\"}" \
      "$url/api/workspaces/"
    curl -s -b "$jar" "$url/api/users/me/workspaces/" | grep -q "\"slug\":\"$WS_SLUG\"" \
      || { echo "plane: could not create workspace '$WS_SLUG'" >&2; exit 1; }
  fi

  # API token
  local key
  key=$(curl -s -b "$jar" -H "X-CSRFToken: $tok" -H "Referer: $url/" \
    -H 'Content-Type: application/json' -d '{"label":"prd-sync"}' \
    "$url/api/users/api-tokens/" | jsonget token)
  [ -n "$key" ] || { echo "plane: API token creation failed" >&2; exit 1; }

  local block
  block=$(printf 'PLANE_API_URL=%s\nPLANE_API_KEY=%s\nPLANE_WORKSPACE=%s\n' \
    "$url" "$key" "$WS_SLUG")
  if [ -n "$envfile" ]; then
    printf '%s\n' "$block" > "$envfile"
    chmod 600 "$envfile"
    echo "plane: wrote $envfile"
  else
    echo "plane: no prds/ board found from $PWD — write this as prds/.plane.env:"
    printf '%s\n' "$block"
  fi
  echo "plane: web UI login: $BOOT_EMAIL / password in $BOOT_ENV"
}

cmd_boot() {
  # multi-project cold start: the app up, every board on the machine
  # bootstrapped into its own project and filled with its PRDs
  cmd_install
  cmd_start
  # self-heal the registry first: keep only absolute paths that still exist
  if [ -f "$BOARDS" ]; then
    local keep; keep=$(grep '^/' "$BOARDS" \
      | grep -vE '^(/private)?(/tmp|/var/folders)/' | while IFS= read -r b; do
      [ -d "$b" ] && (cd "$b" && pwd -P); done | sort -u)
    printf '%s\n' "$keep" > "$BOARDS"
  fi
  local all
  all=$({ [ -f "$BOARDS" ] && cat "$BOARDS"; discover_boards; } | sort -u)
  # a master board names boards nothing else may know about: `members:` is the
  # only record of a board that was never opened in a session of its own
  local mem
  mem=$(while IFS= read -r b; do
    [ -n "$b" ] && [ -d "$b" ] || continue
    python3 "$DIR/sync.py" members "$b" 2>/dev/null \
      | awk '$0 !~ /MISSING/ && NF > 1 {print $2}'
  done <<< "$all")
  all=$(printf '%s\n%s\n' "$all" "$mem" | grep '^/' | sort -u)
  if [ -z "$all" ]; then
    echo "plane: no boards found — run '$0 bootstrap' once from a repo with prds/"
    return
  fi
  local b ok=0 failed=0
  while IFS= read -r b; do
    [ -n "$b" ] && [ -d "$b" ] || continue
    echo "── $b"
    if (cmd_bootstrap "$b") && python3 "$DIR/sync.py" sync "$b"; then
      python3 "$DIR/serve.py" ensure "$b" || true  # live from here on
      ok=$((ok + 1))
    else
      failed=$((failed + 1)); echo "plane: $b failed — fix and re-run: $0 boot"
    fi
  done <<< "$all"
  echo "plane: boot done — $ok board(s) live$([ $failed -gt 0 ] && echo ", $failed failed")"
}

cmd_open() {
  cmd_bootstrap "$@"
  local url; url=$(configured_url)
  if [ -f "$APP_DIR/autologin.yaml" ]; then
    echo "plane: auto-login on — no password screen"
  else
    local pw; pw=$(grep '^PLANE_PASSWORD=' "$BOOT_ENV" | cut -d= -f2-)
    local clip=""
    if command -v pbcopy >/dev/null; then printf '%s' "$pw" | pbcopy; clip=" (in your clipboard)"
    elif command -v wl-copy >/dev/null; then printf '%s' "$pw" | wl-copy; clip=" (in your clipboard)"
    elif command -v xclip >/dev/null; then printf '%s' "$pw" | xclip -selection clipboard; clip=" (in your clipboard)"
    fi
    echo "plane: sign in as $BOOT_EMAIL · password: $pw$clip"
  fi
  if command -v open >/dev/null; then open "$url"
  elif command -v xdg-open >/dev/null; then xdg-open "$url"
  else echo "plane: open $url"
  fi
}

case "${1:-status}" in
  boot)      cmd_boot ;;
  install)   cmd_install ;;
  start)     cmd_start ;;
  bootstrap) shift; cmd_bootstrap "$@" ;;
  open)      shift; cmd_open "$@" ;;
  stop)      cmd_stop ;;
  serve)     shift; exec python3 "$DIR/serve.py" "${@:-status}" ;;
  upgrade)   cmd_upgrade ;;
  status)    shift || true; cmd_status "$@" ;;
  url)       configured_url ;;
  *) echo "usage: $0 boot|install|start|bootstrap|open|stop|status|upgrade|url" >&2; exit 2 ;;
esac
