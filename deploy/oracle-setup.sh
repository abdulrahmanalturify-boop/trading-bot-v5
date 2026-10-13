#!/bin/bash
# TURA Pro on its own server (Oracle Cloud, Ubuntu 24.04, Arm or x86): installs the site, runs it day and night, and keeps it
# up to date: every 3 minutes it looks at GitHub and, when the site has a new version, takes it and restarts.
#
# Run once as root. On Oracle it runs by itself when the server is first started: the text pasted in the "cloud-init script"
# box writes the site's secrets to /opt/tura-secrets.toml and then runs this script. The secrets never go into the code.
#
#   address:  http://<the server's public IP>   (port 80; Caddy passes it to Streamlit on 127.0.0.1:8501)
#   a domain: write it in /opt/tura/domain and run  sudo systemctl restart tura-update  -> https://<domain> with its certificate
set -euxo pipefail

REPO="${TURA_REPO:-https://github.com/abdulrahmanalturify-boop/trading-bot-v5.git}"
BRANCH="${TURA_BRANCH:-main}"
ROOT=/opt/tura
APP=$ROOT/app
VENV=$ROOT/venv
RUNAS=tura
export DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------- packages
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl caddy

# ---------------------------------------------------------------- the site's own user, its code and its Python
id -u $RUNAS >/dev/null 2>&1 || useradd --system --create-home --home-dir /home/$RUNAS --shell /usr/sbin/nologin $RUNAS
mkdir -p $ROOT
chown $RUNAS:$RUNAS $ROOT
if [ ! -d $APP/.git ]; then
  runuser -u $RUNAS -- git clone --branch "$BRANCH" "$REPO" $APP
fi
echo "$BRANCH" > $ROOT/branch
[ -d $VENV ] || runuser -u $RUNAS -- python3 -m venv $VENV
runuser -u $RUNAS -- $VENV/bin/pip install --upgrade pip
runuser -u $RUNAS -- $VENV/bin/pip install -r $APP/requirements.txt

# ---------------------------------------------------------------- the secrets (Streamlit reads ~/.streamlit/secrets.toml of the user it runs as)
mkdir -p /home/$RUNAS/.streamlit
if [ -s /opt/tura-secrets.toml ]; then
  mv /opt/tura-secrets.toml /home/$RUNAS/.streamlit/secrets.toml
fi
touch /home/$RUNAS/.streamlit/secrets.toml
chown -R $RUNAS:$RUNAS /home/$RUNAS/.streamlit
chmod 700 /home/$RUNAS/.streamlit
chmod 600 /home/$RUNAS/.streamlit/secrets.toml

# ---------------------------------------------------------------- the site as a service (starts with the server, restarts if it stops)
cat > /etc/systemd/system/tura.service <<EOF
[Unit]
Description=TURA Pro (Streamlit)
After=network-online.target
Wants=network-online.target

[Service]
User=$RUNAS
WorkingDirectory=$APP
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV/bin/streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# ---------------------------------------------------------------- Caddy in front: port 80 (and 443 once a domain is set)
write_caddy() {
  local site=":80"
  if [ -s $ROOT/domain ]; then site="$(tr -d ' \n' < $ROOT/domain)"; fi
  cat > /etc/caddy/Caddyfile <<EOF
$site {
	encode gzip zstd
	reverse_proxy 127.0.0.1:8501
}
EOF
}
write_caddy

# ---------------------------------------------------------------- updates: every 3 minutes, the newest version from GitHub
# (deploy/update.sh, copied root-owned: the site's own user cannot change what root runs)
install -o root -g root -m 755 $APP/deploy/update.sh $ROOT/update.sh

cat > /etc/systemd/system/tura-update.service <<EOF
[Unit]
Description=TURA Pro: take the newest version from GitHub

[Service]
Type=oneshot
ExecStart=$ROOT/update.sh
EOF
cat > /etc/systemd/system/tura-update.timer <<EOF
[Unit]
Description=TURA Pro: look for a new version every 3 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=3min

[Install]
WantedBy=timers.target
EOF

# ---------------------------------------------------------------- the firewall inside Oracle's Ubuntu image: ports 80 and 443 open
if command -v iptables >/dev/null 2>&1; then
  for p in 80 443; do
    iptables -C INPUT -p tcp --dport $p -m state --state NEW -j ACCEPT 2>/dev/null || \
      iptables -I INPUT 5 -p tcp --dport $p -m state --state NEW -j ACCEPT 2>/dev/null || \
      iptables -I INPUT -p tcp --dport $p -m state --state NEW -j ACCEPT
  done
  if command -v netfilter-persistent >/dev/null 2>&1; then netfilter-persistent save || true; fi
fi

# ---------------------------------------------------------------- start
systemctl daemon-reload
systemctl enable --now tura
systemctl enable --now tura-update.timer
systemctl enable caddy
systemctl restart caddy
echo "TURA Pro is running: http://$(curl -s -4 --max-time 5 ifconfig.me || echo '<this server IP>')"
