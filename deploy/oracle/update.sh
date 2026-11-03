#!/usr/bin/env bash
# Update an already deployed Oracle instance. Run from a verified repository checkout.
set -euo pipefail
if (( EUID != 0 )); then echo "Use sudo" >&2; exit 1; fi
[[ -f hosting_server.py && -f prepare_database.py ]] || { echo "Run from repository root" >&2; exit 2; }
command -v rsync >/dev/null
mkdir -p /opt/matchlab-az/score_cache
rsync -a --delete --exclude='.git/' --exclude='score_cache/' --exclude='world_football.sqlite' ./ /opt/matchlab-az/
chown -R matchlab:matchlab /opt/matchlab-az
cd /opt/matchlab-az
sudo -u matchlab /usr/bin/python3 prepare_database.py
sudo -u matchlab /usr/bin/python3 - <<'PY'
import world_db
data=world_db.counts()
assert data and data.get("total")==506207, f"Database invalid: {data}"
PY
systemctl restart matchlab
curl --fail --silent --show-error --max-time 8 http://127.0.0.1:10000/healthz
echo
echo "MATCHLAB server updated."
