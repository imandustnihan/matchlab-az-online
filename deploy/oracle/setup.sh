#!/usr/bin/env bash
# First-run bootstrap on Ubuntu 22.04 / 24.04 OCI VM. Run: sudo bash setup.sh <https-hostname>
set -euo pipefail

if (( EUID != 0 )); then echo "Run as root via sudo" >&2; exit 1; fi
if (( $# != 1 )); then echo "Usage: sudo bash setup.sh your-domain.example" >&2; exit 2; fi
DOMAIN="$1"
if [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]{2,250}$ ]] || [[ "$DOMAIN" == *..* ]]; then
  echo "Invalid hostname" >&2; exit 2
fi
if [[ ! -f hosting_server.py ]] || [[ ! -f prepare_database.py ]] || [[ ! -f deploy/oracle/matchlab.service ]]; then
  echo "Run from repository root" >&2; exit 2
fi
if ! command -v apt-get >/dev/null 2>&1; then echo "Ubuntu apt-get required" >&2; exit 2; fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-venv git curl ca-certificates caddy
id -u matchlab >/dev/null 2>&1 || useradd --system --home-dir /opt/matchlab-az --shell /usr/sbin/nologin matchlab
mkdir -p /opt/matchlab-az /var/log/caddy
# Source directory should be a checked out repository, not an arbitrary URL.
rsync_available=0
if command -v rsync >/dev/null 2>&1; then rsync_available=1; fi
if (( rsync_available == 0 )); then
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends rsync
fi
rsync -a --delete --exclude='.git/' --exclude='score_cache/' --exclude='world_football.sqlite' ./ /opt/matchlab-az/
mkdir -p /opt/matchlab-az/score_cache
chown -R matchlab:matchlab /opt/matchlab-az
chmod 750 /opt/matchlab-az
cd /opt/matchlab-az
sudo -u matchlab /usr/bin/python3 prepare_database.py
sudo -u matchlab /usr/bin/python3 - <<'PY'
import world_db
counts=world_db.counts()
assert counts and counts.get("total")==506207, f"Database validation failed: {counts}"
print("Validated football records:", counts["total"])
PY
cp deploy/oracle/matchlab.service /etc/systemd/system/matchlab.service
sed "s/MATCHLAB_HOSTNAME/$DOMAIN/g" deploy/oracle/Caddyfile.example >/etc/caddy/Caddyfile
chown -R caddy:caddy /var/log/caddy
caddy validate --config /etc/caddy/Caddyfile
systemctl daemon-reload
systemctl enable --now matchlab
systemctl enable --now caddy
# Do not change SSH firewall access automatically; configure OCI ingress separately.
for n in {1..30}; do
  if curl -fsS --max-time 3 http://127.0.0.1:10000/healthz >/dev/null; then break; fi
  sleep 1
done
curl -fsS --max-time 5 http://127.0.0.1:10000/healthz
echo
echo "Local health passed; check DNS/OCI ingress then https://$DOMAIN/healthz"
