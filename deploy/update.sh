#!/bin/bash
# TURA Pro on its own server: run as root every 3 minutes (tura-update.timer). Takes the site's newest version from GitHub when
# there is one and restarts it - only when something the site runs on changed (a change to the GitHub workflows, the research
# logs or these deploy scripts alone does not cut visitors off). Also applies a domain written in /opt/tura/domain (Caddy + HTTPS).
# Installed root-owned at /opt/tura/update.sh by deploy/oracle-setup.sh, and replaced by the "server ops" workflow (update-scripts).
set -uo pipefail
ROOT=/opt/tura; APP=$ROOT/app; VENV=$ROOT/venv; RUNAS=tura
BRANCH="$(cat $ROOT/branch 2>/dev/null || echo main)"
cd $APP || exit 0
old="$(runuser -u $RUNAS -- git rev-parse HEAD)"
runuser -u $RUNAS -- git fetch -q origin "$BRANCH" || exit 0
new="$(runuser -u $RUNAS -- git rev-parse "origin/$BRANCH")"
if [ "$old" != "$new" ]; then
  changed="$(runuser -u $RUNAS -- git diff --name-only "$old" "$new")"
  runuser -u $RUNAS -- git reset -q --hard "origin/$BRANCH"
  if printf '%s\n' "$changed" | grep -qx 'requirements.txt'; then
    runuser -u $RUNAS -- $VENV/bin/pip install -q -r requirements.txt
  fi
  # the site restarts only for a change it runs on (not the workflows, research logs, scripts or docs alone)
  if printf '%s\n' "$changed" | grep -vE '^(\.github/|research/|scripts/|deploy/|site_check/)|\.md$' | grep -q .; then
    systemctl restart tura
    echo "updated $old -> $new (restarted)"
  else
    echo "updated $old -> $new (no restart: nothing the site runs on changed)"
  fi
fi
want=":80"
[ -s $ROOT/domain ] && want="$(tr -cd 'a-z0-9.-' < $ROOT/domain)"
[ -n "$want" ] || want=":80"
if ! head -1 /etc/caddy/Caddyfile | grep -qF "$want {"; then
  printf '%s {\n\tencode gzip zstd\n\treverse_proxy 127.0.0.1:8501\n}\n' "$want" > /etc/caddy/Caddyfile
  systemctl reload caddy || systemctl restart caddy
  echo "caddy now serves $want"
fi
